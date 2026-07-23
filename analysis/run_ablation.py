"""
Ablation runner for the wche652 expert-system agent.

This script is NOT part of the graded submission (only players/<upi>.py is), so unlike
that file it is free to read/write files on disk. It loads a fresh copy of the agent
module per configuration, patches its tunable module-level constants, runs the full
15-bot tournament (optionally repeated several times per config to average out
run-to-run randomness), and dumps per-bot results, the agent's in-memory decision
trace, and the raw turn-by-turn battle events (from poke_env's own Battle.observations)
to CSV.

Usage (from the repo root, with the local Showdown server running):
    pokemon/bin/python analysis/run_ablation.py [--repeats N] [config_name ...]

With no config names, runs every configuration in CONFIGS. --repeats defaults to 1
(fast single-run screening, e.g. to find which knobs even matter - see
Ablation_Study.md for the screening round this was built for). Once a subset of
configs looks sensitive, re-run just those with --repeats 3 (or more) to average out
noise before trusting which value is actually better - a single run is not reliable
enough on its own (see GitHub issue #2).

Each repeat beyond the first runs as its own isolated subprocess (see run_config()) -
not just an in-process loop. expert_main.py's own tournament run always logs in with
*fixed* usernames (the agent's module name; bots as f"{style}-{team}-1..15"), and
Pokemon Showdown's own protocol evicts a stale session when the same username logs in
again - so a real fresh process naturally self-cleans. This script used to instead loop
--repeats N times *in one process*, giving every repeat its own incrementing username
range purely to dodge "nametaken" crashes - which avoided the crash but meant repeat 1's
connections were never evicted, just accumulated alongside repeat 2's, repeat 3's, etc.
within that one process's lifetime. That accumulation measurably degraded the local
Showdown server partway through a multi-repeat run and inflated timeout-driven losses
for slow matchups (see GitHub issue #14). Running each repeat as its own process (own
PID, own clean exit) reproduces the same self-cleaning behavior a real expert_main.py
invocation gets "for free". A single --repeats 1 invocation is unaffected either way
(nothing to accumulate within it).
"""

import argparse
import csv
import statistics
import subprocess
import sys
import tempfile
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


def build_player(run_index: int, overrides: dict):
    module = expert_main.load_module_from_file(AGENT_FILE, f"{AGENT_NAME}_ablation_{run_index}")
    for key, value in overrides.items():
        if not hasattr(module, key):
            raise AttributeError(f"{AGENT_FILE.name} has no module-level constant {key!r} to override")
        setattr(module, key, value)
    account_config = AccountConfiguration(f"{AGENT_NAME[:8]}a{run_index}", None)
    player = module.CustomAgent(account_configuration=account_config, battle_format="gen9ubers")
    _install_battle_archive(player)
    return player


def _install_battle_archive(player):
    """poke_env's cross_evaluate() calls player.reset_battles() right after every single
    bot matchup (see poke_env/player/utils.py), which clears player.battles - so by the
    time run_once() finishes all 15 matchups and tries to read player.battles to write
    events.csv, it has always been empty (confirmed: events.csv has been header-only
    since the very first commit that added it). Patch this one instance's reset_battles
    to archive battles into player.battle_archive before clearing, so the full history
    across all opponents survives to the end of run_once().
    """
    player.battle_archive = {}
    original_reset_battles = player.reset_battles

    def reset_battles_and_archive():
        player.battle_archive.update(player.battles)
        original_reset_battles()

    player.reset_battles = reset_battles_and_archive


