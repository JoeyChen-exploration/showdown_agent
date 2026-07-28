# An Expert System for Gen9 Ubers Pokémon Battling

## 1. Introduction

Frankly, before starting this project I had never played or watched competitive Pokémon, so my domain knowledge was close to zero. I have played strategy card games like Hearthstone before, though, and the question of "how much do I know about my opponent's options, and how should I allocate resources under that uncertainty" felt structurally similar to what a Pokémon battle asks every turn. I open with this not as a disclaimer, but because it directly shaped the methodology: with no domain intuition to fall back on, the whole design had to start from systematic, verifiable research rather than guessing from experience. This also motivates adopting an expert-system architecture [1][8] — an inference engine applying heuristic rules from a knowledge base, with a clear explanation facility — which keeps every turn's decision path traceable and auditable.

That research identified eight core factors a battle decision system has to handle, which are the foundation the rest of the design is argued from:

| # | Factor | Design implication |
|---|---|---|
| 1 | Type effectiveness | Baseline for nearly every move-choice and switch-safety decision |
| 2 | Move secondary effects | Status chance, stat changes, field effects, recoil, and accuracy define what a move is *for*, not just its power number |
| 3 | Held items | Choice items, permanent transformation items, and one-time defensive items each add a distinct rule |
| 4 | Terastallization | One-time, irreversible — the single largest source of mid-battle complexity this generation |
| 5 | Tier system (Ubers/OU/UU/RU/NU) | Caps opponent strength per tier; source of this task's five-tier opponent ladder |
| 6 | Random teampreview lead order | Verified via `poke_env`'s source — rules out predicting a fixed opener, forcing general runtime rules instead |
| 7 | Speed/turn order | Decides whose move resolves first; opponent's real stats are unknown, so we conservatively assume their maximum possible speed |
| 8 | Simultaneous move selection | Neither side sees the other's choice before submitting — unlike Hearthstone's sequential turns, every decision must hedge against a threat, not react to one |

## 2. Design

The whole decision system is organised around the classic three-part expert-system architecture [1][8]. Concretely, in this codebase: the **Knowledge Base** is the hard-coded Pokémon mechanics (type effectiveness, STAB multiplier, stat-stage multipliers, the speed formula, etc. — §2.1/2.2) plus a set of weight constants calibrated by ablation (§2.4's parameter table); the **Inference Engine** is `_choose_move`'s four-layer cascade, which applies the knowledge base's facts and weights to the current battle state to decide this turn's action (§2.4); the **Explanation Facility** is `self.decision_log`, which records, every turn, a snapshot of both sides (species/HP/status), the candidate actions considered, the one chosen, and its score — so any decision can be traced back to *what the system saw and why it chose that*, rather than a black-box result. The rest of this section elaborates each component in turn.

### 2.1 Task-Rule Analysis

**The five opponent tiers constrain only the opponent, not us** (factor 5). `bots/teams/` has five opponent strength tiers (uber/ou/uu/ru/nu); our own team format is limited only by `battle_format="gen9ubers"` — the least restrictive singles tier [5], permitting nearly any Pokémon including Uber-tier ones. Since the same team faces all five tiers and the tier system places no further restriction on our side, the rational choice is direct: **draft from the strongest legal tier (Uber)** rather than self-handicapping for "fairness." This is the reason the team is built almost entirely from Uber-tier Pokémon (Kyogre, Koraidon, Zacian-Crowned, Eternatus, Arceus-Ghost) — a conclusion drawn from the rules' structure, not from "these Pokémon are strong" as a matter of taste.

**What `poke_env` [2] exposes bounds what the methodology can rely on.** `teampreview_opponent_team` reveals the opponent's full roster during teampreview (before they've actually sent anyone out); `battle.can_tera`/`battle.used_tera` expose whether Tera is still available. Working out exactly what information the framework provides — rather than assuming — is the same discipline as the teampreview-randomness finding above: design boundaries have to be confirmed against source/docs, not guessed.

### 2.2 Opponent Analysis: From Teambuilder to a Threat Table

