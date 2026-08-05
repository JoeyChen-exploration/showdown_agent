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

The system is built from two distinct styles of logic: **turns 1–2 use a fixed if-else script**, everything else uses **greedy scoring** — evaluate every legal action this turn and take the highest-scoring one, with no multi-turn lookahead. The final parameters, each confirmed by ablation (§3.3):

| Parameter | Value | Meaning |
|---|---|---|
| Hard-KO short-circuit | on | Take a guaranteed KO immediately, bypassing scoring; also previews a Tera-assisted KO (factor 4 — used only for this one narrow purpose, not general Tera timing) |
| Ribombee opening script | on | Fixed if-else for turns ≤2 |
| `SETUP_BOOST_WEIGHT` | 55.0 | Score per stat-stage from a setup move |
| `SWITCH_DEFENSE_WEIGHT` | 60.0 | Defensive-risk weight in switch scoring |
| `SWITCH_COST` | 25 | Flat cost applied to any switch |
| `FASTER_/SLOWER_SURVIVAL_THRESHOLD` | 0.9 / 0.6 | Tolerance for a setup move when we move first / when the opponent does (raised from 0.5/0.35 — the check didn't actually fire below this, issue #7) |

**Why if-else for the opening.** Turns 1–2 have no revealed information yet (items, EVs, Tera type are all unknown), which is exactly where a general scoring framework is most likely to misjudge from insufficient data. Sticky Web on turn 1 (slowing the opponent's future switch-ins), branching into Stun Spore or U-turn on turn 2, is a fixed combination already confirmed to hold up under uncertainty — the ablation cost of disabling it (15.00→14.33) is the direct evidence that this specific combo earns its place as a script rather than being recomputed from scratch every game. The U-turn branch specifically checks whether Kyogre is still alive and pivots into it rather than switching arbitrarily: U-turn deals chip damage and swaps out in the same action, and Kyogre's Drizzle sets rain the instant it's sent in — so the pivot both retreats Ribombee and brings the rain-boosted wallbreaker online for free, a scripted synergy that a per-turn scoring pass over "what's the best move right now" would have no way to plan for in advance.

**Why greedy scoring everywhere else.** Mid-to-late-game states are too numerous to hand-enumerate without producing rules that misfire on unanticipated situations — switch evaluation is the clearest case: whether a candidate that "hits hard but takes a big hit back" should out-rank one that's "safe but weak" is a continuous trade-off across HP and type multipliers, not something a discrete if-else branch can express without edge cases, which is why switch scoring subtracts a defensive-risk term from an offensive one (`best move's power score − incoming-damage multiplier × defense weight`) rather than branching on cases. Opponent leads are uniformly random (factor 6, verified from source) and items/EVs/Tera are unknown until revealed — exactly the kind of information-incomplete, combinatorially large space greedy scoring is built for, the mirror image of the opening's "also incomplete, but few enough branches to enumerate by hand." Both sides also pick a move simultaneously each turn without seeing the other's choice (factor 8), so there is no "wait and see, then react" option — only hedging against a threat in this turn's score. This is also why the design never reaches for minimax-style game-tree search [10]: that model assumes players alternate turns under perfect information, but Gen9 battles are simultaneous-move with hidden opponent state — the wrong game model, not just a more expensive one. It's also the design's clearest weakness: nothing here can sacrifice tempo now for a payoff two turns later, so a patient, attrition-based opponent is exactly what this greedy evaluator is structurally worst at.

Two of §2.2's threats get a concrete runtime rule inside this framework. A Pokémon's *effective* speed is halved under paralysis before comparing who moves first, so a slowed target isn't mistaken for "still faster, so setup is safe." Separately, before comparing raw speed at all, the framework checks whether the opponent has already revealed a priority move this battle (e.g. Sucker Punch) — if so, they're assumed to move first regardless of stats, since Gen9 priority brackets [3] override speed outright, and skipping this check would misjudge "I'm numerically faster" as "setup is safe" when it isn't.

The three weight parameters above are each closer to a design choice than a data-proven optimum — ablation (§3.3) finds them tied or nearly tied against every alternative tested, so their specific values are justified there by the team's own identity rather than by this data alone.

## 3. Evaluation

### 3.1 Methodology: A Single Grading Run vs. Our Own Tuning Confidence

The assignment's win condition is simple: best-of-three per bot, >0.5 win rate counts as a win, and rank on the ladder converts to a mark via `expert_main.py` [7]'s `assign_marks`. **Our final submission beats all 15/15 bots, which ranks #1 and earns the maximum mark of 10.0.** Critically, the official grading run almost certainly happens once — whatever that single run produces (move-hit variance, crits, AI randomness included) is the final score, with no averaging.

During development we found that the same code, rerun against the same fixed ladder, produces different results (13/15 one run, 14/15 the next); two configurations differing by one parameter can tie on total score while losing to different bots. A single "win" is therefore not reliable evidence for comparing two designs — it may just be luck, the same lesson system-benchmarking methodology draws about measurement bias producing data indistinguishable from a real, stable effect [9]. To make our own tuning decisions trustworthy, `analysis/run_ablation.py` was extended to rerun a full 15-bot ladder multiple times per configuration and report the mean and standard deviation of bots beaten, rather than trusting one run; a difference only counts as real once it clearly exceeds the noise observed across repeats.

To be explicit about what this buys us: **this multi-run discipline only applies to our own internal tuning — it cannot change how the actual submission is graded**, which still runs once and still carries that run's luck. What it does provide is a better-grounded belief that our submitted parameters are genuinely stronger on average, raising the odds of a good outcome on grading day — and it directly motivated a design goal of reducing variance itself (e.g. the hard-KO rule shortens games and reduces the chance a match gets derailed by randomness, §2.4) rather than only chasing it after the fact.

### 3.2 Isolating Team Strength from Decision Logic

To satisfy the requirement that a good ranking has to be shown to come from the *method*, not just a strong roster, we ran a controlled comparison: keep the team fixed, but replace `_choose_move` with the framework's built-in random move selection — isolating team strength from decision logic.

| Team | Decision logic | Bots beaten / 15 |
|---|---|---|
| Current roster (unchanged) | Random move selection | 1/15 (only `random-ru`, 0.67 win rate; all others <0.5) |
| Current roster (unchanged) | Rule-based system (final) | 15/15 |

With the roster held fixed, random move selection is close to a guaranteed loss; switching to the rule system alone raises bots beaten from 1 to 15. That jump is the quantitative evidence that the win-rate improvement comes from the decision logic, not simply "the roster was already strong."

### 3.3 Ablation: Which Rules and Weights Actually Matter

§3.2 only shows *that* the decision logic matters; this section isolates *which* rules and weights inside it do. Every number below reruns the final configuration (§2.4) with exactly one change, 3 times, reported as mean ± stdev, with a difference only counting as real once it clearly clears the noise floor observed across repeats (0.29 in this data). Full data is in `analysis/results/`, per-config detail in `Ablation_Study.md`.

**Only two modules produce a reproducible, real score difference when removed.** Disabling the hard-KO rule costs 0.33 bots beaten, disabling the opening script costs 0.67 — both several times the 0.29 noise floor. Per-bot detail confirms these are genuine in-battle losses, not timeouts, concentrated against `simple-uber` (`poke_env`'s built-in `SimpleHeuristicsPlayer`, which genuinely sets hazards/boosts/switches, unlike the purely greedy `max_damage` bot).

Every weight parameter, by contrast, is tied or nearly tied across everything tested — but "tied" turns out to mean different things for each, and the three weights don't share one story.

**How `SETUP_BOOST_WEIGHT` was actually found.** Setup-move scoring is `stat-stages boosted × SETUP_BOOST_WEIGHT`; a 2-stage move like Swords Dance scores `2 × SETUP_BOOST_WEIGHT`. At the old default of 30, that's a flat 60 — but across 268 real candidacy cases, the score needed to actually win that turn's comparison ranged from 95 to 570 (mean 237), so 60 never won. Win rate alone can't see this: it takes counting how often the setup move was actually *chosen* in a run, alongside the usual mean-beaten/stdev, to tell "the mechanism is silently dead" apart from "the mechanism works and just doesn't matter here":

| `SETUP_BOOST_WEIGHT` | Setup move chosen (in one run) | Mean beaten / 15 (3 repeats, stdev) |
|---|---|---|
| 30 (old default) | 0 | 15.00 (0.00) — never fires; the mechanism doesn't exist in practice |
| 50 | 0 | 15.00 (0.00) — right at the threshold, still essentially inert |
| **55 (final)** | **1** | **15.00 (0.00) — genuinely fires, at zero measured cost** |
| 65 | 18 | 14.67 (0.29) — fires much more often, and starts costing real games |
| 80 | 243 | 13.00 (0.00) — fires recklessly; even the purely greedy `max_damage` bots start winning |

30, 50, and 55 are indistinguishable by win rate alone — all three score a clean 15.00 — which is exactly the trap: only the chosen time count shows that 30 and 50 aren't "safe defaults," they're a disabled feature. Past 55, chosen time climbs quickly and starts trading away real games, concentrated against `simple-uber`/`simple-uu` (the two opponents in the ladder that actually punish an overcommitted setup turn). A later, narrower retest around 55 (15→15.00, 45→14.67) confirms the same sweet spot holds up.

**`SWITCH_DEFENSE_WEIGHT`: confirmed insensitive under three different formulas, not just once.** Switch scoring's defense term was itself buggy early on — `_switch_score`'s `defense_risk` accidentally computed the *candidate's own offensive* type multiplier against the opponent, not the risk of switching the candidate in — so the first screening round's "30/60/90 all tied" reading rested on a defense term that wasn't measuring defense at all, and wasn't trustworthy. After fixing that formula, a dedicated retest (issue #8) found the same tie holds up anyway: 30/60/90 all averaged 14.00/15 across 3 repeats, with 90 landing at zero stdev — more stable than that round's own reference configuration. The current, clean data confirms the tie a third time, now at a perfect 15.00/15 for all three:

| `SWITCH_DEFENSE_WEIGHT` | Mean beaten / 15 | Stdev |
|---|---|---|
| 30 | 15.00 | 0.00 |
| **60 (final)** | **15.00** | **0.00** |
| 90 | 15.00 | 0.00 |

The same conclusion surviving two independent formula rewrites and a later fix to the ablation script's own connection-handling bug (§4.2) is the actual evidence here, not any single round's numbers. 60 stays the final value not because ablation picked it out — it can't, the data is tied — but because it sits deliberately mid-range rather than at either tested extreme: enough to still pull a key sweeper out of an avoidable follow-up hit, without becoming cautious enough to contradict a playstyle built around staying in and attacking (§2.3).

**`SWITCH_COST`: also insensitive, though its early instability had a different cause.** Unlike the other two weights, `SWITCH_COST`'s apparent "optimal value" flip-flopped across early rounds — a symptom, not a separate bug, of the same ablation-tooling connection-leak issue described in §4.2, which inflated timeout rates unevenly enough to make different values look best from one run to the next. The current, clean data resolves that: 0/25/50 all tie at a perfect 15.00/15.

| `SWITCH_COST` | Mean beaten / 15 | Stdev |
|---|---|---|
| 0 | 15.00 | 0.00 |
| **25 (final)** | **15.00** | **0.00** |
| 50 | 15.00 | 0.00 |

As with `SWITCH_DEFENSE_WEIGHT`, the value is a design choice rather than an empirical one: `SWITCH_COST=25` keeps the framework biased toward staying in and attacking rather than pivoting at the first sign of risk, which a stall team could afford but a speed-sweep team, whose plan is to keep applying tempo, cannot (§2.3). This reasoning for both switch weights matters more, not less, once the opponent isn't the fixed bot ladder: an unknown class-competition opponent may punish over-cautious switching in a way this bot ladder never tests, so bot-ladder data alone was never going to be able to make this choice.

**`FASTER_/SLOWER_SURVIVAL_THRESHOLD`: the one pair that isn't just tied.** Issue #7 raised these from 0.5/0.35 to 0.9/0.6 by direct calculation — a plain 90–120 BP STAB neutral hit already scores 0.34–0.45, so the old thresholds blocked setup moves against almost any real attacker — rather than a broad screening sweep, and the pair had never been re-tested against nearby alternatives until now:

| Configuration | FASTER / SLOWER | Mean beaten / 15 | Stdev |
|---|---|---|---|
| Lower | 0.7 / 0.4 | 14.67 | 0.29 |
| **Final** | **0.9 / 0.6** | **15.00** | **0.00** |
| Higher | 1.1 / 0.8 | 15.00 | 0.00 |

Unlike the three weights above, this one isn't fully insensitive: moving toward the old, stricter direction costs a real 0.33 bots beaten, consistent with the original diagnosis that stricter thresholds block legitimate setup turns. Moving further in the permissive direction costs nothing measured here — though that's more likely a property of this specific bot ladder than proof that even-more-permissive thresholds carry no risk in general, since a genuinely more aggressive opponent could plausibly punish an over-permissive setup call in a way none of these 15 bots do.

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

Evaluation keeps coming back to "noise" and "variance" — here's where that noise actually comes from, in three layers. First, the battle engine itself: hit/crit/status rolls, and — the biggest one — all three opponent AI styles pick their lead pokémon uniformly at random (confirmed from source, §1). No amount of rerunning makes this go away; it only gets averaged out. Second, sample size: official grading is one Bo3 per bot, and even our own screening runs were a single 15-bot pass, so one unlucky game can flip a bot from "beaten" to "not" — this is why §3.1 reruns everything multiple times. Third, the 90-second timeout: it can turn ordinary randomness into a flat win/loss label, but only for the rare match that runs long — most battles finish in 15–30 turns, nowhere close to the wall.

One thing this taught us: a result repeating across many reruns doesn't automatically mean it's real. `max_damage-uber` looked like a stable loss across seven or eight completely unrelated code changes — the kind of consistency that should count as strong evidence. It wasn't the decision logic, though. It was our own ablation script quietly leaking connections across repeats, which turned out to explain the whole pattern. Rerunning a test rules out bad luck, but not a measuring tool that's broken in a consistent way [9] — the two produce data that looks identical.

## References

[1] Wikipedia. *Expert system*. https://en.wikipedia.org/wiki/Expert_system

[2] hsahovic et al. *poke_env* (GitHub repository). https://github.com/hsahovic/poke_env

[3] Smogon / Pokémon Showdown. *pokemon-showdown* (GitHub repository). https://github.com/smogon/pokemon-showdown

[4] Pokémon Showdown. *Teambuilder*. https://play.pokemonshowdown.com/teambuilder

[5] Smogon. *Gen 9 Ubers format rules*. https://www.smogon.com/dex/sv/formats/uber/

[6] pokeAImmd. *Ubers Team Builder*. https://www.pokeaimmd.com/ubers

[7] UoA-CARES. *showdown_agent* (GitHub repository, course starter code). https://github.com/UoA-CARES/showdown_agent

[8] Buchanan, B. G., & Shortliffe, E. H. (1984). *Rule-Based Expert Systems: The MYCIN Experiments of the Stanford Heuristic Programming Project*. Addison-Wesley.

[9] Mytkowicz, T., Diwan, A., Hauswirth, M., & Sweeney, P. F. (2009). *Producing Wrong Data Without Doing Anything Obviously Wrong!* ASPLOS 2009.

[10] Russell, S., & Norvig, P. (2020). *Artificial Intelligence: A Modern Approach* (4th ed.). Pearson.