def run_once(name: str, overrides: dict, run_index: int, repeat: int) -> dict:
    """Runs one full 15-bot tournament for one (config, repeat) pair."""
    player = build_player(run_index, overrides)
    # Bot account names are only unique *within* one gather_bots() call (ids 1..15), so
    # every (config, repeat) pair needs its own id range - otherwise it collides with a
    # still-lingering connection from an earlier run on the local Showdown server
    # ("nametaken" errors, which get counted as losses and silently corrupt the results).
    # The 100-wide gap only stays collision-free while each config's bot roster fits
    # under 100 bots.
    bots_per_config = len(expert_main.BOT_STYLE_ORDER) * len(expert_main.BOT_TEAM_ORDER)
    assert bots_per_config < 100, (
        f"{bots_per_config} bots/config no longer fits the 100-id gap between runs; "
        "widen the gap in run_once() before trusting ablation results"
    )
    bots = expert_main.gather_bots(bot_id_start=run_index * 100 + 1)

    per_bot_rows = []
    beaten = 0
    for bot_index, bot in enumerate(bots, start=1):
        print(f"    [{bot_index}/{len(bots)}] vs {bot.username} ...", end=" ", flush=True)
        winrate, hard_failure = expert_main.evaluate_player_vs_bot(player, bot)
        did_beat = winrate > 0.5 and not hard_failure
        beaten += int(did_beat)
        print(f"winrate={winrate:.2f}{' (beat)' if did_beat else ''}")
        per_bot_rows.append(
            {"config": name, "repeat": repeat, "opponent": bot.username, "winrate": winrate, "beaten": did_beat}
        )

    rank = len(bots) + 1 - beaten
    mark = expert_main.assign_marks(rank)

    config_dir = RESULTS_DIR / name
    config_dir.mkdir(parents=True, exist_ok=True)

    # Only keep the decision/event trace for the first repeat - it's for qualitative
    # drill-down (see GitHub issue #6), not part of the quantitative comparison, and
    # keeping every repeat's trace would multiply file count for no analytical benefit.
    if repeat == 0:
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
            # player.battles is reset after every single matchup by poke_env's
            # cross_evaluate() (see _install_battle_archive) - battle_archive is what
            # actually survives across all 15 bots.
            for battle in {**player.battle_archive, **player.battles}.values():
                for turn, observation in battle.observations.items():
                    for event in observation.events:
                        writer.writerow(
                            [battle.battle_tag, battle.opponent_username, battle.won, turn, "|".join(event)]
                        )

    return {
        "config": name, "repeat": repeat, "rank": rank, "mark": mark,
        "beaten": beaten, "total": len(bots), "per_bot_rows": per_bot_rows,
    }


def _run_repeat_via_subprocess(name: str, repeat: int, tmp_root: Path) -> dict:
    """Runs exactly one repeat of `name` in a fresh, isolated child process - see the
    module docstring (and GitHub issue #14) for why: a real separate process, with its
    own fixed account IDs (bot_id_start=1 every time, same as a plain expert_main.py
    invocation), self-cleans on the local Showdown server the same way expert_main.py
    does, instead of accumulating connections alongside sibling repeats the way an
    in-process loop with incrementing usernames used to.
    """
    repeat_dir = tmp_root / f"repeat_{repeat}"
    subprocess.run(
        [sys.executable, str(Path(__file__).resolve()), "--repeats", "1",
         "--output-dir", str(repeat_dir), name],
        check=True,
        cwd=str(REPO_ROOT),
    )
    repeat_config_dir = repeat_dir / name
    with open(repeat_config_dir / "per_bot.csv", newline="", encoding="utf-8") as f:
        per_bot_rows = [
            {
                "config": name,
                "repeat": repeat,
                "opponent": row["opponent"],
                "winrate": float(row["winrate"]),
                "beaten": row["beaten"] == "True",
            }
            for row in csv.DictReader(f)
        ]
    beaten = sum(1 for r in per_bot_rows if r["beaten"])
    rank = len(per_bot_rows) + 1 - beaten
    mark = expert_main.assign_marks(rank)

    # Only keep the decision/event trace for the first repeat - see run_once()'s note
    # on why (same reasoning, just relocating the child process's output instead of
    # writing it directly).
    if repeat == 0:
        config_dir = RESULTS_DIR / name
        config_dir.mkdir(parents=True, exist_ok=True)
        for fname in ("decisions.csv", "events.csv"):
            (repeat_config_dir / fname).replace(config_dir / fname)

    return {
        "config": name, "repeat": repeat, "rank": rank, "mark": mark,
        "beaten": beaten, "total": len(per_bot_rows), "per_bot_rows": per_bot_rows,
    }