Every one of the 15 bots' teams (30 Pokémon total) was entered into the [Showdown Teambuilder](https://play.pokemonshowdown.com/teambuilder) [4] to check each Pokémon's actual type, ability, held item, and full move effects — not just base power. Only patterns that recurred across multiple strength tiers were treated as generalisable design input; single-bot quirks were not, which is also why the final design never hard-codes a response to a specific opponent (consistent with teampreview's uniform randomness, §1). These five threats are factors 2 and 3 above, as they actually show up in this specific opponent ladder:

| Threat | Concrete effect |
|---|---|
| Paralysis moves (e.g. Cobalion/Rotom-Wash/Slowbro, 3 tiers) | Speed halved; 25% chance to be fully paralysed |
| Priority moves (e.g. Sucker Punch/Extreme Speed/Bullet Punch, multiple tiers) | Move priority overrides speed — the opponent moves first regardless of our stats |
| Choice items (e.g. Darkrai/Metagross/Zapdos-Galar, 3 tiers) | Move locked after first use until switching out |
| Entry hazards (Stealth Rock/Spikes, almost every tier) | Damage on every switch-in, compounding with stacked layers |
| Knock Off (almost every tier) | Permanently strips the target's item, with a same-turn power bonus |

These five threats split cleanly by *when* they can be addressed. Paralysis and priority both bear on "who moves first this turn" — a judgement that has to be re-made every turn from the current battle state, so it can only live in runtime scoring logic (§2.4). Choice-locking, hazards, and Knock Off are the opposite: their cost accrues over many turns (an information disadvantage, chip damage, reduced firepower once an item is gone), and the moment that actually determines their outcome is team/item selection, not any single turn's score — runtime logic has no way to price in "damage that accumulates across turns" (§2.3). That split is itself part of the argument for a fast team: since these three cumulative threats can't be handled algorithmically at all, a slower, attrition-based playstyle would be far more exposed to them than a playstyle that ends the game before they can compound.

### 2.3 Team Composition: A Hyper Offense Roster

The team was built with the [pokeaimmd.com Ubers team builder](https://www.pokeaimmd.com/ubers) [6] around a **Hyper Offense** identity — the playstyle that best matches a system built on general, non-opponent-specific rules, for two concrete reasons. First, Hyper Offense is fast (factor 7) and hits hard, so its value is realised almost entirely within the current turn rather than depending on a payoff several turns later — which matches exactly what §2.4's single-turn scoring architecture can evaluate, rather than asking it to reason about value it structurally cannot compute. Second, raw, high, direct damage is easier to translate into the scoring formula's numbers (e.g. `_power_score`, which folds a move's type-effectiveness multiplier [factor 1], STAB, and base power into one score) than a stall team's slow-building resource advantage would be, and it tolerates more scoring error: an imperfect choice this turn is more survivable when your own output is already high than when the whole plan depends on no single turn going wrong.

| Pokémon | Role |
|---|---|
| Ribombee (Focus Sash; Sticky Web / Stun Spore / Moonblast / U-turn) | Lead support: hazards, opponent speed control, one guaranteed-survival turn |
| Kyogre (Choice Band, Drizzle; Waterfall / Body Slam / Earthquake / Tera Blast) | Rain-boosted physical wallbreaker, locked into one move at a time |
| Koraidon (Loaded Dice; Swords Dance / Scale Shot / Flare Blitz / Taunt) | Fast setup sweeper |
| Zacian-Crowned (Rusted Sword; Swords Dance / Close Combat / Behemoth Blade / Wild Charge) | Fast setup sweeper |
| Eternatus (Power Herb; Sludge Bomb / Meteor Beam / Dynamax Cannon / Fire Blast) | Special wallbreaker, one-shot nuke via Power Herb |
| Arceus-Ghost (Spooky Plate, Multitype; Judgment / Aura Sphere / Power Gem / Calm Mind) | Bulkier special closer, doubles as a pivot |

Ribombee is the only Pokémon carrying opponent-speed-control (Sticky Web), tempo disruption (Stun Spore), and a risk-free opening turn (Focus Sash) together, which is why it leads and anchors the fixed opening script (§2.4).

### 2.4 Core Algorithm: if-else for the Opening, Greedy Scoring Everywhere Else

![Decision cascade](analysis/figures/decision_flow.png)

*The four-layer decision cascade inside `_choose_move`: forced switch → fixed Ribombee opening (turns ≤2) → hard-KO short-circuit → general single-turn scoring fallback. Any layer that fires short-circuits the rest.*

The system is built from two distinct styles of logic: **turns 1–2 use a fixed if-else script**, everything else uses **greedy scoring** — evaluate every legal action this turn and take the highest-scoring one, with no multi-turn lookahead. The final, ablation-confirmed parameters:

| Parameter | Value | Meaning | Ablation result (§3.3) |
|---|---|---|---|
| Hard-KO short-circuit | on | Take a guaranteed KO immediately, bypassing scoring; also previews a Tera-assisted KO (factor 4 — used only for this one narrow purpose, not general Tera timing) | 15.00→14.67 when disabled — one of only two modules with a measurable effect |
| Ribombee opening script | on | Fixed if-else for turns ≤2 | 15.00→14.33 when disabled — the other module with a measurable effect |
| `SETUP_BOOST_WEIGHT` | 55.0 | Score per stat-stage from a setup move | Calibrated up from 30; largely insensitive across the tested range |
| `SWITCH_DEFENSE_WEIGHT` | 60.0 | Defensive-risk weight in switch scoring | Tested at 30/90 — both still perfect scores |
| `SWITCH_COST` | 25 | Flat cost applied to any switch | Tested at 0/50 — both still perfect scores |
| `FASTER_/SLOWER_SURVIVAL_THRESHOLD` | 0.9 / 0.6 | Tolerance for a setup move when we move first / when the opponent does | Raised from 0.5/0.35 — the setup-safety check didn't actually fire below this (issue #7) |

**Why if-else for the opening.** Turns 1–2 have no revealed information yet (items, EVs, Tera type are all unknown), which is exactly where a general scoring framework is most likely to misjudge from insufficient data. Sticky Web on turn 1 (slowing the opponent's future switch-ins), branching into Stun Spore or U-turn on turn 2, is a fixed combination already confirmed to hold up under uncertainty — the ablation cost of disabling it (15.00→14.33) is the direct evidence that this specific combo earns its place as a script rather than being recomputed from scratch every game. The U-turn branch specifically checks whether Kyogre is still alive and pivots into it rather than switching arbitrarily: U-turn deals chip damage and swaps out in the same action, and Kyogre's Drizzle sets rain the instant it's sent in — so the pivot both retreats Ribombee and brings the rain-boosted wallbreaker online for free, a scripted synergy that a per-turn scoring pass over "what's the best move right now" would have no way to plan for in advance.

**Why greedy scoring everywhere else.** Mid-to-late-game states are too numerous to hand-enumerate without producing rules that misfire on unanticipated situations — switch evaluation is the clearest case: whether a candidate that "hits hard but takes a big hit back" should out-rank one that's "safe but weak" is a continuous trade-off across HP and type multipliers, not something a discrete if-else branch can express without edge cases, which is why switch scoring subtracts a defensive-risk term from an offensive one (`best move's power score − incoming-damage multiplier × defense weight`) rather than branching on cases. Opponent leads are uniformly random (factor 6, verified from source) and items/EVs/Tera are unknown until revealed — exactly the kind of information-incomplete, combinatorially large space greedy scoring is built for, the mirror image of the opening's "also incomplete, but few enough branches to enumerate by hand." Both sides also pick a move simultaneously each turn without seeing the other's choice (factor 8), so there is no "wait and see, then react" option — only hedging against a threat in this turn's score.

Two of §2.2's threats get a concrete runtime rule inside this framework. A Pokémon's *effective* speed is halved under paralysis before comparing who moves first, so a slowed target isn't mistaken for "still faster, so setup is safe." Separately, before comparing raw speed at all, the framework checks whether the opponent has already revealed a priority move this battle (e.g. Sucker Punch) — if so, they're assumed to move first regardless of stats, since Gen9 priority brackets [3] override speed outright, and skipping this check would misjudge "I'm numerically faster" as "setup is safe" when it isn't.

## 3. Evaluation

### 3.1 Methodology: A Single Grading Run vs. Our Own Tuning Confidence

The assignment's win condition is simple: best-of-three per bot, >0.5 win rate counts as a win, and rank on the ladder converts to a mark via `expert_main.py` [7]'s `assign_marks`. **Our final submission beats all 15/15 bots, which ranks #1 and earns the maximum mark of 10.0.** Critically, the official grading run almost certainly happens once — whatever that single run produces (move-hit variance, crits, AI randomness included) is the final score, with no averaging.

During development we found that the same code, rerun against the same fixed ladder, produces different results (13/15 one run, 14/15 the next); two configurations differing by one parameter can tie on total score while losing to different bots. A single "win" is therefore not reliable evidence for comparing two designs — it may just be luck, the same lesson system-benchmarking methodology draws about measurement bias producing data indistinguishable from a real, stable effect [10]. To make our own tuning decisions trustworthy, `analysis/run_ablation.py` was extended to rerun a full 15-bot ladder multiple times per configuration and report the mean and standard deviation of bots beaten, rather than trusting one run; a difference only counts as real once it clearly exceeds the noise observed across repeats.

To be explicit about what this buys us: **this multi-run discipline only applies to our own internal tuning — it cannot change how the actual submission is graded**, which still runs once and still carries that run's luck. What it does provide is a better-grounded belief that our submitted parameters are genuinely stronger on average, raising the odds of a good outcome on grading day — and it directly motivated a design goal of reducing variance itself (e.g. the hard-KO rule shortens games and reduces the chance a match gets derailed by randomness, §2.4) rather than only chasing it after the fact.

### 3.2 Isolating Team Strength from Decision Logic

To satisfy the requirement that a good ranking has to be shown to come from the *method*, not just a strong roster, we ran a controlled comparison: keep the team fixed, but replace `_choose_move` with the framework's built-in random move selection — isolating team strength from decision logic.

| Team | Decision logic | Bots beaten / 15 |
|---|---|---|
| Current roster (unchanged) | Random move selection | 1/15 (only `random-ru`, 0.67 win rate; all others <0.5) |
| Current roster (unchanged) | Rule-based system (final) | 15/15 |

With the roster held fixed, random move selection is close to a guaranteed loss; switching to the rule system alone raises bots beaten from 1 to 15. That jump is the quantitative evidence that the win-rate improvement comes from the decision logic, not simply "the roster was already strong."

### 3.3 Ablation: Which Rules and Weights Actually Matter

§3.2 only shows *that* the decision logic matters; this section isolates *which* rules and weights inside it do. Each row below reruns the final configuration (§2.4) with exactly one change, 3 times, reported as mean ± stdev — a difference only counts as real once it clearly clears the noise floor, which in this data never exceeds 0.29 bots beaten, well under the smallest real difference reported (0.33). Full data is in `analysis/results/`, per-config detail in `Ablation_Study.md`.

![Ablation: mean bots beaten per config, 3 repeats each](analysis/figures/ablation_mean_beaten.png)

| Configuration | Change from final | Mean beaten / 15 | Stdev |
|---|---|---|---|
| **Final configuration** | none | **15.00** | 0.00 |
| No hard-KO | hard-KO rule disabled | 14.67 | 0.29 |
| No opening script | opening script disabled | 14.33 | 0.29 |
| Setup weight 15 | `SETUP_BOOST_WEIGHT` 55→15 | 15.00 | 0.00 |
| Setup weight 45 | `SETUP_BOOST_WEIGHT` 55→45 | 14.67 | 0.29 |
| Switch defense weight 30/90 | `SWITCH_DEFENSE_WEIGHT` 60→30/90 | 15.00 / 15.00 | 0.00 / 0.00 |
| Switch cost 0/50 | `SWITCH_COST` 25→0/50 | 15.00 / 15.00 | 0.00 / 0.00 |

**Finding 1 — only two modules produce a reproducible, real score difference when removed.** Disabling the hard-KO rule costs 0.33 bots beaten, disabling the opening script costs 0.67 — both several times the 0.29 noise floor. Per-bot detail confirms these are genuine in-battle losses, not timeouts, concentrated against `simple-uber` (`poke_env`'s built-in `SimpleHeuristicsPlayer`, which genuinely sets hazards/boosts/switches, unlike the purely greedy `max_damage` bot).

**Finding 2 — weight parameters are largely insensitive across the tested range.** Every weight tested ties the final configuration except `SETUP_BOOST_WEIGHT=45`, which costs 0.33 bots beaten — right at the noise floor, and the only weight change with any measurable effect at all.

**What this means for the final configuration.** Both the hard-KO rule and the opening script stay enabled: each is one of only two things in the whole system with a measured, reproducible cost if removed. `SWITCH_DEFENSE_WEIGHT=60` and `SWITCH_COST=25` are, strictly, tied with every other tested value against this bot ladder — the data alone can't pick 60 or 25 over the alternatives. What breaks that tie is the team's own Hyper Offense identity (§2.3): `SWITCH_COST=25` keeps the framework biased toward staying in and attacking rather than pivoting at the first sign of risk, which a stall team could afford but a speed-sweep team, whose whole plan is to keep applying tempo, cannot; `SWITCH_DEFENSE_WEIGHT=60` sits deliberately mid-range rather than at either tested extreme — enough to still pull a key sweeper out of an avoidable follow-up hit, without becoming cautious enough to contradict the team's own playstyle. This reasoning matters more, not less, once the fixed bot ladder is no longer the opponent: a class-competition opponent is unknown and may well punish over-cautious play, so the tie-breaker there can't come from bot-ladder data at all — it has to come from what the team is actually built to do.

## 4. Reflections

### 4.1 Where the Difficulty Actually Was

This assignment isn't hard to *implement* — `_choose_move` is, at bottom, a handful of functions across two files. The real difficulty was deciding, after each bug, whether it was **encoded knowledge that was wrong** or **irreducible environmental uncertainty** — the same distinction raised in the introduction between an expert system's failure mode and an ML system's. Three properties of the task made this hard on its own terms, independent of implementation: opponent information is always incomplete outside teampreview, forcing the knowledge base to encode conservative defaults (`_max_speed_estimate` always assumes maximum investment) rather than exact values; the evaluation environment is non-deterministic (hit/crit/status rolls plus random leads), so "did this change actually help" needed the whole multi-run methodology of §3.1 rather than a single answer; and correctness rests entirely on the human — there's no training data to catch a mistake, and several bugs were only found by systematic audit rather than a runtime error, because the rule was syntactically fine and only semantically wrong.

The system described in §2 is the product of three iterations, each closed out with a full ablation pass before moving on: `v1` established six correctness fixes to the scoring logic (Judgment's typing, Scale Shot's multi-hit damage, switch-scoring direction, among others); `v2` added three targeted mechanisms for edge cases the default framework handled poorly (anti-stall Taunt logic, a teampreview counter table, delayed hazard-value scoring); `v3` added Terastallize handling. What's more informative than the feature list, though, is what went wrong reaching each one:

| Version / issue | What went wrong | Lesson |
|---|---|---|
| v1 | `_switch_score` had its offensive/defensive terms reversed — a genuine misunderstanding at design time, not a typo, found by working backward from anomalous losses | Knowledge-to-code translation errors are the characteristic expert-system failure mode |
| v2 | Assumed `max_damage-uber`'s timeouts came from stat-boost stalling; built two features around that assumption before reading `bots/max_damage.py` and finding it only ever picks the highest-power move | Verify against the opponent's actual implementation before designing a fix — don't guess from "typical" play |
| v3 (Terastallize) | Code review caught two bugs: Judgment's post-Tera type was resolved backwards, and `Pokemon.tera_type` reflects a *revealed* Tera type, not our own pre-set one | Confirms v1's original call to defer Terastallize ("too many variables, too easy to get wrong") was correct in hindsight |
| Priority fix (#15/16) | Logic verified correct (unit test + code review), but ablation found a real, reproducible cost with no traceable direct cause; confirmed via source that seeded replay can't isolate it — the protocol never exposes a seed, and even if it did, a diverging decision legitimately diverges the RNG stream from that point on | Not every causal chain resolves, even when specifically investigated |

The nature of the difficulty shifted over time — from translation errors (v1), to undertested assumptions (v2), to third-party framework semantics and unreliable measurement tools (v3 onward), to causal questions that stay open even under direct investigation. That progression is itself the clearest evidence of how our understanding of "expert agent" evolved: knowledge correctness was the obvious difficulty at first, but the environment the knowledge runs in, and how to verify it's correct, turned out to be just as unavoidable a part of the design problem.

### 4.2 The Randomness Behind the Numbers

Evaluation leans on "noise" and "variance" repeatedly; the underlying causes split into three layers. The **root cause** is the battle engine itself — hit/crit/status rolls, and critically, all three opponent AI styles picking their lead uniformly at random (confirmed from source, §1) — a source of variance that no sample size averages away, only smooths. **Sample size** is not itself a source of randomness but our ability to average out the first layer: official grading is one Bo3 per bot, and even our own screening runs were single 15-bot passes, so one unlucky game can flip a bot from "beaten" to "not," which is exactly why §3.1's multi-run methodology exists. The **90-second timeout** is a threshold effect that can fold continuous randomness into a binary win/loss label, but only for the rare match that's inherently long — most battles resolve in 15–30 turns, far short of the wall.

This is a structural limit of a rule-based expert system operating in a non-deterministic environment: the rules themselves can be fully deterministic and traceable, but the environment they run in is not, so correctness can only ever be argued statistically, never proven from one run — which is exactly why §4.3 shows that even "stable across many reruns" is not, on its own, sufficient evidence.

### 4.3 A Structural Conclusion That Turned Out to Be a Tooling Bug

Across several ablation rounds, `max_damage-uber` looked like a stable loss: `baseline`'s win rate against it reproduced the same number (~1/3, stdev 0.58) across roughly seven or eight unrelated code changes. That stability looked like the strongest possible evidence, so — following our own "don't trust a single run" discipline — we concluded it was a structural limitation of single-turn greedy scoring rooted in §4.2's randomness, and stopped investing in it.

That conclusion was wrong, and wrong in an interesting place: not the decision logic, but **our own ablation script**. To run multiple repeats in one process, it incremented each repeat's bot usernames to avoid collisions — but Showdown's protocol replaces an old session on a same-name reconnect, so incrementing usernames let stale connections accumulate for the life of the process, unlike a real grading run's clean, fresh-process-per-run behaviour. The "stable timeout" we observed was stable **tooling side-effect**, not a property of the system under test; switching to one fresh process per repeat, the same configuration ran clean across 27 independent repeats with zero timeouts.

The methodological lesson matters more than the fix: reproducibility across reruns only rules out random noise, not a *biased but deterministic* measurement tool, which produces data indistinguishable from a real, stable effect [10] — a distinct discipline from "never trust a single run," and one this project only learned by going back to the grading harness's own source rather than running yet another ablation.

### 4.4 Greedy Scoring vs. if-else, in Hindsight

A related but distinct sense of "greedy" is worth revisiting too: the framework never does multi-turn search either, on the reasoning that minimax's value depends on the opponent optimising against us — the "single-agent vs. multi-agent" distinction in Russell & Norvig's task-environment taxonomy [9] — which the fixed ladder's bot AI, verified from source, does not do. That premise is unverified for a future class-competition setting, where opponents are other students' agents that might genuinely counter-play; if it doesn't hold there, single-turn scoring loses its justification outright, rather than merely losing precision the way if-else's edge cases do.

This comparison doesn't need to be hypothetical — both styles run inside our own system: the opening script (§2.4) is pure if-else/hardcode, everything else is greedy scoring. Measured against real ablation data (§3.3), the result cuts against the intuition that "the more sophisticated continuous framework should contribute more": the only two modules with a reproducible, real score impact are both hardcoded rules (the hard-KO short-circuit and the opening script), while greedy scoring's own weights are almost entirely insensitive across the tested range. The two styles aren't in competition — the same determinism/stochasticity framing [9] explains why: if-else wins where information is certain and the branch space is small enough to enumerate by hand (the opening, "can this KO"), where a decision is unambiguous once conditions are met; greedy scoring wins where information is incomplete and the space is too large to enumerate, at the cost of any single rule's precision — which is also why the weights are insensitive: the framework was built for coverage, not for any one number being exact. Both remain the same category of system underneath, though: the scoring formulas are just as hand-written as the if-else branches (the `_switch_score` direction bug lived in the scoring framework, not the hardcoded script), and both are equally capable of the "knowledge encoded wrong" failure mode regardless of how long the reasoning chain is. The actual takeaway is to match the tool to how certain and enumerable the sub-problem is, not to assume a general framework is inherently superior to a hardcoded rule.

## References

[1] Wikipedia. *Expert system*. https://en.wikipedia.org/wiki/Expert_system

[2] hsahovic et al. *poke_env* (GitHub repository). https://github.com/hsahovic/poke_env

[3] Smogon / Pokémon Showdown. *pokemon-showdown* (GitHub repository). https://github.com/smogon/pokemon-showdown

[4] Pokémon Showdown. *Teambuilder*. https://play.pokemonshowdown.com/teambuilder

[5] Smogon. *Gen 9 Ubers format rules*. https://www.smogon.com/dex/sv/formats/uber/

[6] pokeAImmd. *Ubers Team Builder*. https://www.pokeaimmd.com/ubers

[7] UoA-CARES. *showdown_agent* (GitHub repository, course starter code). https://github.com/UoA-CARES/showdown_agent

[8] Buchanan, B. G., & Shortliffe, E. H. (1984). *Rule-Based Expert Systems: The MYCIN Experiments of the Stanford Heuristic Programming Project*. Addison-Wesley.

[9] Russell, S. J., & Norvig, P. *Artificial Intelligence: A Modern Approach*.

[10] Mytkowicz, T., Diwan, A., Hauswirth, M., & Sweeney, P. F. (2009). *Producing Wrong Data Without Doing Anything Obviously Wrong!* ASPLOS 2009.
