"""
Ablation runner for the wche652 expert-system agent.

This script is NOT part of the graded submission (only players/<upi>.py is), so unlike
that file it is free to read/write files on disk. It loads a fresh copy of the agent
module per configuration, patches its tunable module-level constants, runs the full
15-bot tournament, and dumps per-bot results, the agent's in-memory decision trace, and
the raw turn-by-turn battle events (from poke_env's own Battle.observations) to CSV.

Usage (from the repo root, with the local Showdown server running):
    pokemon/bin/python analysis/run_ablation.py [config_name ...]

With no arguments, runs every configuration in CONFIGS.

NOTE: configs are run serially within one process, and bot/player account names are only
deconflicted *within* that one run (see the bot_id_start comment below). Do not launch two
copies of this script at the same time against the same local Showdown server - they would
both start numbering from the same ids and collide, reproducing the "nametaken" bug this
script was written to avoid in the first place.
"""

import csv
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = REPO_ROOT / "showdown_agent" / "scripts"
PLAYERS_DIR = SCRIPTS_DIR / "players"
RESULTS_DIR = Path(__file__).resolve().parent / "results"

sys.path.insert(0, str(SCRIPTS_DIR))

import expert_main  # noqa: E402  (reuses gather_bots / evaluate_player_vs_bot / load_module_from_file)
from poke_env import AccountConfiguration  # noqa: E402

AGENT_FILE = PLAYERS_DIR / "wche652.py"
AGENT_NAME = "wche652"

# name -> {module-level constant name: override value}. "baseline" ships as-is.
CONFIGS = {
    "baseline": {},
    "no_hard_ko": {"ENABLE_HARD_KO": False},
    "no_opening_script": {"ENABLE_RIBOMBEE_OPENING": False},
    "setup_weight_15": {"SETUP_BOOST_WEIGHT": 15.0},
    "setup_weight_45": {"SETUP_BOOST_WEIGHT": 45.0},
    "switch_defense_weight_30": {"SWITCH_DEFENSE_WEIGHT": 30.0},
    "switch_defense_weight_90": {"SWITCH_DEFENSE_WEIGHT": 90.0},
    "switch_cost_0": {"SWITCH_COST": 0},
    "switch_cost_50": {"SWITCH_COST": 50},
}

DECISION_LOG_FIELDS = [
    "battle_tag", "turn", "my_pokemon", "my_hp_fraction", "my_status",
    "opp_pokemon", "opp_hp_fraction", "opp_status", "branch",
    "candidates", "chosen_action", "chosen_score", "we_move_first",
]


def build_player(config_index: int, overrides: dict):
    module = expert_main.load_module_from_file(AGENT_FILE, f"{AGENT_NAME}_ablation_{config_index}")
    for key, value in overrides.items():
        if not hasattr(module, key):
            raise AttributeError(f"{AGENT_FILE.name} has no module-level constant {key!r} to override")
        setattr(module, key, value)
    account_config = AccountConfiguration(f"{AGENT_NAME[:10]}a{config_index}", None)
    return module.CustomAgent(account_configuration=account_config, battle_format="gen9ubers")


def run_config(name: str, overrides: dict, config_index: int) -> dict:
    player = build_player(config_index, overrides)
    # Bot account names are only unique *within* one gather_bots() call (ids 1..15), so every
    # config needs its own id range - otherwise the second config's bots collide with the
    # first's still-lingering connections on the local Showdown server ("nametaken" errors,
    # which get counted as losses and silently corrupt the results). The 100-wide gap only
    # stays collision-free while each config's bot roster fits under 100 bots.
    bots_per_config = len(expert_main.BOT_STYLE_ORDER) * len(expert_main.BOT_TEAM_ORDER)
    assert bots_per_config < 100, (
        f"{bots_per_config} bots/config no longer fits the 100-id gap between configs; "
        "widen the gap in run_config() before trusting ablation results"
    )
    bots = expert_main.gather_bots(bot_id_start=config_index * 100 + 1)

    per_bot_rows = []
    beaten = 0
    for bot_index, bot in enumerate(bots, start=1):
        print(f"    [{bot_index}/{len(bots)}] vs {bot.username} ...", end=" ", flush=True)
        winrate, hard_failure = expert_main.evaluate_player_vs_bot(player, bot)
        did_beat = winrate > 0.5 and not hard_failure
        beaten += int(did_beat)
        print(f"winrate={winrate:.2f}{' (beat)' if did_beat else ''}")
        per_bot_rows.append(
            {"config": name, "opponent": bot.username, "winrate": winrate, "beaten": did_beat}
        )

    rank = len(bots) + 1 - beaten
    mark = expert_main.assign_marks(rank)

    config_dir = RESULTS_DIR / name
    config_dir.mkdir(parents=True, exist_ok=True)

    with open(config_dir / "per_bot.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["config", "opponent", "winrate", "beaten"])
        writer.writeheader()
        writer.writerows(per_bot_rows)

    with open(config_dir / "decisions.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=DECISION_LOG_FIELDS)
        writer.writeheader()
        for entry in player.decision_log:
            row = dict(entry)
            row["candidates"] = repr(row["candidates"])
            writer.writerow(row)

    with open(config_dir / "events.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["battle_tag", "opponent_username", "won", "turn", "event"])
        for battle in player.battles.values():
            for turn, observation in battle.observations.items():
                for event in observation.events:
                    writer.writerow(
                        [battle.battle_tag, battle.opponent_username, battle.won, turn, "|".join(event)]
                    )

    return {"config": name, "rank": rank, "mark": mark, "beaten": beaten, "total": len(bots)}


def main():
    requested = sys.argv[1:]
    unknown = [name for name in requested if name not in CONFIGS]
    if unknown:
        sys.exit(f"unknown config name(s): {unknown!r}; available: {list(CONFIGS)}")
    configs = {name: CONFIGS[name] for name in requested} if requested else CONFIGS

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    total_configs = len(configs)
    summary_rows = []
    for index, (name, overrides) in enumerate(configs.items()):
        print(f"=== [{index + 1}/{total_configs}] config: {name} ({overrides or 'baseline'}) ===")
        summary = run_config(name, overrides, index)
        print(f"  -> rank=#{summary['rank']} mark={summary['mark']} beaten={summary['beaten']}/{summary['total']}")
        summary_rows.append(summary)

    with open(RESULTS_DIR / "summary.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["config", "rank", "mark", "beaten", "total"])
        writer.writeheader()
        writer.writerows(summary_rows)

    print(f"\nSummary written to {RESULTS_DIR / 'summary.csv'}")


if __name__ == "__main__":
    main()
