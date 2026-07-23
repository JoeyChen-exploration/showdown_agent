"""
Runs a single player-vs-bot matchup (Bo3) for one ablation config against one opponent,
to drill into *why* a config wins/loses that specific matchup (see Ablation_Study.md's
"simple-uu 摇摆" observation / GitHub issue #6). Not part of the graded submission - free
to read/write files, same as run_ablation.py.

Writes decisions.csv + events.csv to analysis/results/_trace/<config>__<opponent_prefix>/
- a *separate* directory from analysis/results/<config>/, so it never touches or
overwrites the committed multi-repeat aggregate data those directories hold.

Usage (from the repo root, with the local Showdown server running):
    pokemon/bin/python analysis/trace_matchup.py <config_name> <opponent_username_prefix>
Example:
    pokemon/bin/python analysis/trace_matchup.py baseline simple-uu
"""

import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from run_ablation import CONFIGS, DECISION_LOG_FIELDS, RESULTS_DIR, build_player  # noqa: E402

import expert_main  # noqa: E402  (run_ablation.py's import puts SCRIPTS_DIR on sys.path)

# Kept far away from the run_index/bot_id ranges the real ablation runs use (run_index
# up to ~20, bot ids up to ~2015), so this never collides with a still-lingering
# connection on the local Showdown server.
TRACE_RUN_INDEX = 999
TRACE_BOT_ID_START = 99900


def main():
    if len(sys.argv) != 3:
        sys.exit(f"usage: {sys.argv[0]} <config_name> <opponent_username_prefix>")
    config_name, opponent_prefix = sys.argv[1], sys.argv[2]
    if config_name not in CONFIGS:
        sys.exit(f"unknown config name {config_name!r}; available: {list(CONFIGS)}")

    player = build_player(TRACE_RUN_INDEX, CONFIGS[config_name])
    bots = expert_main.gather_bots(bot_id_start=TRACE_BOT_ID_START)
    matches = [b for b in bots if b.username.startswith(opponent_prefix)]
    if len(matches) != 1:
        sys.exit(f"expected exactly one bot matching {opponent_prefix!r}, found {[b.username for b in matches]}")
    bot = matches[0]

    print(f"tracing config={config_name!r} vs {bot.username} ...")
    winrate, hard_failure = expert_main.evaluate_player_vs_bot(player, bot)
    print(f"winrate={winrate:.2f}{' (hard failure)' if hard_failure else ''}")

    out_dir = RESULTS_DIR / "_trace" / f"{config_name}__{opponent_prefix}"
    out_dir.mkdir(parents=True, exist_ok=True)

    with open(out_dir / "decisions.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=DECISION_LOG_FIELDS)
        writer.writeheader()
        for entry in player.decision_log:
            row = dict(entry)
            row["candidates"] = repr(row["candidates"])
            writer.writerow(row)

    with open(out_dir / "events.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["battle_tag", "opponent_username", "won", "turn", "event"])
        for battle in {**player.battle_archive, **player.battles}.values():
            for turn, observation in battle.observations.items():
                for event in observation.events:
                    writer.writerow(
                        [battle.battle_tag, battle.opponent_username, battle.won, turn, "|".join(event)]
                    )

    print(f"wrote {out_dir}")


if __name__ == "__main__":
    main()
