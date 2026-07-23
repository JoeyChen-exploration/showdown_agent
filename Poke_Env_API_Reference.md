# poke_env API 速查：写决策逻辑时能拿到什么信息

> 目的：在设计新规则之前，先把 `wche652.py` 里能读到的 poke_env 状态摊开看一遍，
> 避免"其实早就有现成信息，绕了远路自己猜"这种情况（比如这次发现 `teampreview_opponent_team`
> 能在团队预览阶段就知道对面全部 6 只精灵）。只收录跟写战斗决策逻辑相关的公开属性，
> 不是完整 API 文档——完整文档看 poke_env 源码（本地装在 `pokemon/lib/python3.12/site-packages/poke_env`）。
> 已经在 `wche652.py` 里用到的标了 ✅，还没用到但可能有用的标了 💡，名字容易让人以为是一个意思、
> 实际行为不一样、已经踩过坑的标了 ⚠️。

## `battle: AbstractBattle`（每次 `_choose_move(battle)` 传进来的对象）

### 局面状态
| 属性 | 说明 |
|---|---|
| `battle.turn` | 当前回合数（从 1 开始） |
| `battle.active_pokemon` ✅ | 我方当前场上精灵 |
| `battle.opponent_active_pokemon` ✅ | 对方当前场上精灵 |
| `battle.available_moves` ✅ | 当前可用招式列表 |
| `battle.available_switches` ✅ | 当前可换精灵列表 |
| `battle.force_switch` ✅ | 是否处于"必须换人"状态（精灵阵亡/被弹出） |
| `battle.finished` / `battle.won` / `battle.lost` / `battle.tied` | 对局是否结束及结果 |
| `battle.battle_tag` | 这场对局的唯一标识 |

### 我方 / 对方队伍信息
| 属性 | 说明 |
|---|---|
| `battle.team` | 我方全队（`Dict[str, Pokemon]`，含未上场的） |
| `battle.opponent_team` | 对方**已经亮相过**的精灵（`Dict[str, Pokemon]`，没亮相的不在里面） |
| `battle.teampreview_team` | 团队预览阶段看到的我方全队（一般不需要，我方队伍我们自己知道） |
| 💡 `battle.teampreview_opponent_team` | **团队预览阶段就能拿到对方全部 6 只精灵**（`Set[Pokemon]`），比 `opponent_team` 早，不用等实际上场才知道对面带了什么——这个是这次讨论"要不要保留 Eternatus 打 Arceus-Fairy"的关键信息源 |
| `battle.team_size` / `battle.max_team_size` | 队伍人数上限 |

### 场地效果
| 属性 | 说明 |
|---|---|
| `battle.side_conditions` ✅ | 我方场地效果（`Dict[SideCondition, int]`，比如反射壁/撒菱层数） |
| `battle.opponent_side_conditions` ✅ | 对方场地效果（比如钉子层数） |
| 💡 `battle.weather` | 当前天气（`Dict[Weather, int]`，比如下雨/日照，key 是 `Weather` 枚举） |
| 💡 `battle.fields` | 场地效果（`Dict[Field, int]`，比如电气场地/戏法空间） |

### 太晶化 / 极巨化 / 超级进化状态（太晶化 v3 起已用到，见 `_find_ko_move` 的太晶断死分支）
| 属性 | 说明 |
|---|---|
| ✅ `battle.can_tera` | 这回合我方能不能太晶化 |
| ✅ `battle.used_tera` | 我方这局用没用过太晶（整局限一次） |
| 💡 `battle.opponent_used_tera` | 对方用没用过太晶 |
| `battle.can_dynamax` / `battle.used_dynamax` / `battle.opponent_used_dynamax` | 极巨化相关（Gen9 Ubers 规则下一般不可用，仅供参考） |
| `battle.can_mega_evolve` / `battle.used_mega_evolve` | 超级进化相关（Gen9 里绝大多数精灵不支持） |

### 比赛元信息（一般用不上，但存在）
`battle.player_username` / `battle.opponent_username` / `battle.rating` / `battle.opponent_rating` / `battle.gen` / `battle.format`