def run_config(name: str, overrides: dict, run_index_start: int, repeats: int) -> dict:
    """Runs `repeats` full tournaments for one config and aggregates the results.
    repeats <= 1 runs in-process (nothing to accumulate, no isolation needed).
    repeats > 1 runs each repeat as its own isolated subprocess (see
    _run_repeat_via_subprocess and the module docstring, issue #14)."""
    if repeats <= 1:
        repeat_results = [run_once(name, overrides, run_index_start, 0)]
    else:
        repeat_results = []
        with tempfile.TemporaryDirectory(prefix="ablation_repeat_") as tmp:
            tmp_root = Path(tmp)
            for repeat in range(repeats):
                print(f"  -- repeat {repeat + 1}/{repeats} (isolated process) --")
                repeat_results.append(_run_repeat_via_subprocess(name, repeat, tmp_root))

    config_dir = RESULTS_DIR / name
    config_dir.mkdir(parents=True, exist_ok=True)
    all_per_bot_rows = [row for result in repeat_results for row in result["per_bot_rows"]]
    with open(config_dir / "per_bot.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["config", "repeat", "opponent", "winrate", "beaten"])
        writer.writeheader()
        writer.writerows(all_per_bot_rows)

    # Aggregate per opponent across repeats: mean/stdev winrate and how often it counted
    # as a win, so a config's reliability against a specific bot is visible, not just the
    # aggregate mark - this is what lets a "tied on mark" result (e.g. no_opening_script
    # vs baseline in the first screening round) actually get resolved.
    by_opponent = {}
    for row in all_per_bot_rows:
        by_opponent.setdefault(row["opponent"].rsplit("-", 1)[0], []).append(row)
    summary_rows = []
    for opponent, rows in sorted(by_opponent.items()):
        winrates = [r["winrate"] for r in rows]
        summary_rows.append({
            "config": name,
            "opponent": opponent,
            "repeats": len(rows),
            "mean_winrate": statistics.mean(winrates),
            "stdev_winrate": statistics.stdev(winrates) if len(winrates) > 1 else 0.0,
            "beaten_count": sum(1 for r in rows if r["beaten"]),
        })
    with open(config_dir / "per_bot_summary.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f, fieldnames=["config", "opponent", "repeats", "mean_winrate", "stdev_winrate", "beaten_count"]
        )
        writer.writeheader()
        writer.writerows(summary_rows)

    marks = [r["mark"] for r in repeat_results]
    beaten_counts = [r["beaten"] for r in repeat_results]
    return {
        "config": name,
        "repeats": repeats,
        "mean_mark": statistics.mean(marks),
        "stdev_mark": statistics.stdev(marks) if len(marks) > 1 else 0.0,
        "mean_beaten": statistics.mean(beaten_counts),
        "min_beaten": min(beaten_counts),
        "max_beaten": max(beaten_counts),
        "total": repeat_results[0]["total"],
    }


def main():
    global RESULTS_DIR
    parser = argparse.ArgumentParser()
    parser.add_argument("--repeats", type=int, default=1, help="tournaments per config (default: 1, fast screening)")
    parser.add_argument(
        "--output-dir", type=str, default=None,
        help=argparse.SUPPRESS,  # internal: used by _run_repeat_via_subprocess() to isolate each repeat's output
    )
    parser.add_argument("configs", nargs="*", help="config names to run (default: all)")
    args = parser.parse_args()

    if args.output_dir:
        RESULTS_DIR = Path(args.output_dir)

    unknown = [name for name in args.configs if name not in CONFIGS]
    if unknown:
        sys.exit(f"unknown config name(s): {unknown!r}; available: {list(CONFIGS)}")
    configs = {name: CONFIGS[name] for name in args.configs} if args.configs else CONFIGS

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    total_configs = len(configs)
    summary_rows = []
    run_index = 0
    for index, (name, overrides) in enumerate(configs.items()):
        print(f"=== [{index + 1}/{total_configs}] config: {name} ({overrides or 'baseline'}), "
              f"{args.repeats} repeat(s) ===")
        summary = run_config(name, overrides, run_index, args.repeats)
        run_index += args.repeats
        print(
            f"  -> mean_mark={summary['mean_mark']:.2f} (stdev={summary['stdev_mark']:.2f}) "
            f"mean_beaten={summary['mean_beaten']:.1f}/{summary['total']} "
            f"(range {summary['min_beaten']}-{summary['max_beaten']})"
        )
        summary_rows.append(summary)

    with open(RESULTS_DIR / "summary.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "config", "repeats", "mean_mark", "stdev_mark", "mean_beaten", "min_beaten", "max_beaten", "total",
        ])
        writer.writeheader()
        writer.writerows(summary_rows)

    print(f"\nSummary written to {RESULTS_DIR / 'summary.csv'}")


if __name__ == "__main__":
    main()