## `pokemon: Pokemon`（`battle.active_pokemon`/`opponent_active_pokemon`/`team[...]` 等都是这个类型）

| 属性 | 说明 |
|---|---|
| `pokemon.species` | 种类名（小写、无空格，比如 `"arceusghost"`） |
| `pokemon.types` ✅ | 当前实际类型列表（太晶化后会变成太晶属性） |
| `pokemon.original_types` | 太晶化前的原始类型（不受太晶影响） |
| `pokemon.base_stats` ✅ | 种族值（原始数字，不含努力值/个体值） |
| `pokemon.stats` ✅ | 实际计算出的数值属性（我方精灵才有真实值，对方在数值被推断出来之前是 `None`） |
| `pokemon.boosts` ✅ | 当前能力等级加成（`Dict[str, int]`，-6~6，key 是 `"atk"`/`"spa"`/`"spe"` 等字符串） |
| `pokemon.status` ✅ | 异常状态（`Status` 枚举或 `None`） |
| `pokemon.effects` ✅ | 当前生效的 volatile 效果（`Dict[Effect, int]`，比如混乱/挑衅/畏缩） |
| `pokemon.current_hp_fraction` ✅ | 当前血量百分比（0~1） |
| `pokemon.fainted` | 是否已阵亡 |
| `pokemon.item` ✅ | 持有道具（字符串 id，未知/无道具是 `None`） |
| `pokemon.ability` | 特性（字符串 id，对方精灵可能是 `None` 直到被动作揭示） |
| `pokemon.possible_abilities` | 对方精灵可能持有的特性候选列表（还没揭示时用得上） |
| `pokemon.moves` ✅ | 已知招式（`Dict[str, Move]`，对方精灵只有已经用过的才会出现在这里） |
| `pokemon.is_terastallized` ✅ | 是否已经太晶化 |
| `pokemon.tera_type` ⚠️ | **不是**"队伍文本里配置的太晶属性"，是"太晶属性目前有没有被战斗协议揭示过"——只有
  真的太晶化过、或对局开了 Open Team Sheets 才会有值，**我方自己未太晶化的精灵这个字段是 `None`**，
  这个误解在 v3 实现太晶断死时真的踩过（见 `Experiment_Log.md` 2026-07-24 条目）。要拿"我方队伍
  文本里写的太晶属性"，`wche652.py` 自己维护了一份 `OUR_TERA_TYPES`（species → `PokemonType`）查表，
  不依赖这个属性 |
| `pokemon.stab_multiplier` | 当前 STAB 倍率（已经处理好太晶同属性 2.0 倍的特殊情况）——`wche652.py`
  没有直接调用它，`_tera_power_score` 自己重新实现了同样的判断逻辑（因为需要算"假设太晶化"的
  假设性倍率，这个属性只能算"已经/正在太晶化"的实际倍率） |
| `pokemon.active` | 是否在场上 |
| `pokemon.must_recharge` | 是否处于"打完招式后必须休整一回合"状态（如喷火驾炮） |
| `pokemon.preparing` / `pokemon.preparing_move` | 是否处于"蓄力招式的蓄力回合"状态 |
| `pokemon.protect_counter` | 连续使用守住类招式的次数（失败率递增判断用） |
| `pokemon.first_turn` | 是不是这只精灵上场的第一回合（某些招式如先制类判断有用） |
| `pokemon.revealed` | 对方精灵是不是已经在这局亮过相 |

## `move: Move`（`battle.available_moves`/`pokemon.moves.values()` 里的元素）

| 属性 | 说明 |
|---|---|
| `move.id` ✅ | 招式 id（小写无空格，比如 `"stickyweb"`） |
| `move.type` ✅ | 招式属性（静态查表，Judgment 等签名招式不会跟着使用者变，需要自己特判，见 `_effective_move_type`） |
| `move.category` ✅ | `MoveCategory.PHYSICAL`/`SPECIAL`/`STATUS` |
| `move.base_power` ✅ | 基础威力（多段攻击是单次命中的威力，要另外乘 `expected_hits`） |
| `move.expected_hits` ✅ | 期望命中次数（普通招式是 1，多段攻击类是加权平均值） |
| `move.accuracy` ✅ | 命中率（0~1，`True` 表示必中） |
| `move.boosts` ✅ | 招式附带的能力等级加成（`Dict[str, int]` 或 `None`） |
| `move.self_boost` | 部分招式的加成只针对使用者自己（跟 `boosts` 分开记录，看具体招式） |
| `move.status` ✅ | 招式附带的异常状态（`Status` 或 `None`） |
| `move.volatile_status` | 招式附带的 volatile 效果（`Effect` 或 `None`，比如挑衅本身设置的是这个而不是 `status`） |
| `move.side_condition` ✅ | 招式设置的场地效果（`SideCondition` 或 `None`） |
| `move.target` ✅ | 招式目标（`Target` 枚举，判断打己方场地还是对面场地要用这个） |
| `move.heal` ✅ | 回复比例（0~1，非回复招式是 0） |
| `move.recoil` ✅ | 反作用力比例 |
| `move.drain` | 吸血比例（打出伤害后按比例回血，跟 `heal` 是不同机制） |
| `move.priority` | 招式优先度（先制类招式判断用，目前 `_we_move_first` 没有把这个纳入速度比较，只比速度） |
| `move.secondary` | 附加效果列表（灼伤/麻痹几率等，原始数据结构，没有现成解析） |
| `move.crit_ratio` | 招式自带的暴击率加成等级 |
| `move.breaks_protect` | 是否无视守住类招式 |
| `move.force_switch` | 是否强制目标换人（比如吼叫） |
| `move.self_switch` | 使用后是否强制自己换人（U-turn/急速折返这类） |
| `move.terrain` / `move.weather` | 招式设置的场地/天气效果 |
| `move.pseudo_weather` | 部分特殊场地效果（比如引力） |

## 关键枚举

- **`MoveCategory`**：`PHYSICAL` / `SPECIAL` / `STATUS`
- **`Status`**：`BRN`（灼伤）/ `FNT`（濒死）/ `FRZ`（冰冻）/ `PAR`（麻痹）/ `PSN`（中毒）/ `SLP`（睡眠）/ `TOX`（剧毒）
- **`Target`**：`ALLY_SIDE`（己方场地）/ `FOE_SIDE`（对方场地）/ `NORMAL`（普通单体）等——单打里最常用的是这三个，判断钉子类招式打哪边要用这个，不能用 `move.side_condition`
- **`Weather`**：`SUNNYDAY`（日照）/ `RAINDANCE`（下雨）/ `SANDSTORM`（沙暴）/ `HAIL`（冰雹）/ `DESOLATELAND`/`PRIMORDIALSEA`（极端天气）/ `DELTASTREAM`
- **`Field`**：`ELECTRIC_TERRAIN`/`GRASSY_TERRAIN`/`MISTY_TERRAIN`/`PSYCHIC_TERRAIN`（场地）、`TRICK_ROOM`（戏法空间，先后手规则反转）、`GRAVITY`（重力）等
- **`SideCondition`**：`STEALTH_ROCK`/`SPIKES`/`STICKY_WEB`/`TOXIC_SPIKES`（各类钉子）、`REFLECT`/`LIGHT_SCREEN`/`AURORA_VEIL`（减伤壁）、`SAFEGUARD`（打谷场）等
- **`Effect`**：volatile 状态，种类很多，目前用到的只有 `TAUNT`（挑衅），其它常见的还有 `CONFUSION`（混乱）、`FLINCH`（畏缩，单回合）、`SUBSTITUTE`（替身）、`LEECH_SEED`（寄生种子）等，具体枚举名看 `poke_env/battle/effect.py`

## 跟这次讨论直接相关的一条

`battle.teampreview_opponent_team` 是这次"要不要保留 Eternatus 打 Arceus-Fairy"这个设计的关键——
团队预览阶段（回合 1 之前）就能拿到对方全部 6 只精灵的种类，不需要等 Arceus-Fairy 真的上场才认出来，
思路 1/2/3（见 `Experiment_Log.md` 对应条目）都可以在这个时间点提前算好"这局要不要特别照顾谁"。
