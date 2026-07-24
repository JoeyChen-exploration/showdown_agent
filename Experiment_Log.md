# 实验记录

> 记录每一轮"改队伍/改策略 → 跑评测 → 看结果"的过程，写期末 report 的时候直接从这里整理，
> 不用事后回忆当时为什么这么改。**每完成一轮实验就往这里加一条新记录**，不要等到最后补。

## 怎么写一条记录

```
## YYYY-MM-DD 简短标题

**目标 / 假设**：这轮想验证或解决什么问题（例："0 只精灵打不过任何 bot，先补齐 6 人队伍看基线"）

**改动**：
- 队伍：具体改了什么（新增/替换了哪些精灵，为什么选它们）
- 代码：`_choose_move` / `teampreview` 逻辑改了什么

**结果**：`python expert_main.py --upi <upi>` 的输出，至少记录：
- 排名 / 分数（`ranked #N with a mark of X.X`）
- 15 个 bot 各自的胜率（哪几个赢了、哪几个没赢，方便看出规律，比如"全部 simple 档都没打过"）

**观察 / 结论**：这轮结果说明了什么，验证了还是推翻了开头的假设

**下一步**：基于这轮结果，下一轮打算改什么
```

---

## 2026-07-21 环境搭建 + 基线测试（占位版本）

**目标 / 假设**：先确认本地开发环境（Showdown 服务器 + Python 依赖）和评测流程能跑通，
用模板自带的占位版本（`choose_random_move` + 队伍只有一只 Pikachu）拿一个基线分数。

**改动**：无——用的是仓库自带的模板默认值，没有手动改队伍或 `_choose_move`。

**结果**：
```
python expert_main.py --upi wche652
wche652 ranked #16 with a mark of 0.0 (0/15 bots beaten)
```
15 个 bot（`simple`/`max_damage`/`random` 三档 AI × `uber`/`ou`/`uu`/`ru`/`nu` 五档队伍强度）全部告负。

**观察 / 结论**：符合预期——占位版本本来就是纯随机选招 + 队伍不完整（只有 1 只精灵，实战中大部分时间
在"没精灵可换"的劣势下硬撑），谈不上策略。评测流程本身跑通了：本地 Showdown 服务器连接正常，
15 场对战全部正常执行完并给出排名/分数，说明工具链没问题，可以开始正式写队伍和策略。

**下一步**：
1. 用 [Teambuilder](https://play.pokemonshowdown.com/teambuilder)（Gen9 → Ubers 格式）搭一支完整的 6 人队伍。
2. 把 `_choose_move` 从随机换成规则系统，先做到"有克制打克制、能斩杀就斩杀"这个最基础版本。
3. 重新跑 `expert_main.py`，按 bot 类型/强度拆解结果，看看新版本具体在哪些对手上还打不过。

---

## 2026-07-21 满编强队 + 仍是随机策略（隔离"队伍强度"这一个变量）

**目标 / 假设**：换上一支网上找的高强度 Ubers 队伍（Ribombee / Koraidon / Arceus-Ghost /
Zacian-Crowned / Eternatus / Kyogre），但 `_choose_move` 先不动、继续用 `choose_random_move`。
目的是把"队伍强度"和"决策逻辑"这两个变量分开看：光靠数值压制，纯随机选招能拿下几场？

**改动**：
- 队伍：`players/wche652.py` 里的 `team` 换成上述 6 人队伍（经本地 `pokemon-showdown validate-team gen9ubers`
  校验通过，退出码 0，格式/搭配合法）。
- 代码：`_choose_move` 未改动，仍是 `self.choose_random_move(battle)`。

**结果**：
```
python expert_main.py --upi wche652
wche652 ranked #15 with a mark of 1.0 (1/15 bots beaten)
```

| 对手 AI 档位 | uber | ou | uu | ru | nu |
|---|---|---|---|---|---|
| simple | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| max_damage | 0.33 | 0.0 | 0.33 | 0.33 | 0.0 |
| random | 0.33 | 0.0 | 0.33 | **0.67（赢）** | 0.33 |

（数字是 3 局取的胜率，>0.5 才算赢下这个 bot；只有 `random-ru` 过线。）

**观察 / 结论**：
- **打 `simple` 档 5 战全灭，一局没赢过**——只要对面会看属性克制/会换人，纯随机选招完全没有还手之力，
  队伍数值再强也没用。说明"决策逻辑"这个变量对 `simple` 档是决定性的，不是队伍能补的短板。
- **打 `max_damage`/`random` 这两档"不看克制"的 AI，单场胜率普遍在 0.33~0.67 之间**——不再是 0.0，
  说明队伍的数值压制确实有效，但纯随机应对太不稳定，3 局里经常 1:2 惜败，赢面被随机性浪费掉了。
- 结论：队伍强度已经"够用"，接下来 `_choose_move` 哪怕只做到最基础的规则（不浪费克制、能斩杀就斩杀、
  不在明显劣势时硬打），预期能把 `max_damage`/`random` 这两档的胜率从"看运气"变成"稳定拿下"，
  `simple` 档大概率还是最难啃的，需要更完整的规则（换人时机、异常状态压制等）才能碰。

**下一步**：把 `_choose_move` 从随机换成规则系统，第一版先做"有克制打克制、能斩杀就斩杀"，
重新跑一次对比这三档 AI 的胜率变化，尤其关注 `max_damage`/`random` 是否如预期变稳定。

---

## 2026-07-21 v1 规则系统上线（硬短路 KO + 单回合价值打分 + Ribombee 开局脚本）

**目标 / 假设**：把 `_choose_move` 从随机换成 `bots_strategy.md` 里设计好的 v1 规则系统，验证是否能把
`max_damage`/`random` 档的胜率从"看运气"变成"稳定拿下"，并看看 `simple` 档能不能开始破防。

**改动**：
- 队伍：不变（Ribombee/Koraidon/Arceus-Ghost/Zacian-Crowned/Eternatus/Kyogre），Ribombee 道具确认保持
  `Focus Sash`（中途写代码时手滑改成过 Heavy-Duty Boots，复查时改了回来，用户已经明确表示不换道具）。
- 代码（`players/wche652.py`）：
  - 硬短路规则：这回合有招式能斩杀对面就直接用（多个可斩杀选项里优先选没反作用力的）。
  - Ribombee 固定开局脚本：第 1 回合无脑放 Sticky Web；第 2 回合按"对面是草系→直接 U-turn / 否则查换人评分决定 U-turn 还是放 Stun Spore"。
  - 通用单回合价值打分：换人评分（进攻端 `_power_score` 最大值 - 防御端类型倍率 × 60），铺垫招式打分（强化幅度 × 速度感知的"扛不扛得住"存活系数），其余伤害招式按 `base_power × STAB × 属性倍率` 打分，所有合法动作统一比较取最高分。
  - 太晶（Tera）本版不触发，按 `bots_strategy.md` 里"明确延后到 v2"的决定。
  - `_incoming_threat_score`/`_power_score` 都是简化启发式（没用 poke_env 自带的 `calc.calculate_damage` 精确伤害计算器，因为那个函数要求双方 stats 完整已知，对手真实 EV/性格未知时用不了），本质是"base_power × STAB × 属性倍率"这个相对打分，不是真实伤害百分比，`_survivability_factor` 里 `/400` 这个换算常数是拍脑袋定的粗略校准，不是精确值。

**结果**：
```
python expert_main.py --upi wche652
wche652 ranked #3 with a mark of 9.0 (13/15 bots beaten)
```

| 对手 AI 档位 | uber | ou | uu | ru | nu |
|---|---|---|---|---|---|
| simple | **1.0（赢）** | 0.33 | 0.33 | **1.0（赢）** | **0.67（赢）** |
| max_damage | **1.0（赢）** | **1.0（赢）** | **1.0（赢）** | **1.0（赢）** | **1.0（赢）** |
| random | **1.0（赢）** | **1.0（赢）** | **1.0（赢）** | **1.0（赢）** | **1.0（赢）** |

**观察 / 结论**：
- **`max_damage`/`random` 两档 15 局全部满分拿下**（上一轮还是 0.33~0.67 看运气），跟预期完全吻合——
  有判断逻辑之后，面对"不看克制"的 AI，队伍的数值压制能被稳定兑现，不再被随机应对浪费掉。
- **`simple` 档从 5 战全灭变成 3/5 拿下**（uber/ru/nu 赢，ou/uu 没赢），说明规则系统对会切人/看克制的
  AI 也开始有效，但还没完全解决——`simple-ou` 和 `simple-uu` 具体是哪个环节没扛住（换人评分算错、
  铺垫时机不安全、还是纯粹打不过对面阵容），需要下一轮针对性排查，可能要看战斗回放（`replays/` 目录）
  具体分析卡在哪个回合。
- 排名从 #16→#3，分数从 0.0→9.0，验证了"通用规则 + 单回合打分"这个架构方向是对的，不需要针对具体
  对手写死规则也能拿到这个效果，符合最初"写通用逻辑，不做打表"的设计原则。

**下一步**：
1. 排查 `simple-ou`/`simple-uu` 具体输在哪个环节（建议看 `replays/wche652/` 里这两场的录像）。
2. 补 `bots_strategy.md` 里还没细化的部分：打分公式权重的进一步校准、Arceus-Ghost/Eternatus 的角色定位。
3. 视情况决定要不要开始设计 v2 的太晶（Tera）触发逻辑。

---

## 2026-07-21 加追踪基础设施（`decision_log` + `analysis/` 消融脚本），冒烟测试就挖到一个真实 bug

**目标 / 假设**：为了给 Report_Outline.md 里"Evaluation 需要机制级验证、不能只看整体胜率"这个缺口
补证据，也为了后续做消融实验（不同权重/开关对胜率的贡献），需要能记录每回合的决策细节。

**改动**：
- `players/wche652.py`：
  - 把之前散落在代码里的几个魔法数字（铺垫打分权重、换人评分权重、`SWITCH_COST`、KO 判断阈值、
    速度安全阈值）都提成模块级常量，加了 `ENABLE_HARD_KO`/`ENABLE_RIBOMBEE_OPENING` 两个功能开关——
    纯重构，不改变默认行为，目的是让外部脚本能在不碰这个文件本身的前提下做参数覆写。
  - `CustomAgent.__init__` 加了 `self.decision_log = []`（纯内存 list，不涉及磁盘写入，不触发
    `file_write_detection.py`），每个决策分支（`ribombee_opening`/`hard_ko`/`general_scoring`/
    `forced_switch`）都会往里面 append 一条记录。
- 新增 `analysis/run_ablation.py`（仓库根目录，不在 `players/` 里，不属于提交范围，可以自由写盘）：
  热加载 `wche652.py`、按配置覆写模块常量、跑完整 15-bot 梯队、把 `decision_log` 和 `poke_env`
  自带的 `battle.observations`（双方每回合的完整事件记录，这部分不用我们自己实现）落盘到
  `analysis/results/<config>/`。

**结果（冒烟测试，只跑了 `baseline` 一组配置）**：
```
python analysis/run_ablation.py baseline
-> rank=#2 mark=9.5 beaten=14/15
```
比上一轮的 13/15 还多赢一场（`simple-uu` 也拿下了）——单纯是同一套代码不同随机数种子跑出来的正常
波动，不是逻辑变了（这次改动是纯重构 + 加日志，没碰任何判断逻辑本身），但也提醒了"目前每个版本
只测一次，样本量偏薄"这个 Report_Outline.md 里已经记过的缺口。

**观察 / 结论——冒烟测试第一场战斗就挖到一个真实问题**：
`decision_log` 显示 vs `simple-uber-1`（对面开局 Zacian-Crowned）这场，第 2 回合我们判断
`we_move_first = True` 选择 U-turn 撤退，但 Ribombee 当场阵亡，U-turn 根本没打出去——说明实际
是对面先手，我们的速度判断错了。根因：`_effective_speed` 对我方用真实计算过的速度，对对手因为
不知道真实努力值只能退化成种族值估算，而这套 bot 队伍的 Zacian-Crowned 实际拉了 252 速度努力值
（真实速度约 414，种族值只有 148），我们的估算方式系统性低估了这类"认真堆速度"的对手。
详细分析和这个案例怎么用在 Reflections 部分，已经写进 `Report_Outline.md`。

**下一步**：
1. 决定要不要修这个速度估算问题（比如对手默认假设"投满速度努力值+中性/加速性格"来估算，
   而不是裸用种族值），还是先记录下来当已知局限性、按原计划继续跑完整套消融实验。
2. 跑完剩下 8 组消融配置（`no_hard_ko`/`no_opening_script`/权重扫描），产出
   `analysis/results/summary.csv` 的完整对比表。
3. 排查 `simple-ou`/`simple-uu` 具体输在哪个环节这件事，现在可以直接用 `decision_log` 分析，
   不一定非要看 replay 视频了。

---

## 2026-07-21 消融跑批发现命名冲突 bug，修复后重跑

**目标 / 假设**：跑上面待办第 2 项——9 组配置的完整消融实验。

**改动**：`analysis/run_ablation.py` 里 `expert_main.gather_bots()` 每次都从编号 1 开始给 bot 账号
命名（`simple-uber-1`、`random-nu-15` 这类），第一次全量跑批时，从第二组配置开始就跟上一组配置
还没完全断开的连接撞名（Showdown 报 `nametaken` 错误），这些场次的异常被 `evaluate_player_vs_bot`
当成"打输了"记了下来——**第一次跑批（`baseline` 之后的 8 组配置）的数据不可信，已经作废**，只有
`baseline` 那组是干净的（它是唯一一次跑批里的第一组，没有历史命名冲突）。修复：每组配置调用
`gather_bots(bot_id_start=config_index * 100 + 1)`，把编号错开，避免跨配置撞名；顺手加了逐场
`[i/N] vs 对手名: winrate=...` 的进度输出。

**结果**：修复后还没重新跑完整套（这次改动是 code review 之后才动手的，详见下一条记录）。

**下一步**：用户提出"每一步是不是该有 subagent 交叉验证"，已经用 `code-reviewer` 子代理审查了
`wche652.py` 和 `run_ablation.py` 的这几轮改动，审查结果处理完之后再重新起跑全部 9 组配置。

---

## 2026-07-21 code review 结果 + 处理

**目标 / 假设**：用户提出质疑"每一步是不是该有 subagent 交叉验证"，之前几轮写了不少实质代码
（`wche652.py` 整套决策逻辑、`run_ablation.py`）都只做了编译检查/写盘检测/实跑验证，没有独立代码审查。
用 `code-reviewer` 子代理审查这两个文件。

**结果**：无 Critical。3 条 Warning + 4 条 Suggestion：

1. **（Warning，重要）硬短路 KO 规则判断"能不能斩杀"时没看招式威力**——`_find_ko_move` 的
   `likely_ko` 条件只看属性倍率和对面血量百分比，招式威力/STAB 只在"已经判定为能斩杀的几个选项里
   挑一个"这一步才用上。会导致偶尔选中一个威力不够、实际打不死对面的"KO 招式"，浪费一回合。
   **用户决定：记录成已知局限性，留到下一个 version 再修，这一版先按现状把消融跑完。**
2. （Warning）`run_ablation.py` 的防撞名方案只在单进程串行跑批时成立，已加注释警告，不支持并行跑多个配置。
3. （Warning）100 的编号间隔是没有保护的魔法数字，如果以后 bot 数量超过 100/配置会静默复发撞名 bug，
   已加 `assert bots_per_config < 100` 提前报错。
4. （Suggestion，未处理）`_is_setup_move` 要求所有 boost 都为正，像 Shell Smash 这种有正有负的
   铺垫招式会漏判——现在队伍里没人用这类招式，不影响，记录备查。
5. （Suggestion，未处理）`_survivability_factor` 是硬阈值 0/1 二值判断，不是连续过渡，会让消融实验里
   权重扫描的结果不连续/有跳变，解读 `analysis/results/*/decisions.csv` 时要注意这一点。
6. （已过时——2026-07-22 修复了第 1 条后这两个常量被删掉了）原文：`CONFIGS` 没有覆盖
   `KO_EFFECTIVE_HP_THRESHOLD`/`KO_NEUTRAL_HP_THRESHOLD` 这两个阈值的消融。修复后 `_find_ko_move`
   改用跟 `_incoming_threat_score` 一致的 `_power_score`/`INCOMING_THREAT_SCALE` 估算，两个阈值
   常量已删除，这条消融覆盖缺口不再适用。
7. 已修复：传入不存在的配置名现在报友好错误，不是裸 `KeyError`。

**观察 / 结论**：写了实质决策逻辑代码之后主动跑一次独立 code review 是值得的——这次直接挖出一条
真实的决策质量问题（KO 判断不看威力），而且是纯人工审查代码逻辑发现的，不是靠跑测试碰出来的，
补上了"光靠实跑验证覆盖不到的角落"。

**下一步**：
1. `_find_ko_move` 不看威力这个问题留到下一个 version 再改（已记进 `bots_strategy.md` 待细化清单）。
2. 重新跑全部 9 组消融配置（这次命名冲突和报错处理都修好了）。

---

## 2026-07-21 9 组消融实验跑完

**目标 / 假设**：修复命名冲突 bug 后重新跑全部 9 组消融配置（`baseline`/`no_hard_ko`/
`no_opening_script`/铺垫权重×2/换人防御权重×2/换人成本×2）。

**结果**：完整的配置列表、结果总表、逐条信号解读、`max_damage-uber` 超时问题的分析和处理方式，
单独写了一份文档：[Ablation_Study.md](Ablation_Study.md)（不在这里重复，避免两份文档打架）。

**观察 / 结论（摘要，完整版见上面链接）**：硬短路 KO 规则有正贡献；铺垫打分权重存在"甜区"
（默认值 30 两侧都更差，调高到 45 是全场最差的一组）；换人相关权重在测试范围内不敏感；
`simple-uu`/`max_damage-uber` 是贯穿多组配置的"摇摆"对手；`max_damage-uber` 这场经常打到
39-42 回合、逼近 90 秒超时墙——**跟用户确认过，不会为了让本地消融数据更干净就放宽这个超时常量**，
因为正式评测用的就是这个 90 秒，放宽了本地测的就不代表真实评测环境，这个问题要留到 v2 从"让打法
更果断、避免拖成拉锯战"这个方向解决。

**下一步**：见 `Ablation_Study.md` 的"下一步"部分（复盘 `simple-uu`/`max_damage-uber` 的
`decision_log`；`no_opening_script` 这类打平的结果需要多轮重跑才能判断是否显著；v2 把"更快结束
拉锯战"列为专门设计目标）。

---

## 2026-07-22 消融实验支持多次重跑（GitHub issue #2），跑筛选出来的敏感配置

**目标 / 假设**：上一轮 9 组消融是"筛选实验"（每组只跑一次），已经区分出敏感变量
（`ENABLE_HARD_KO`/`SETUP_BOOST_WEIGHT`/`SWITCH_COST`）、不敏感变量（`SWITCH_DEFENSE_WEIGHT`）、
信号被噪声盖住需要重跑确认的变量（`ENABLE_RIBOMBEE_OPENING`）。这一轮给 `analysis/run_ablation.py`
加多次重跑支持，对筛出来的敏感/不确定配置跑 3 次取均值，不敏感的 `switch_defense_weight_30/90`
先不重跑（沿用上一轮的单次数据）。

**改动**：`analysis/run_ablation.py` 加 `--repeats N` 参数（默认 1，保留原来的快速筛选模式）。
每个 (配置, 第几次重跑) 组合独立分配 bot 账号编号段避免撞名；`decisions.csv`/`events.csv`
（质化复盘用）只保留第一次重跑的，不随重跑次数膨胀；新增 `per_bot_summary.csv`
（每个对手在多次重跑里的均值/标准差胜率）和聚合后的 `summary.csv`（每个配置的
`mean_mark`/`stdev_mark`/`mean_beaten` 等）。冒烟测试（`baseline` 跑 2 次）验证过机制正常——
`max_damage-uber` 的胜率标准差明显高于其他对手，符合"这场容易被超时噪声干扰"的预期。

**结果**：7 组配置 × 3 次重跑跑完了，`mean_mark`/`stdev_mark`/`mean_beaten`（15 场制）：
`baseline` 9.17/0.29/13.33，`no_hard_ko` 9.00/0.00/13.00，`no_opening_script` **9.50/0.00/14.00**，
`setup_weight_15` **9.50/0.00/14.00**，`setup_weight_45` 8.83/0.29/12.67（全场最差），
`switch_cost_0` 9.00/0.00/13.00，`switch_cost_50` 9.33/0.29/13.67。完整的按对手拆分数据、信号
解读、更新后的敏感度分类，写进了 `Ablation_Study.md` 新增的"2026-07-22 多次重跑确认结果"一节
（不在这里重复）。

**观察 / 结论（摘要，完整版见 `Ablation_Study.md`）**：
1. `max_damage-uber` 这场的输赢在这 7 个参数上不敏感——筛选轮里 `baseline` 那次唯一的"赢"标准差
   高达 0.58，是全表最不稳定的一格，其余 6 组配置全部稳定输（stdev=0）。说明筛选轮"只有 baseline
   赢这场"的对比其实是噪声，不是 baseline 真的更强；这场胜负目前主要由是否卡进 90 秒超时决定，
   继续调这几个权重没用，要靠 issue #4 的结构性改动。
2. `ENABLE_RIBOMBEE_OPENING=False`（关闭开局脚本）和 `SETUP_BOOST_WEIGHT=15`（下调铺垫权重）
   两组独立地把结果稳定在 14/15（stdev=0），机制相同：都是让 `simple-uu` 从稳定输翻成稳定赢，
   而"代价"（`max_damage-uber` 从偶尔赢变稳定输）根据第 1 条其实不算真代价。这解决了筛选轮里
   `no_opening_script` "打平、说不清是不是噪声"的悬案——多次重跑后是清楚的正向信号。
3. 三种完全不同机制的改动（关开局脚本 / 调铺垫权重 / 调换人成本到 50）都能独立把 `simple-uu`
   从稳定输翻成稳定赢，说明背后可能有同一个根因在起作用，值得单独复盘 `decision_log`（issue #6）。

**下一步**：
1. 复盘 `simple-uu` 的 `decision_log`，对比这几组配置在同一局面下的候选打分差异找根因（issue #6）。
2. 测试 `no_opening_script` + `setup_weight_15` 叠加配置，看收益是否叠加还是重叠（issue #8）。
3. `max_damage-uber` 超时问题转给 v2"更快结束拉锯战"的专门设计（issue #4），不再指望调权重解决。

---

## 2026-07-22 复盘 issue #6（simple-uu），挖到 `_switch_score` 一个方向反了的 bug 并修复

**目标 / 假设**：上一条记录留的"下一步"第 1 条——用 `decision_log` 复盘 `simple-uu` 这场，看
`baseline`（稳定输）和 `no_opening_script`/`setup_weight_15`（稳定赢）在同一局面下具体选了什么
不同的动作，找输的根因。

**过程**：
1. 想先靠 `events.csv`（记录双方每回合原始协议事件，本来是为这种复盘场景准备的）拿到
   `battle_tag → 对手用户名` 的映射，结果发现 **`events.csv` 从第一次提交就是空的**（只有表头）——
   定位到根因：poke_env 的 `cross_evaluate()` 每打完一场对局就立刻调用 `reset_battles()` 清空
   `player.battles`，而 `run_ablation.py` 是等 15 个 bot 全打完才去读 `player.battles`，那时候早就
   被清空了。这个"质化复盘"功能其实从没真正工作过。
2. 修复：给 `analysis/run_ablation.py` 的 `build_player()` 加了一个 `_install_battle_archive()`，
   给每个 player 实例的 `reset_battles` 打个补丁——清空前先把 `battles` 归档到
   `player.battle_archive`，这样跑完全部 15 个 bot 后还能拿到完整历史。只改 `analysis/`（不属于
   提交范围），没碰评测框架代码。同时写了 `analysis/trace_matchup.py`——针对单个 (配置, 对手) 组合
   单独跑一次 Bo3，输出写到 `analysis/results/_trace/<config>__<opponent>/`（跟正式消融数据的目录
   分开，不会覆盖已经跑好的 3 次重跑聚合结果），比每次为了复盘一个对手重跑全部 15 个 bot 快很多。
3. 用 `trace_matchup.py` 分别跑 `baseline vs simple-uu`（0/3，全输）和
   `no_opening_script vs simple-uu`（2/3，赢）、`setup_weight_15 vs simple-uu`（3/3，赢），对比
   `decisions.csv` 前几回合的具体选择：
   - `baseline` 里，Ribombee 开局脚本不管对面首发是谁都固定"黏黏网→急速折返"；第三局对面首发
     Metagross 时，Ribombee 第 1 回合被 Psychic Fangs（超能力打毒系 2 倍效果）打到只剩 Focus Sash
     保住的 1 点血，第 2 回合急速折返弹出后，弹出的换人目标（走 `_best_switch`，不是写死的）选了
     **Eternatus**——而 Eternatus（毒/龙）挨 Metagross 的超能力系招式正好是 2 倍弱点，直接被
     Psychic Fangs 一击打空（421→0）。
   - 查 `events.csv` 原始事件确认了这个一击必杀，回头去看 `_switch_score()` 的代码：
     ```python
     defense_risk = max((opponent.damage_multiplier(t) for t in candidate.types if t), default=1.0)
     ```
     poke_env 的 `pokemon.damage_multiplier(t)` 语义是"**这个 pokemon** 挨类型 `t` 攻击时的伤害
     倍率"（查了 poke_env 源码 `pokemon.py`/`pokemon_type.py` 确认，不是猜的）。这行代码算的是
     `opponent.damage_multiplier(t) for t in candidate.types`——**候选人自己的属性打在对手身上的
     倍率**，是进攻效果，不是"候选人换上来会不会被打疼"的防御风险，变量名和实际算出来的东西方向
     完全反了。对应到 Eternatus 案例：算出来的是"毒/龙打钢/超能力系"（很低，钢免疫毒），公式里
     `offense - defense_risk * SWITCH_DEFENSE_WEIGHT` 的惩罚项几乎不扣分，看起来是个"安全"的换人，
     但完全没算到 Eternatus 反过来会被超能力系克制这件事。
   - **这个 bug 影响范围比 simple-uu 这一个对手大得多**：`_switch_score` 是每次强制换人（U-turn
     弹出、精灵阵亡）都会跑的通用逻辑。回头看上一轮消融的"`SWITCH_DEFENSE_WEIGHT`（30/60/90）在
     测试范围内不敏感"这个结论，很可能是因为这个权重乘的量本身就算错了——不管权重调多大，对
     "真正的防御风险"这个维度都没有区分度，调权重看不出差异不代表换人逻辑没问题，恰恰相反。

**改动**：把 `wche652.py` 的 `_switch_score()` 改成
```python
defense_risk = max((candidate.damage_multiplier(t) for t in opponent.types if t), default=1.0)
```
（受害者是 `candidate`，攻击方的属性来自 `opponent.types`——跟文件里 `_power_score`/
`_incoming_threat_score` 已经用对的同一个模式对齐）。改完让 code-reviewer 复查了一遍：确认修复
语义正确、文件里其它 4 处 `damage_multiplier` 调用方向都是对的（只有这一处反了）、`_switch_score`
的三个调用点（`_best_switch`/`_ribombee_opening`/`_best_scored_action`）都只依赖"分数越高越好"这个
相对关系，不依赖旧的错误行为，没有隐藏的向后兼容坑。

**效果（初步，单次 Bo3 复测）**：修复后重跑 `baseline vs simple-uu`，从 0/3（全输）变成 3/3（全赢）。
这次随机首发换了别的对手（不是 Metagross，poke_env 首发是均匀随机的），没能复现一模一样的场景，
但换人选择明显更合理（比如挨 Rotom-Wash 打的换人目标不再是被克制的那个）。

**重要影响 / 后续**：这个 bug 影响每一次强制换人，不只是 simple-uu 这一场——意味着 2026-07-21/22
两轮消融实验（9 组筛选 + 7 组多次重跑确认）**全部是基于修复前的错误换人逻辑跑出来的**，
`Ablation_Study.md` 和 `Report_Draft.md` 3.2-3.4 节现在描述的已经不是当前这版智能体的真实行为。
跟用户确认过，方向是**重新跑一遍完整消融**（7 组配置 × 3 次重跑）拿到基于修复后代码的准确数据，
再重写这几份文档——这个也是很好的报告素材，"从真实对局日志定位到一个方向搞反的核心 bug、修复、
量化改进"这条线，比单纯调参数的消融实验更能体现专家系统"观察 → 推理 →改进"的方法论。

**下一步**：
1. 后台重新跑 7 组配置 × 3 次重跑消融（用修复后的代码）。
2. 跑完后重写 `Ablation_Study.md` 的多次重跑章节和 `Report_Draft.md` 3.2-3.4 节，数据和结论
   都要更新成修复后的版本；`Report_Outline.md` 同步。**2026-07-22 明确**：报告里只呈现数据本身
   （修正前后的胜场对比、观察到的规律），不展开这次是怎么从代码层面调试定位到问题的过程——
   那部分细节留在这份 Experiment_Log 里，不进报告。

---

## 2026-07-22 修正后重新跑完 7 组消融，数据大幅重排

**结果**：`mean_mark`/`stdev_mark`/`mean_beaten`（15 场制，括号里是修正前的旧值对比）：

| 配置 | mean_beaten（新） | stdev（新） | 胜场区间（新） | mean_beaten（旧） | stdev（旧） |
|---|---|---|---|---|---|
| `baseline` | 13.67 | 0.76 | 12–15 | 13.33 | 0.29 |
| `no_hard_ko` | 13.67 | 0.29 | 13–14 | 13.00 | 0.00 |
| `no_opening_script` | 13.67 | 0.29 | 13–14 | **14.00** | **0.00** |
| `setup_weight_15` | **14.00** | **0.00** | 14–14 | **14.00** | **0.00** |
| `setup_weight_45` | **14.00** | **0.00** | 14–14 | 12.67（全场最差） | 0.29 |
| `switch_cost_0` | 13.67 | 0.29 | 13–14 | 13.00 | 0.00 |
| `switch_cost_50` | 13.67 | 0.29 | 13–14 | 13.67 | 0.29 |

**观察 / 结论**：
1. **整体胜场普遍上移**（7 组里 6 组 mean_beaten 从 13.0-13.33 涨到 13.67，两组涨到 14.00），跟
   预期方向一致——换人打分修正之后，各配置的换人质量都变好了。
2. **`simple-uu` 不再是"摇摆对手"**：7 组配置里现在有 6 组稳定赢（beaten_count 2-3/3，多数
   winrate ≥0.78），不再是之前那种"部分配置稳定输、部分配置稳定赢"的分裂状态。之前观察到的
   "三种不同机制的改动都能独立让 simple-uu 翻盘"这个现象，现在看是**同一个根因的三种不同触发
   路径**，根因解决后这个对手本身不再是分歧点。
3. **`SETUP_BOOST_WEIGHT` 的"甜区"结论被推翻**：修正前的数据显示默认值 30 两侧（15/45）都更差、
   45 是全场最差；修正后 **15 和 45 变成并列最好**（都是 14.00，stdev 0），完全不是之前那种
   单侧甜区形状。说明之前那个结论建立在错误的换人打分之上，不能带进报告。
4. **`no_opening_script` 的优势也消失了**：修正前它是唯一跟 `setup_weight_15` 并列最优（14.00，
   stdev 0）的配置；修正后回落到跟 `baseline` 同一档（13.67），不再是一个可以单独拿出来讲的
   正向发现。
5. **`max_damage-uber` 这场的模式完全没变**：`baseline` 仍然是唯一有概率赢这场的配置
   （winrate 均值 0.33，stdev 0.58，跟修正前的数字几乎一样），其余 6 组配置仍然稳定输（0/3）。
   再次确认这场的胜负是 90 秒超时决定的，跟换人打分对不对没关系——修正前后这一条结论完全一致，
   是这次重跑里少数没变的东西。
6. **`baseline` 自己的标准差反而变大了**（0.29 → 0.76，胜场区间从 13-14 变成 12-15）：换人打分
   修正后，遇到"两个换人选项风险接近"的局面时，选择可能变得更容易在两者之间摇摆（不再是错误公式
   给出的一个偏向性很强、几乎不变的答案），三次重跑样本还太小，暂时不确定这是真实变化还是噪声，
   需要更多重跑才能判断。

**下一步**：
1. 用这份新数据重写 `Ablation_Study.md`、`Report_Draft.md` 3.2-3.4 节（撤掉待更新标记），
   `Report_Outline.md` 同步。
2. `SWITCH_DEFENSE_WEIGHT`（30/60/90，之前判定"不敏感"）建立在同一个错误公式上，之前的"不敏感"
   结论也不可信，值得找机会重新测一次（issue #8）。
3. `baseline` 标准差变大这件事先记下来，等以后有机会再跑更多次重跑确认是不是真实效应。

---

## 2026-07-23 v1 遗留的另外两个已知 bug 一起修：对手速度估算、KO 判断威力盲区

**目标 / 假设**：`_switch_score` 那个方向反的 bug 修完之后，用户提出"既然发现了一个 bug，就把 v1
现存的已知 bug 一次修完，严谨一点，再重新跑一遍消融"，不要修一个跑一次、来回折腾。盘点 bots_strategy.md
"待细化"清单和之前 code review 记录，v1 目前有记录、但还没动手的正确性 bug 只有两个（跟 issue #4/#5/
#7/#8 那类"设计/校准/新功能"性质的待办不是一回事，那些不算 bug）：

1. **对手速度估算系统性偏低**（issue #3，2026-07-21 冒烟测试就抓到的真实案例：Ribombee 被速度
   投资过的对手 Zacian-Crowned 反超，第 2 回合阵亡，因为 `_effective_speed` 对未知对手直接退化成
   种族值 148，而对面真实速度约 414）。
2. **硬短路 KO 判断没看招式威力**（issue #13，2026-07-21 code review 挖出来、当时决定留到"下一个
   version"的那条）。

**改动**：
- `_effective_speed`：对手（`stats_known=False`）不再直接用 `mon.base_stats["spe"]`（种族值原始
  数字），改成 `_max_speed_estimate()`——按标准的满配速度个体值/努力值/正性格公式
  `(2*base + 31 + 63 + 5) * 1.1` 估算"这个种族理论上能跑多快"，宁可高估对手速度、多几次保守换人，
  也不要像之前那样低估导致像 Ribombee 那次一样的误判。用真实案例验证过：Zacian-Crowned（种族速度
  148）新估算是 434.5，超过 Ribombee 的真实速度（约 381.7）——现在能正确判断对面更快了。
- `_find_ko_move`：`likely_ko` 判断不再是"属性倍率 + 对面血量百分比"两个独立阈值判断，改成跟
  `_incoming_threat_score` 一致的口径——用 `_power_score(move, me, opp) / INCOMING_THREAT_SCALE`
  估算这一下大概能打掉对面百分之多少血，跟对面当前血量百分比直接比较，只有"估计打得死"才算数。
  威力弱的招式即使属性克制、对面残血，现在也不会被误判成"稳斩"。原来的 `KO_EFFECTIVE_HP_THRESHOLD`/
  `KO_NEUTRAL_HP_THRESHOLD` 两个阈值常量删掉了（改完之后没有代码再用到）。

**验证**：两处改动都单独让 code-reviewer 复查过，均无 Critical/Warning。速度估算那处有一条
Suggestion：现在对所有未知对手都假设"投满速度"，可能让智能体在对面其实很慢的局面里也变得偏保守
（铺垫/回血招式更容易被判定"扛不住"而放弃）——不是逻辑错误，是这个保守估计策略本身的副作用，
留意这次重新消融的数据里铺垫类招式的使用情况是不是变少了。

**结果**：两个修复一起加上后，后台重新跑一遍完整的 7 组配置 × 3 次重跑消融（不再像上一轮那样
修一个跑一次），跑完更新 `Ablation_Study.md`/`Report_Draft.md`。

**下一步**：
1. 等后台消融跑完，把这两处修复的效果和上一轮（只修了 `_switch_score`）的数据放在一起看。
2. 检查 speed-estimation review 提到的"铺垫招式是否变得过度保守"这个疑虑，在新的 `decision_log`
   里能不能看出来。
3. `SWITCH_DEFENSE_WEIGHT` 的重测（issue #8）等这轮跑完之后再排期。

---

## 2026-07-23 三处修复一起生效后，重新跑完 7 组消融

**结果**：`mean_beaten`/15（括号里是"只修 `_switch_score`"那一轮的对比值）：

| 配置 | mean_beaten（新，三处修复） | stdev | mean_beaten（上一轮，只修换人打分） |
|---|---|---|---|
| `baseline` | **14.00** | 0.50 | 13.67 |
| `no_hard_ko` | **14.00** | 0.00 | 13.67 |
| `no_opening_script` | 13.00 | 0.00 | 13.67 |
| `setup_weight_15` | **14.00** | 0.00 | 14.00 |
| `setup_weight_45` | 13.67 | 0.29 | 14.00 |
| `switch_cost_0` | 13.67 | 0.29 | 13.67 |
| `switch_cost_50` | **14.00** | 0.00 | 13.67 |

**观察**：
1. 现在 4/7 组配置（`baseline`/`no_hard_ko`/`setup_weight_15`/`switch_cost_50`）并列最高 14/15，
   比上一轮（只有 2 组并列最高）更多配置达到这个水平——整体上移，跟预期方向一致。
2. `no_opening_script` 这次掉到全场最差（13/15）：细看是 `simple-uber` 这个对手上出问题
   （mean_winrate 0.11，3 次重跑 0/3，其余配置这个对手基本都是稳定赢）。跟前几轮比，"哪个改动
   更好"这件事本身也在随其他修复变化——`no_opening_script` 从来没有在任何一轮里稳定地比默认配置
   更好，三轮里分别是"打平→最优→现在最差"，波动比其它配置都大。
3. `setup_weight_45` 从上一轮的并列最优掉到中间档（13.67），`SETUP_BOOST_WEIGHT` 现在只有
   `15` 这个方向还站得住（三轮里持续拿到 14/15），`45` 这个方向不再有正面证据。
4. `simple-uu` 现在 7 组配置全部是多数胜（≥2/3），不再是任何配置的明显弱点。`simple-uber` 变成
   新的、跨配置波动最大的对手（0/3 到 3/3 都有），值得下一轮复盘。
5. `max_damage-uber` 的模式三轮消融里完全没变过：只有 `baseline` 偶尔赢（这次还是 1/3，
   stdev 0.58），其余配置稳定输——这是目前唯一一个连续三轮、跨越所有代码修复都没变化的结论，
   足够确认是纯粹的结构性超时问题。

**结论（当前有效数据，喂给 issue #8）**：`SETUP_BOOST_WEIGHT=15` 是目前唯一一个在两轮独立重跑
里都拿到 14/15 的改动，值得当作下一版默认值候选；`ENABLE_HARD_KO`（默认开启）也在这轮里跟
`baseline` 打平在最高档，没有新证据支持关掉它。其余几个开关方向都不稳定，不建议现在下结论。

**下一步**：
1. 复盘 `simple-uber` 的 `decision_log`，尤其是 `no_opening_script` 这组为什么会 0/3——新的
   摇摆对手，值得跟当年 `simple-uu` 一样的方式处理。
2. 重新测 `SWITCH_DEFENSE_WEIGHT`（issue #8），三处修复后旧数据都不可信。
3. 用 `SETUP_BOOST_WEIGHT=15` 更新 `Ablation_Study.md`/`Report_Draft.md` 3.3 节当前有效数据。

---

## 2026-07-23 `SWITCH_DEFENSE_WEIGHT` 重测（issue #8）

**结果**：`switch_defense_weight_30`/`switch_defense_weight_90` 各 3 次重跑，均 14.00/15——
跟 `baseline`（默认值 60，同样 14.00）打平，`90` 这组标准差是 0（比 baseline 自己的 0.50 还稳）。

**结论**：30/60/90 全部并列最高。旧的"不敏感"结论（筛选轮测的，那时 `_switch_score` 还有方向反了
的 bug）修复后重新验证依然成立，但原因变了——不是公式本身没有区分度，是换人打分修正之后这个权重
在这个范围内确实不太影响最终胜场。不再往这个参数上投入精调预算，`SWITCH_DEFENSE_WEIGHT` 维持
默认值 60。完整数据见 `Ablation_Study.md`。

**下一步**：复盘 `simple-uber` 的 `decision_log`（`no_opening_script` 那组 0/3 的根因），这是目前
唯一还没解释的信号。

---

## 2026-07-23 全文件系统性 bug 审查（用户要求"把 v1 bug 全部搞定"），挖到一个新 Critical

**目标 / 假设**：连续三处 bug（换人打分方向反、对手速度估算、KO 威力盲区）都是同一类问题——
"变量名/注释看起来对，但没对照 poke_env 真实 API 语义核实"。用户明确要求不要再零散地一个一个碰
运气找，而是趁现在把 `wche652.py` 从头到尾系统过一遍，找出所有还没抓到的同类问题，再统一处理，
不要一个 bug 跑一轮消融来回折腾。

**方法**：让 code-reviewer 子代理不做 diff review，而是逐个函数核对每处读取 `Pokemon`/`Move`/
`Battle` 属性、调用 poke_env 方法的地方，对照 poke_env 源码（不是猜）确认语义符合代码假设；同时
检查算术/比较逻辑方向、状态追踪正确性。明确要求排除已知的"故意设计取舍"（比如没有太晶逻辑、没有
Trick Room 检测、`_survivability_factor` 是二值判断），只找"实现跟旁边注释/docstring 的意图不符"
的真问题。

**发现**（按严重程度）：

1. **（Critical）Judgment（Arceus-Ghost 的招牌招式）的属性从不跟着阵型动态解析**：poke_env 的
   `move.type` 对 Judgment 是静态查表，永远返回原始的一般系（用 `GenData.from_gen(9).moves['judgment']['type']`
   验证过，确实是 `'Normal'`），不会因为 Arceus 换成幽灵盘变成幽灵系（Arceus-Ghost 真实类型是
   `['Ghost']`，同样查了 `gen9pokedex.json` 确认）。后果：
   - `_stab()` 永远不给 Judgment 加成（一般系不在 `[幽灵]` 里）
   - 属性克制算反了方向：对面是幽灵系时，代码算出免疫（0倍，一般系打幽灵系免疫），但真实游戏里
     幽灵系打幽灵系是超克（2倍）——Arceus 打幽灵系对手时，明明是最佳克制，却完全没被打分系统看到
   - 更危险的方向：对面是一般系时，代码算出中性（1倍，一般系打一般系），但真实游戏里幽灵系打
     一般系是完全打不中（0倍，幽灵/一般系互相免疫）——`_find_ko_move` 可能把这种招式的
     `estimated_damage_fraction` 算出一个非零数字、过了 KO 门槛，直接锁定 `create_order` 打出去，
     但实际伤害是 0，等于白白送一个回合
2. **（Warning）十字剑（Scale Shot，Koraidon 核心招式）的多段攻击伤害被低估约 3 倍**：
   `move.base_power` 对多段攻击招式返回的是单次命中威力（25），代码从来没乘上 poke_env 算出来的
   期望命中次数（`move.expected_hits`，十字剑约 3.17 次）。真实期望威力约 79（算上龙系 STAB 约
   119），代码只按 25（STAB 后约 37.5）打分——这不是边缘情况，是十字剑作为候选招式的**每一回合**
   都在发生的系统性低估，比暴风所（120 威力无 STAB）还低估了不少。
3. **（Warning）`_score_move` 判断"钉子招式是否该我方场地已经有了"时，默认钉子类招式都是打对面
   场地**：`move.side_condition` 只说明招式设置的是哪种场地效果，不说明打在哪一侧——现在队伍里
   只有黏黏网符合（确实打对面场地），暂时没触发错误，但以后加反射壁/清新之风这类打己方场地的
   招式就会查错字典（`opponent_side_conditions` 而不是 `side_conditions`），误判成"还没设置过"
   反复重复使用。
4-6.（Suggestion，未处理）：KO 判断/伤害估算没打命中率折扣（比如 85% 命中的火焰放射被当成
   100% 稳中）；通用打分框架没检查状态招式的属性免疫（比如草系免疫麻痹粉，开局脚本自己特判了，
   通用框架没有）；Ribombee 开局脚本"决定撤退去 Kyogre"这个判断理由，跟实际执行换人的
   `_best_switch`（走全体换人候选重新打分）没有强制绑定，多数情况会自然一致但没有代码保证。

**改动**：
- 新增 `_effective_move_type(move, attacker)`：对 Judgment 特判，返回攻击方自己当前的类型
  （`attacker.types[0]`）而不是 `move.type`——Judgment 在真实游戏里永远跟使用者自己的类型一致，
  这个特判本身就是"永远正确"的，不是近似。`_stab`/`_power_score` 改用这个辅助函数。
- `_power_score` 增加 `move.expected_hits` 乘数，修正多段攻击招式的威力估算。
- `_find_ko_move`（`CustomAgent` 类内）原来自己重新算了一遍 `effectiveness`/`power`（跟
  `_power_score` 逻辑重复但没有跟着一起修），改成调用同一个 `_effective_move_type` 辅助函数、
  同样乘上 `expected_hits`，避免两处逻辑各修各的、又漂移出新的不一致。
- `_score_move` 的钉子招式分支改成按 `move.target == Target.ALLY_SIDE` 判断查哪个场地字典
  （`battle.side_conditions` vs `battle.opponent_side_conditions`），新导入 `Target`。

第 4-6 条 Suggestion 用户明确决定这轮先不处理（先集中处理已经确认是错误行为的这三条，Suggestion
级别的留到之后单独排期）。

**下一步**：
1. 三处改动一起让 code-reviewer 复查（正在跑）。
2. 复查通过后重新跑一次完整消融验证效果——尤其关注 Koraidon（Scale Shot 威力修正）和 Arceus-Ghost
   （Judgment 类型修正）相关对局是否有变化。
3. 4-6 条 Suggestion（命中率折扣、状态免疫检查、开局脚本换人绑定）记录备查，暂不处理。

**Code review 结果**：无 Critical。一条 Warning：`_effective_move_type` 的 Judgment 特判在
"Log 里写的'永远正确，不是近似'"这个说法不完全对——一旦攻击方太晶化，poke_env 的 `attacker.types`
会切换成太晶属性，而 Judgment 真实类型是跟随神圣盘、不受太晶影响的，特判会用错类型（具体验证：
我方 Arceus-Ghost 配置的太晶属性是星晶，`PokemonType.damage_multiplier` 对星晶攻击方有特判永远
算中性 1 倍，会重新引入 bug #1 想解决的那种"误判免疫目标为可斩杀"的问题）。查过 `create_order`
在文件里从没传过 `terastallize=True`，我方自己永远不会触发太晶，**这条对我方自己完全不会触发**；
但会影响 `_incoming_threat_score` 对"太晶化的对手 Arceus 用 Judgment 打我方"这种局面的威胁估算
准确性，是个真实但很窄的缺口。一条 Suggestion：`_find_ko_move` 算完 `move_type` 后又调用 `_stab`
重新算了一遍，多余但无害。

**改动（针对 review 结果）**：
- `_effective_move_type` 加 `and not attacker.is_terastallized` 守卫，太晶化时退回 `move.type`
  （不是完美修复——太晶后 Judgment 真实类型仍然是盘决定的，跟 `move.type` 也不一样——但明确比
  "永远算中性"这个确定性错误更安全，且这条只影响我们估计对手威胁的准确度，不影响我方自己的出招）。
- `_stab` 加一个可选的 `move_type` 参数，`_power_score`/`_find_ko_move` 都改成把已经算好的
  `move_type` 传进去，不再各自重复调用 `_effective_move_type`。

两处小改动做了快速语义验证（`is_terastallized` 属性确认存在、模块能正常热加载），没有再单独发起
一轮 code review（改动很小、风险低，review 本身已经指出了具体修法）。

**下一步**：重新跑一次完整消融（换人打分 + 对手速度估算 + KO 威力盲区 + Judgment 类型 +
Scale Shot 威力 + 钉子招式目标判断，六处修复一起验证）。

---

## 2026-07-23 复盘 `no_opening_script` vs `simple-uber` 的 0/3 回归（不是新 bug）

**背景**：之前两轮消融里，`no_opening_script` 对 `simple-uber` 从其它配置的稳定赢变成稳定输
（0/3），六处新修复之后用 `trace_matchup.py` 单独复测，回归依然存在（`baseline` 3/3 赢，
`no_opening_script` 3/3 输），说明不是已修的那几个 bug 造成的，单独复盘 `decision_log`/`events.csv`。

**发现**：第一局具体过程——turn 1 我方直接换 Eternatus 上场（对面首发正好也是 Eternatus，镜像局，
类型中性，这步换人本身没算错）；对面 Eternatus 用 Meteor Beam（能量陨石，120 威力，靠强化道具
当回合直接放）打掉我方 Eternatus 68% 血；turn 2 我方反杀了对面 Eternatus，但 turn 3 对面换上
Zacian-Crowned（无畏之剑特性自动 +1 攻击），残血的我方 Eternatus 直接被剑舞态一击收割，顶上去的
Kyogre 也被同一套流程秒掉。等 Arceus-Ghost 真正上场时已经损失两个精灵，逆转不回来。

**根因分析（两个已知局限叠加，不是新 bug）**：
1. 关掉开局脚本后，Ribombee 换人损失了 Focus Sash 保底血 + 侦察这一步——直接送 Eternatus 上去
   硬吃对面的开局重炮，比走开局脚本先垫一回合更冒险。
2. 对手招式还没揭示时，威胁估算统一假设招式威力 90（`DEFAULT_ATTACK_ASSUMPTION_BP`），而
   Meteor Beam 是 120——这个默认假设本身偏乐观，让"这次换人安全"的判断从一开始就基于一个
   被低估的对手火力预期。

**结论**：不是需要紧急修的 bug——是"不看对方真实威力上限、只看类型克制"这个已知设计局限
（`_power_score`/`_incoming_threat_score` 从来没有承伤/坚固度这个维度）具体体现出来的一个案例。
不在这轮处理，记录下来：
- 对 issue #7（Arceus-Ghost/Eternatus 角色定位）：Eternatus 被当成"先手挡刀"的候选，但挡不住
  高压对手的开局重炮，角色定位需要更明确。
- 对 issue #8（打分权重系统性校准）：`DEFAULT_ATTACK_ASSUMPTION_BP=90` 这个默认假设值得重新
  校准或者做成消融维度之一。
- 对 report Reflections：是个很好的具体案例——"预判安全的换人撞上了模型看不到的对手强招"，
  体现纯规则系统在信息不完整时的局限性。

**下一步**：不再单独处理，留给 issue #7/#8 后续排期；继续等消融跑完看六处修复的综合效果。

---

## 2026-07-23 六处修复综合效果——`baseline` 首次成为全场单独最优

**结果**：`mean_beaten`/15（括号里是上一轮——只修三处——的对比值）：

| 配置 | mean_beaten（新，六处修复） | stdev | mean_beaten（上一轮，三处修复） |
|---|---|---|---|
| **baseline** | **14.33** | 0.29 | 14.00 |
| no_hard_ko | 14.00 | 0.00 | 14.00 |
| no_opening_script | 13.00 | 0.00 | 13.00 |
| setup_weight_15 | 13.67 | 0.29 | 14.00 |
| setup_weight_45 | 14.00 | 0.00 | 13.67 |
| switch_cost_0 | 14.00 | 0.00 | 13.67 |
| switch_cost_50 | 14.00 | 0.00 | 14.00 |

**观察**：
1. **`baseline`（默认参数）首次成为全场单独最优**（14.33/15，3 次重跑里有一次打出 15/15
   满分），比其余所有配置都高——这在四轮消融里是第一次出现。修 Judgment 类型 + Scale Shot
   多段伤害之后，Koraidon/Arceus-Ghost 这两只精灵的核心输出手段终于被正确估算，核心系统本身
   变强了，不再需要靠调这几个权重去弥补。
2. **`simple-uber` 现在被 `baseline` 稳定拿下**（3/3，之前几轮都在 2-3/3 之间摇摆）——直接印证
   Judgment/Scale Shot 修复带来的提升，这两个精灵在这个对局里正是主力输出。
3. **`SETUP_BOOST_WEIGHT` 的"最优值"第三次反转**：15→45→15→45 这几轮里从"最优"变"最优"变
   "较差"变"最优"，没有任何一个非默认值能连续两轮站得住。既然默认值 30（即 `baseline`）现在
   是单独最高分，**不再建议改这个参数**——之前"15 更优"的结论已经被推翻。
4. **`no_opening_script` 依然稳定卡在 13/15**（连续两轮、stdev 都是 0）——这六处修复都没碰
   Ribombee 相关逻辑，跟之前复盘的结论一致（Focus Sash 缓冲 + `DEFAULT_ATTACK_ASSUMPTION_BP`
   偏低共同导致，不是这几个 bug 造成的）。
5. **`max_damage-uber` 的模式连续四轮、跨六处代码修复完全没变过**：只有 `baseline` 偶尔赢
   （这次还是 1/3，stdev 0.58，数字几乎和第一轮一模一样），其余配置稳定输——这是目前整个研究里
   证据最扎实的结论，纯粹是 90 秒超时问题，不受任何已测参数影响。

**结论（当前有效数据，v1 阶段性收尾）**：
- v1 默认配置（不改任何一个已测参数）目前是综合表现最好的版本，六处 bug 修复本身就是最大的
  提升来源，参数微调的边际收益现在看不如预期。
- `SETUP_BOOST_WEIGHT`/`ENABLE_HARD_KO`/`ENABLE_RIBOMBEE_OPENING`/`SWITCH_COST` 都维持默认值。
- `no_opening_script` 的 `simple-uber` 回归和 `max_damage-uber` 的超时问题是仅剩的两个已知、
  已解释、暂不通过调参解决的缺口，分别对应 issue #7/#8 和 issue #4。

**下一步**：
1. v1 阶段性告一段落——回到 issue #9/#11（Report Design/Reflections 部分）或 issue #7/#4/#5
   这些更大的 v2 方向，具体听用户排期。
2. 用 `baseline`（当前默认参数）作为最终数据源重写 `Ablation_Study.md`/`Report_Draft.md`
   3.2-3.3 节。

---

## v1 → v2 分界线（2026-07-23）：从"v1 遇到的问题"到"v2 要加什么"

v1 阶段做的事情性质是单一的：找出决策逻辑里跟设计意图不符的地方（换人打分方向反了、对手速度
低估、KO 威力盲区、Judgment 类型、Scale Shot 多段伤害……），把"写错的东西改对"。六处修复 +
`SETUP_BOOST_WEIGHT`/`SWITCH_DEFENSE_WEIGHT` 等参数的消融确认之后，`baseline`（默认参数）
已经是目前测过的组合里综合表现最好的一版——**这条路线的边际收益已经很低了，继续在这个方向上
找,大概率找不到更多能大幅提升的东西**。

但四轮独立消融（跨越全部六处修复）里始终有一条结论纹丝不动：`max_damage-uber` 这场稳定卡在
超时。这不是"哪个参数没调对"能解释的——它是**决策逻辑里缺了一块能力**：面对一个不断冥想叠盾
+ 回血的对手（Arceus-Fairy），我方没有任何手段主动打断这个循环，只能干瞪眼看着对面越滚越大，
拖到 90 秒超时判负。翻队伍配置发现 Koraidon 带着 Taunt（挑衅），但因为打分公式里没给它写专门
规则，落在"其它兜底"分支固定 10 分，几乎不可能被选中——**工具已经在手上，只是决策逻辑没有
识别出"这个局面正好用得上它"**。

这就是从 v1 推到 v2 的具体链条：**v1 阶段性收尾（找不到更多"改错"的空间）→ 复盘仅剩的已知
结构性缺口（`max_damage-uber` 超时，四轮消融反复验证过跟参数无关）→ 定位到缺口背后的具体
原因（Taunt 存在但没被合理评分）→ v2 第一个具体改动：给 Taunt 加"对面已经在叠盾"的识别规则**
（见下一条记录）。往后 v2 的条目都是同一个模式：不是碰运气加功能，是先找到"现有框架覆盖不到
哪类局面"，再针对性设计。Report 相关工作（Design/Evaluation/Reflections）暂缓，先集中精力
推进 v2、多积累数据和实验记录，留到最后一起写报告。

---

## 2026-07-23 v2 第一个改动：Taunt 反叠盾评分（issue #4）

**目标**：给 `_score_move` 加一条 Taunt 专用规则——对面已经有正的能力等级加成（`opp.boosts`
里有正值，直接证据，不是预判）时，给 Taunt 一个跟已叠加成正比的分数，而不是像之前一样落进"其它
兜底"固定 10 分。新增两个常量 `TAUNT_ANTI_STALL_BASE`/`TAUNT_ANTI_STALL_PER_BOOST`。

**Code review 发现（无 Critical，2 条 Warning）**：
1. 用真实撞到的对局（Koraidon vs `max_damage-uber` 的 Arceus-Fairy）算了一遍：十字剑是龙系，
   龙打妖精免疫（0 倍），Koraidon 唯一能打的是烈焰冲锋——但我们从不太晶化，Koraidon 本身不是
   火系，没有 STAB，固定 120 威力。冥想每次 +1 特攻+1特防（`boost_total` 一次加 2），按最初的
   权重（`BASE=60, PER_BOOST=15`）算，冥想一次 Taunt 才 90 分，还是打不过烈焰冲锋的 120，
   要冥想两次打平（还会因为排序稳定性被烈焰冲锋抢到），三次才真正超过——等真正触发的时候，
   对面已经叠了三层，为时已晚，没达到"尽早打断"的设计目的。
   → **改动**：`TAUNT_ANTI_STALL_PER_BOOST` 从 15 调到 35，冥想一次（`boost_total=2`）就是
   60+70=130，超过烈焰冲锋的 120，能在对面刚开始叠盾时就打断，不用等到叠三层。
2. 注释里"正的能力等级加成就是直接证据证明对方用了强化招式"这个说法过于绝对——自动强化类特性
   （Moody/愤怒的甲壳等）或临界浆果也可能造成加成。不影响实际判断是否正确（不管加成怎么来的，
   打断都是对的），只是措辞不够精确，已改成更准确的表述。

**验证**：改完权重后单独用 `trace_matchup.py` 复测 `baseline vs max_damage-uber` 两次，
都还是打满 90 秒超时（`decisions.csv` 里连一条决策记录都没有，说明可能连一整局都没跑完就撞了
时间墙——这场对局本身单独拿出来打，即使只对这一个 bot，也经常吃不满 90 秒的预算，样本量
（n=2）太小还看不出这次改动有没有实质帮助）。

**下一步**：
1. 单场复测样本太小，参考意义有限——better 的验证方式是跑一次完整消融（对比 Taunt 加分前后
   `max_damage-uber` 的胜率/标准差有没有变化），而不是反复单独复测这一场。
2. 如果这样调完还是经常吃满超时，说明"打断叠盾"本身可能不够，还需要"更快结束拉锯战"更结构性的
   方案（比如接近超时时主动收紧决策容错、优先选更快解决战斗的动作）。

---

## 2026-07-23 Taunt 修复效果验证 + 挖到前提假设本身是错的

**验证**：`baseline`（含 Taunt 修复）跑一次完整 3 次重跑消融，`max_damage-uber` 这场结果——
`mean_winrate=0.33, stdev=0.58, beaten=1/3`——**跟修复前一模一样，连续第五轮完全没有变化**。

**追查根因**：单独测这一场的样本量太小（n=3）说明不了太多，但"完全没有任何变化"这个信号本身
值得深挖——回头去查 `bots/max_damage.py` 的源码（`max_damage-uber` 用的正是这个 AI 风格），
发现整个决策逻辑只有一行：

```python
best_move = max(battle.available_moves, key=lambda move: move.base_power)
```

**永远选当前威力最高的招式，没有任何其它判断**。冥想（Calm Mind）和自我再生（Recover）威力
都是 0，只要神灵判决（Judgment，100 威力）还有 PP，这个 bot 就永远不会用冥想或回血——
`Opponent_Roster.md` 里"冥想+回血组合拖久了会滚雪球"这条描述，是按"真人/会做判断的对手会怎么
打这套配置"写的，对这个具体 bot 根本不成立。

**这就是 Taunt 修复完全没效果的真正原因**：它专门针对"对面已经在叠盾"这个信号打分，但这个信号
在 `max_damage-uber` 身上从来不会出现——不是修复没做对，是**修复瞄准的场景在这个对手身上压根
不存在**。真正拖长战斗的原因大概率只是 Arceus 种族值本身够肉、加上 Judgment 打在我方队伍上
大部分是中性伤害，纯粹是双方磨伤害磨得慢，跟"能不能打断叠盾"无关。

`Opponent_Roster.md` 对应描述已经加了修正说明。`simple`/`random` 两种风格没有查源码，
不确定是否也是纯"最大威力优先"这种简单逻辑，或者真的会用到冥想（`simple` 用的是 poke_env 自带
的 `SimpleHeuristicsPlayer`，逻辑比 `max_damage` 复杂，但没具体验证过是否会用冥想）。

**这次经历本身是个值得记的教训**：一开始基于"这套配置理论上应该怎么打"的常识判断（冥想+回血=
滚雪球）设计了修复，没有先去确认"这个具体对手的 AI 实际上会不会这么打"，导致修复方向从一开始
就没瞄准真正的原因。以后遇到"针对某个具体 bot 行为设计对策"的场景，应该先查对应的 `bots/*.py`
源码确认真实决策逻辑，而不是套用"这套宝可梦配置一般怎么打"的经验假设。

**Taunt 修复本身要不要留着**：不撤销——对 `simple`/`random` 风格或其它真的会叠盾的对手（如果
存在）可能还是有用，且没有证据表明它有负面效果（只在对面已经出现正面加成时才触发，不会误伤）。
只是不再指望它能解决 `max_damage-uber` 这个具体问题。

**下一步**：
1. `max_damage-uber` 超时问题回到"双方磨伤害磨得慢"这个更朴素的根因，重新想方案——比如查我方
   打 Arceus-Fairy（妖精系）时哪些招式是中性/被抵抗，有没有更好的应对精灵/招式组合。
2. 有空的话查一下 `simple`/`random` 的实际决策逻辑，确认 Taunt 修复对这两种风格是否真的有用。

---

## 2026-07-23 v2 正式开始：克制对照表（issue #7，回应 Eternatus vs Arceus-Fairy 案例）

**背景**：复盘 `max_damage-uber` 赢的那局发现，Sludge Bomb（我方 Eternatus）打 Arceus-Fairy 是
2 倍超克，一下能打掉 74% 血，是那局能快速结束的关键。担心的场景是：如果 Eternatus 在真正遇到
Arceus-Fairy 之前就先阵亡/被消耗，等对面真派出 Arceus-Fairy 时手上没有这张牌，就只能拿中性伤害
慢慢磨——这可能是拖到超时的真正原因之一。

**方案讨论**：先聊了三个思路（简单到复杂），最后选了通用版：不止对 Eternatus/Arceus-Fairy 这一对
硬编码，而是团队预览阶段就把"我方每只精灵 vs 对方每只精灵"的克制关系都算一遍，建一张表。之所以
可行——`battle.teampreview_opponent_team`（见 `Poke_Env_API_Reference.md`）团队预览阶段就能
拿到对方全部 6 只精灵，而 `_switch_score` 这个函数完全是靠双方**属性**算的（不依赖对手招式是否
已经揭示），所以团队预览这个时间点，双方属性数据都齐全，可以直接对 6×6 提前算完，不用等实际
交手才知道。

**设计（分两层，先只做第一层）**：
1. **团队预览时建表**：对对方每只精灵，在我方 6 只里找 `_switch_score` 最高的一个，只有分数
   明显够高（不是"随便谁都比谁好一点"这种弱信号）才收录进表。只在 `teampreview()` 里算一次、
   缓存起来，不是每回合重算。
2. **反应式加分（先做这一层）**：对面真正把某只精灵派上场、且这只精灵在表里有对应的
   "designated counter"时，给那只 counter 的换人分数加一个加分，让它更快被换上来抓住属性优势。
3. **预留式压制（先设计，暂不实现）**：对面还没放出目标精灵之前，压低对应 counter 被随便消耗掉
   的倾向——更复杂（要判断"目标是否已经不可能再出现"这类状态），先不做，等第 2 步跑出数据后
   如果还是经常出现"目标出现时 counter 已经阵亡"，再回头做这一层，避免两层一起上、分不清是哪层
   在起作用。

**下一步**：实现第 1+2 层，code review，跑消融验证（重点看 `max_damage-uber`，同时确认没有
让其它 14 个 bot 的表现变差）。

**实现**：新增 `_build_counter_table(battle)`（团队预览时对 6×6 组合算 `_switch_score`，超过
`COUNTER_TABLE_THRESHOLD=100` 才收录）、`self._counter_tables`（按 `battle_tag` 缓存，一个
player 实例要连续打很多场）、`teampreview()` 里建表、`_best_scored_action`/`_best_switch`
两处换人打分都加 `COUNTER_MATCH_BONUS=40` 的判断。

**Code review 结果**：无 Critical。一条 Warning：如果对方精灵**换人时**触发种类改变（比如
Palafin 英雄化，团队预览时是 `palafin`，真正变身后 `.species` 会变成 `palafinhero`），表的
key 会跟实际对不上，对应加分会静默失效——查过 `bots/teams/` 全部 15 个 bot 的队伍文件，
**没有 Palafin**，这条对本项目完全不会触发，记录不修。另外指出 Ribombee 开局脚本（回合 1-2）
的换人判断直接调 `_switch_score`，没有经过对照表加分——这是已有的"前面分支优先、后面逻辑不再
生效"这套设计的自然结果，不是新 bug，先接受这个范围限定（对照表只在开局脚本结束后、进入通用
打分/强制换人分支时才生效）。

**下一步**：跑一次完整消融验证效果。

---

## 2026-07-23 克制对照表验证结果：`max_damage-uber` 连续第六轮数字完全没变，推翻"打不动"假设

**结果**：`baseline`（含克制对照表）3 次重跑，`max_damage-uber` 还是精确的
`mean_winrate=0.33, stdev=0.58, beaten=1/3`——从修 `_switch_score` 那轮开始算，这是**连续
第六轮完全相同的数字**，跨越三处修复、六处修复、Taunt 反叠盾、现在克制对照表，四种完全不同方向
的改动，这个数字一次都没变过。

**追查**：翻 `decisions.csv` 找这次跑到的 Arceus-Fairy 对局（`battle-gen9ubers-5133`），
发现关键事实——**这局 Arceus-Fairy 是被 Zacian-Crowned 的白刃斩（Behemoth Blade）两下解决的
（100%→7%→击杀），根本没走"换人"这一步**（Zacian-Crowned 是因为之前别的强制换人顺路留在场上）。
查了一下：白刃斩是**钢系**招式，钢系打妖精系同样是超克（2 倍）——不是只有 Eternatus 的污泥炸弹
（毒系）能超克 Arceus-Fairy，Zacian-Crowned/Koraidon 的钢系招式也可以，我方队伍对这只精灵至少
有两条独立的超克路线。

**结论（推翻之前的假设）**：从 2026-07-21 第一次发现 `max_damage-uber` 超时问题开始，一直
默认"我方打不动这只精灵/资源没留对"是根因，围绕这个假设试了 Taunt 反叠盾和克制对照表两版 v2
功能，**都没有改变这个数字一分**。现在看这个假设本身站不住——我方对 Arceus-Fairy 从来不缺
超克手段，不管当时手上是谁大概率都能打得动。真正拖时间、导致超时的原因，大概率**跟"能不能打赢
这一场"完全无关**，而是 Bo3 三局里只要任意一局（不一定是遇到 Arceus-Fairy 的那局）因为其它原因
磨得慢，整个 90 秒的总预算就可能超支——这更像是一个纯粹的**时长/网络延迟问题**，不是我们这边
的决策质量问题。三轮完全不同方向的策略改动都没能撼动这个数字，是相当有力的证据。

**处理**：不再针对 `max_damage-uber` 这一个具体对手继续设计规则——这条路线大概率已经走到头了。
如果还想改善这类超时问题，方向应该从"专门解决这一个对手"改成"整体上让所有对局更快结束"（比如
更激进地追求斩杀、减少不必要的换人回合），但这已经是完全不同的设计方向，不是这几轮尝试的延续。

**Taunt 反叠盾/克制对照表要不要保留**：两个都保留——都没有证据表明对其它 14 个 bot 有负面影响
（这轮 3 次重跑，其余 14 个 bot 全部维持 100% 胜率或接近），只是没能解决当初设想要解决的那个
具体问题，作为通用机制本身没有问题，以后可能在别的对局里发挥作用。

**下一步**：
1. `max_damage-uber` 超时问题从"针对性设计"改成"整体更果断"这个更大的方向，或者先接受这是
   一个已知的、暂时无法通过决策逻辑解决的结构性损失（15 个 bot 里的 1 个）。
2. 克制对照表已经是个通用机制，值得找机会看看它在其它对局里有没有实际发挥作用（不一定是
   `max_damage-uber`）。

---

## 2026-07-23 v2 继续：把"延迟收益"这个能力做进通用打分框架

**背景讨论**：聊 Gemini 对我方队伍"黏黏网强攻队"的分析时，用户观察到——我们明确选择的是单回合
贪心打分（不做多回合搜索），但队伍核心机制黏黏网的价值完全要靠"未来对面还会换人几次"才能兑现，
这是一个结构性的不匹配。具体机制上确认过：黏黏网**不影响对面当前在场的精灵**，只在"以后有新精灵
换上来"那一刻才生效——放的那一回合，对当下局面的即时收益严格是 0。这正是 `_score_move` 现在把
钉子类招式写成固定 35 分兜底、而不敢交给通用框架自己判断的原因：贪心框架天生看不到"这一步以后
才兑现"的价值，留给它自己判断，大概率永远选立即有收益的攻击招式（`no_opening_script` 配置的
消融数据也证实了这一点：交给通用框架后 13.00/15，比带脚本的 14.33/15 明显更差）。

**方案**：不去动 Ribombee 那段硬编码开局脚本本身，而是先把"延迟收益"这个能力**做进通用打分
框架**，看通用框架加上这个能力之后能不能自己算对。具体做法：钉子类招式的分数不再是固定值，
改成跟"对面还有多少只精灵可能在未来换上来"挂钩——`battle.opponent_team` 能查到对面已经阵亡
几只，`6 − 阵亡数 − 1`（减 1 是因为当前在场那只已经受不到影响了）就是"未来还可能触发几次钉子
效果"的估计，这个数字越大钉子价值越高，对面只剩最后一只精灵时价值趋近于 0。

**验证计划**：加完之后，用这个新公式分别测"带开局脚本"和"关开局脚本交给通用框架"两种配置——
如果关脚本之后跟带脚本的差距明显缩小甚至反超，说明通用框架现在真的能自己判断"该不该放钉子"了，
硬编码脚本可以考虑退役；如果差距还是很大，说明这个启发式不够，硬编码继续留着。用数据决定，不靠猜。

**下一步**：实现、code review、跑消融（`baseline` + `no_opening_script`都要跑，对比差距变化）。

**实现**：新增 `HAZARD_VALUE_PER_FUTURE_SWITCH_IN=20.0`，`_score_move` 里钉子/减益壁类招式的
打分从固定 35 分改成 `20 × 对方（或己方，按 move.target 判断）还剩几只精灵可能换上来`——用
`battle.team_size − 已阵亡数` 算剩余存活数，减 1（当前在场那只已经受不到影响）。

**Code review 结果**：无 Critical/Warning。确认 `battle.opponent_team` 只含已亮相精灵不会导致
低估（没亮相的必然还活着，`team_size − 已阵亡数` 这个算法本身不依赖亮相与否）；确认我方 `battle.team`
从第一回合起就完整可靠；用 `battle.team_size` 替代原来写死的 `6`（review 建议，已采纳，更稳健）。
提示：这套公式目前主要在 `ENABLE_RIBOMBEE_OPENING=False` 时才会真正生效——开局脚本开启时黏黏网
走的是脚本分支，不经过 `_score_move`，这是预期行为不是 bug。

**验证结果**：
1. 先单独测 `baseline` vs `no_opening_script` 两组：`no_opening_script` 从固定的 13.00/15 涨到
   13.33/15（stdev 0.29），跟 `baseline`（14.33/15）的差距从 1.33 缩到 1.00——**方向是对的，
   通用框架现在确实能算对一部分黏黏网的价值**，但还没追平带脚本的版本。
2. 补齐剩下 5 组配置、凑完整 7 组消融后重新出图，`no_opening_script` 这次又回落到 13.00/15——
   查了 per-bot 明细，输的还是老熟人 `max_damage-uber`（0/3，结构性超时问题，跟这次改动无关）和
   `simple-uber`（0/3，之前记过的开局脚本回归，同样跟这次改动无关），不是新问题，是"3 次重跑"
   这个样本量本身的正常波动（跟 3.1 节讲的方法论区分是同一回事——这次亲身撞上了）。
3. `max_damage-uber` 这次还是精确复现 `mean_winrate=0.33, stdev=0.58, beaten=1/3`——**连续第七轮
   完全没变过**，跨越三处修复、六处修复、Taunt、克制对照表、这次的延迟收益公式，五种完全不同方向
   的改动，一次都没能撼动这个数字，是这份研究里最扎实的一条结论。

**结论**：延迟收益框架化这个方向部分成功——证明了"给通用框架补上对的信息，它确实能算得更好"这个
思路本身是对的，但目前这版公式还不足以完全替代硬编码开局脚本，脚本继续保留。这个能力本身是通用的
（不止服务于 Ribombee 开局），以后队伍里如果加反射壁/光墙这类己方场地招式，也能直接受益，不用
再单独写一次。

**下一步**：
1. 硬编码开局脚本继续保留，这版延迟收益公式作为通用框架的长期改进保留（不影响现有分支的行为）。
2. `max_damage-uber` 的超时问题正式认定为当前决策逻辑范式下无法解决的结构性损失，不再单独立项
   尝试解决，除非有全新思路。
3. 数据源已经是当前代码的完整 7 组消融，`analysis/figures/ablation_mean_beaten.png` 已重新生成。

---

## 2026-07-23 v2 新常量首次消融筛选，`max_damage-uber` 八轮以来第一次被真正打赢

**背景**：v2 加的三个新能力（Taunt 反叠盾、克制对照表、延迟收益打分）用的常量都只是写代码时定的
初始值，从没做过消融扫描。用户要求补上这一步，跟 v1 那几个常量同等对待。给 `analysis/run_ablation.py`
的 `CONFIGS` 加了 8 组新配置（`COUNTER_TABLE_THRESHOLD`/`COUNTER_MATCH_BONUS`/`TAUNT_ANTI_STALL_BASE`/
`TAUNT_ANTI_STALL_PER_BOOST`/`HAZARD_VALUE_PER_FUTURE_SWITCH_IN` 各测两侧邻近值），先跑一轮
单次筛选（issue #8）。

**结果**：6 组都停在正常的单次 14/15 水平，没有特别信号。两组例外：
- **`counter_threshold_60`（`COUNTER_TABLE_THRESHOLD` 100→60）打出 15/15 满分**——查了
  `per_bot.csv`，`max_damage-uber` 这场 `winrate=1.0`，**这是连续八轮消融以来，第一次有
  非 `baseline` 之外的配置真正赢下这场**，而且不是险胜。再查回合数：三局全部在**第 14 回合**
  结束，远低于这场历史上常见的 39-42 回合。降低克制对照表的门槛（意味着更多对手精灵会被标记为
  "有对应克制手段"、触发换人加分的场景变多）看起来让这场打得更快更果断，直接避开了超时。
- `taunt_base_30`（`TAUNT_ANTI_STALL_BASE` 60→30）掉到 13/15，方向不明确，需要确认是否真实。

**注意（方法论）**：这仍然只是单次筛选结果，`max_damage-uber` 历史上方差极大（`baseline` 自己
偶尔赢这场时标准差就有 0.58），不能因为一次 15/15 就下结论——正在跑 3 次重跑确认
`counter_threshold_60`/`taunt_base_30` 这两组信号是否站得住。

**下一步**：等 3 次重跑确认结果，如果 `counter_threshold_60` 真的稳定解决 `max_damage-uber`，
这会推翻"这是当前算法范式解决不了的结构性问题"这个刚下不久的结论——需要重新看待。

---

## 2026-07-23 3 次重跑确认：`counter_threshold_60` 的信号是假的，单次筛选的运气

**结果**：
- `counter_threshold_60`：`mean_beaten` 从单次的 15.00 掉回 **14.33/15**（跟 `baseline` 一模
  一样）。`max_damage-uber` 这场单独查——`mean_winrate=0.33, stdev=0.58, beaten=1/3`，
  **精确复现了历史上其它所有配置的同一个数字**。上一条记录里那次"三局全部 14 回合结束、干净
  利落赢下 `max_damage-uber`"的单次筛选结果，就是单纯运气好抽到了这场历史上本来就有 33% 概率
  会赢的那一侧，不是 `COUNTER_TABLE_THRESHOLD` 调低真的解决了什么。
- `taunt_base_30`：回到正常的 14.00/15（比筛选轮的 13.00 更好），也没有变差，同样是单次样本
  的噪声。

**结论**：`max_damage-uber` 是纯粹的结构性超时问题这个判断**不需要推翻，反而被这次意外插曲
再次印证**——现在是第九轮独立验证得到同一个基本事实：不管代码怎么改，这场赢不赢基本就是一次
概率约 1/3 的抽签，任何单次结果（哪怕是 15/15 满分）都不能当真，必须多次重跑才能判断。

**这次插曲本身是个很好的方法论案例**：从"单次筛选打出满分、以为找到了解法"到"3 次重跑打回原形"，
完整走了一遍 3.1 节讲的"为什么不能信单次结果"这个道理，而且是发生在我们自己身上、亲身经历的，
比空讲道理更有说服力，适合直接写进 report（Evaluation 3.1 或 Reflections 都可以，具体待写作时
决定放哪）。

**v2 常量最终结论**：8 个新常量里，筛选+确认下来没有一个被证明比默认值更好，也没有被证明更差——
`COUNTER_TABLE_THRESHOLD`/`COUNTER_MATCH_BONUS`/`TAUNT_ANTI_STALL_BASE`/`TAUNT_ANTI_STALL_PER_BOOST`/
`HAZARD_VALUE_PER_FUTURE_SWITCH_IN` 全部维持当前默认值，不用再继续测其它候选值——这几个常量
现在等同于 v1 那几个常量的地位（消融验证过，默认值站得住）。

**下一步**：v2 常量校准工作到此完成，`analysis/results/summary.csv` 保持 7 组核心配置的
版本不变（screening/confirm 用的 8+2 组数据留在各自子目录里，不进主汇总表）。

---

## 2026-07-23 v2/v3 边界划定 + v2 现阶段成果诚实小结

**v2 vs v3 划分**：issue #7（Arceus-Ghost/Eternatus 角色定位）性质上还是"给现有单回合打分框架
加更精细的判断能力"，跟 Taunt/克制对照表/延迟收益打分是同一类工作，继续算 v2。issue #5（太晶化）
是第一次要给决策框架加一个之前完全不存在的新决策维度（要不要用、什么时候用、变成什么属性），
不是优化现有逻辑，从这里开始正式进入 v3。

**v2 现阶段成果小结（如实记录，不夸大）**：在"打赢多少个 bot"这个核心指标上，v2 目前**没有带来
任何提升**——`baseline` 从 v1 收尾时的 14.33/15，到 v2 三个新功能 + 常量校准完成后，还是精确的
14.33/15，一分没变。v2 真正交付的是：
1. 决策框架新增三个通用能力（Taunt 反叠盾、克制对照表、延迟收益打分），消融验证过没有负面影响，
   只是在当前这 15 个固定对手身上还没有场景真正触发到能翻盘的地步。
2. 排除了一个错误方向——`max_damage-uber` 超时问题被九轮独立验证确认是结构性问题，不是决策
   逻辑能解决的，避免继续在死胡同里投入精力（issue #4 已关闭）。
3. 校准方法论往深一层推广——v2 自己的新常量现在也走了跟 v1 常量同等严谨的筛选+确认流程
   （issue #8 已关闭）。
4. 过程中纠正了好几次错误假设（Gemini 晴雨天联动分析错误、"冥想回血"这个错误前提、单次筛选
   假信号），这类"发现问题→查证据→纠正"的过程是很实在的 Reflections 素材。

**下一步**：开始 issue #7，先用 `decision_log` 数据看 Arceus-Ghost/Eternatus 目前实际的出场
频率和招式使用情况，不凭空讨论"应该扮演什么角色"。

#####这个时候已经没有思路该如何解决这个问题了 永远是过不了max-uber#######

---

## 2026-07-23 issue #7 起步：用 `decision_log` 查实际出场频率，意外发现 Koraidon 被严重冷落

**方法**：不凭空讨论"应该扮演什么角色"，先查 `baseline` 的 `decisions.csv`（repeat 0，已提交），
统计每只精灵作为"当前在场"精灵出现在多少条决策记录里，以及具体用了哪些招式/走了哪些分支。

**出场频率**（`my_pokemon` 出现次数，能反映实际使用强度）：

| 精灵 | 出场决策数 |
|---|---|
| Ribombee | 219 |
| Kyogre | 206 |
| Eternatus | 184 |
| Arceus-Ghost | 177 |
| Zacian-Crowned | 159 |
| **Koraidon** | **59** |

**Arceus-Ghost/Eternatus 的角色（数据支持）**：
- **Arceus-Ghost**：主力输出是 Judgment（86 次，压倒性第一），偶尔 Aura Sphere（24）/Power Gem（14）
  补充；**冥想几乎从未被选中**（top 10 里完全没出现）；很少被强制换出（`forced_switch` 只 8 次）。
  实际角色是"稳定特攻输出手，不强化，靠地位坚挺"。
- **Eternatus**：三个主力攻击招式（陨石光束 39 / 污泥炸弹 39 / 龙星群 36）用量几乎均分，没有明显
  主力；换出频率明显更高（`forced_switch` 18 次，是 Arceus-Ghost 的两倍多）。实际角色是"灵活
  特攻手，但没有固定打法，比较脆"。

**意外发现**：Koraidon 出场数只有 59，不到其它精灵的三分之一，明显被冷落，不在 issue #7 原本
聚焦的两只精灵里，但值得先查清楚——用户决定先深挖这个。

**下一步**：查 Koraidon 为什么几乎不出场——是很少被换上来（`_switch_score`/`_power_score` 系统性
偏低），还是换上来了但很快就阵亡/被换走。

**追查结果（范围比 Koraidon 大得多）**：
- **被选为换人目标的次数**：Eternatus 75、Zacian-Crowned 66、Kyogre 64、Arceus-Ghost 62、
  Ribombee 53、**Koraidon 30**——Koraidon 被换上来的次数是最低的，大约只有次低者（Ribombee）
  的一半多，直接解释了它出场决策数偏低。
- **Koraidon 每次出场的具体记录**（完整列在这条日志的原始输出里）：常在较晚回合（13-20 回合
  常见）才被换上，进场时经常已经是 0.88 血（大概率是入场时踩了隐形岩的标准 1/8 掉血，不是
  Koraidon 特有问题）；模式基本是"上来打一两下 Scale Shot/Flare Blitz，然后很快换走或阵亡"，
  没有一次表现出"站稳打持久战"的样子。
- **决定性发现**：查了 `move:swordsdance`/`move:calmmind`/`move:taunt` 在整份 `baseline`
  单次跑（全部 15 个 bot）数据里的出现次数——**一次都没有**。不只是 Koraidon 的剑舞没被选中过，
  Zacian-Crowned 的剑舞、Arceus-Ghost 的冥想同样一次都没触发过。

**根因分析**：矛头指向 `_survivability_factor`——这是个二值门槛（0/1），只有"预估来袭威胁"低于
阈值（先手 0.5、后手 0.35，乘以 `INCOMING_THREAT_SCALE=400`）才放行铺垫类招式，否则打分直接
归零。看起来这个门槛在实战里几乎从不通过。更值得注意的是：**这次对手速度估算修复（保守假设对手
投满速度）让"我方先手"判定变得更保守，会更频繁触发更严格的后手阈值（0.35）**，两个改动叠加，
可能让这道门槛比设计初衷更难通过。这也顺带解释了之前 `SETUP_BOOST_WEIGHT` 消融"最优值"每轮
反转的怪现象——如果这个乘数大多数时候是 0，具体权重设多少几乎不影响结果，能不能凑巧翻盘全看运气。

**处理决定**：这个问题比 issue #7 原计划的范围大（不是 Koraidon 一个人的问题，是全队铺垫类招式
共同的问题），但用户决定**先不处理**——现在还没开始太晶化（v3 起点），不想在 v2 收尾阶段又
开一条新线。讨论过"换掉 Koraidon"和"修 `_survivability_factor` 门槛逻辑"两个方向：换精灵只能
治标（Zacian/Arceus-Ghost 的铺垫招式照样会撞上同一堵墙），修门槛逻辑才是治本，以后真要处理时
优先看这个方向。这条发现先存档，不列入当前任务。

**具体后续 TODO（用户明确要求记下来）**：以后回头处理时，应该对 `_survivability_factor` 涉及
的几个常量做一次专门的细化消融——`FASTER_SURVIVAL_THRESHOLD`（现在 0.5）、
`SLOWER_SURVIVAL_THRESHOLD`（现在 0.35）、`INCOMING_THREAT_SCALE`（现在 400）——现有的
`SETUP_BOOST_WEIGHT` 消融测的是"铺垫招式的价值权重"，但根本没测过"这道门槛本身松紧合不合适"，
两件事不是一回事，之前的消融从没覆盖过后者。这是重新设计/校准这套门槛逻辑之前，第一步该做的事。

---

## 2026-07-23 v3 正式开始：太晶化（issue #5），MVP 设计

**范围确认**：这是第一次给决策框架加一个之前完全不存在的决策维度（要不要太晶化、什么时候用），
跟 v2 那种"给现有单回合打分框架补充信息"性质不同，正式算 v3 起点（跟 issue #7 的划分讨论一致）。

**已确认的 poke_env API**（详见 `Poke_Env_API_Reference.md`）：`battle.can_tera`（这回合能不能
太晶）、`battle.used_tera`（这局用没用过，整局限一次）、`mon.tera_type`（配置的太晶属性）、
`mon.stab_multiplier`（已经内置太晶同属性 2.0 倍加成的逻辑）、`self.create_order(move,
terastallize=True)`（发出太晶化+出招的指令，确认过参数存在）。我方 6 只精灵配置的太晶属性：
Ribombee 钢、Koraidon 火、Arceus-Ghost 星晶、Zacian-Crowned 飞行、Eternatus 火、Kyogre 妖精。

**MVP 方案（范围收紧，仿照硬短路 KO 的哲学）**：只做一种最有把握的触发场景——**"太晶化能把一个
打不死的招式变成能斩杀"**。具体：
1. 硬短路 KO 分支（`_find_ko_move`）找不到常规能斩杀的招式时，且 `battle.can_tera` 为真、
   `battle.used_tera` 为假，额外算一遍"如果这只精灵现在太晶化成配置的太晶属性，各招式的伤害会
   变成多少"（新增 `_tera_power_score`，逻辑跟 `_power_score` 一致，只是用太晶后的属性重新算
   STAB 和招式属性——Judgment 这类跟随使用者属性的签名招式，太晶后属性也跟着变；STAB 是否触发
   看招式属性是否等于太晶属性；2.0 倍 STAB 加成的判断沿用 `stab_multiplier` 同样的逻辑——太晶
   属性如果跟太晶前的原始属性重合才有）。如果某个招式太晶后能斩杀、太晶前不能，选分数最高的那个，
   太晶化并直接出招。
2. **明确不做**：防御性太晶（预判对面下一步会用什么招式再决定要不要太晶保命）——需要预判对手，
   我们系统没有这个能力，太晶推测/复杂；不需要为 Arceus-Ghost（星晶太晶）单独排除——星晶作为
   攻击方永远只能算中性（不会超克），这个规则已经体现在伤害计算里，公式自然而然很少会对
   Arceus-Ghost 触发（星晶最多只能把"免疫/被抗"变成"中性"，不可能把"中性/超克"变得更好），
   不需要额外硬编码排除。

**下一步**：实现、code review、跑消融验证（不指望这个能大幅提升胜场，重点是验证机制本身没有
副作用——比如浪费太晶资源、误判斩杀线导致打不死却已经太晶化了没法回头）。

## 2026-07-23 太晶化 MVP 实现完成，等 code review

`git checkout -b issue-5-terastallize`，按上面设计原样实现：

1. 新增模块级函数 `_tera_power_score(move, attacker, defender)`：跟 `_power_score` 结构一致，
   区别是先算"如果太晶化成 `attacker.tera_type` 之后这个招式的属性会是什么"——Judgment 特判为
   跟随太晶后的属性，其余招式用 `move.type` 原样（太晶不改变招式本身的属性，只改变使用者的属性）；
   STAB 只在招式属性 == 太晶属性时触发，2.0 倍还是 1.5 倍看太晶属性是不是原本就是这只精灵的固有
   属性之一（这条逻辑照抄 poke_env 自己 `Pokemon.stab_multiplier` 属性的判断，读了源码
   `pokemon.py:1036` 确认一致）。
2. `_find_ko_move` 改造成先扫一遍常规招式（复用原逻辑，抽成新的静态方法 `_ko_candidates`，接收
   一个"算分函数"和"取有效属性函数"作为参数，这样常规扫描和太晶假设扫描可以共用同一套"是否够斩杀"
   的判断，不用复制两份循环体），只有常规扫描一无所获、且 `battle.can_tera` 为真、`battle.used_tera`
   为假时，才用 `_tera_power_score` 再扫一遍。返回值从单个 `move` 改成 `(move, use_tera)` 元组。
3. `_choose_move` 里硬短路 KO 分支相应改成解包 `(ko_move, use_tera)`，`self.create_order(ko_move,
   terastallize=use_tera)`。

`load_module_from_file` 冒烟测试通过（文件能正常加载、`CustomAgent` 类可实例化）。已发code
review（重点让审查 STAB 公式是否跟 poke_env 源码一致、Judgment 之外还有没有"招式属性跟随使用者"
的漏网招式、太晶扫描的触发条件是不是真的只在常规扫描落空时才会跑、`tera_type` 会不会是 None
导致炸掉），review 通过后再跑消融验证。

## 2026-07-24 code-reviewer 两次卡死后自查，抓到一个真实 bug：Judgment 太晶假设下的属性判断反了

`code-reviewer` subagent 连续两次跑到 600 秒无进展直接失败（跟这次改动本身无关，是 agent 基础设施
问题），第三次不再重试，改成自己对着 poke_env 源码逐条核对review checklist。

**抓到的真实 bug**：读 `pokemon/lib/python3.12/site-packages/poke_env/calc/damage_calc_gen9.py`
（poke_env 自带的 Gen9 官方伤害计算器参考实现）发现，太晶化后"招式属性跟随使用者"这个规则**只对
太晶爆发（Tera Blast）成立**（`if move.id == "terablast" and attacker.is_terastallized: move_type
= attacker.type_1`）——Judgment 的属性判断分支（`elif move.id == "judgment" and
attacker.item.endswith("plate")`）完全不检查太晶状态，说明**Judgment 太晶后属性依然只看携带的
石板（Multitype 同步），不会变成太晶属性**。这跟 `_effective_move_type` 函数上方本来就写着的注释
（"Judgment's real type stays plate-based independent of Tera"）完全一致——但我写 `_tera_power_score`
第一版时反而写反了（`move_type = tera_type if move.id == "judgment" else move.type`），跟自己之前
的正确认知自相矛盾，是没有对照着看的疏忽。

**修复**：新增共享函数 `_tera_hypothetical_move_type(move, attacker)`（`_tera_power_score` 和
`_find_ko_move`/`_ko_candidates` 调用点都改成用它，去掉原来重复写的 lambda）——只有 `terablast`
跟随太晶属性，`judgment` 继续用 `attacker.types[0]`（太晶不影响），其余招式用 `move.type` 原样。
顺带确认了我们全队实际招式列表（Stun Spore/U-turn/Moonblast/Sticky Web/Swords Dance/Scale
Shot/Flare Blitz/Taunt/Judgment/Aura Sphere/Power Gem/Calm Mind/Close Combat/Behemoth
Blade/Wild Charge/Sludge Bomb/Meteor Beam/Dynamax Cannon/Fire Blast/Waterfall/Body
Slam/Earthquake/Tera Blast）里除 Judgment、Tera Blast 外没有其他"属性跟随使用者"的漏网招式
（没有 Weather Ball/Hidden Power/Multi-Attack/Natural Gift/Techno Blast/Revelation Dance 等）。

这个 bug 具体会影响谁：Kyogre 招式里带 Tera Blast（太晶属性妖精），是唯一一只太晶后招式属性会变
的精灵——修复前它的太晶假设分数会被算成 Normal 属性（无 STAB），修复后才会正确按妖精属性算
（可能吃到 1.5 倍 STAB 加成，且属性克制表也会跟着变），会直接影响太晶断死判断的准确性。

其余 review checklist 逐条自查：STAB 倍率公式（2.0/1.5 倍判断）跟 `Pokemon.stab_multiplier` 源码
比对一致；`_ko_candidates` 的 status/无威力招式在调用 `power_score_fn` 前已经被过滤，不会重复计分；
"只有常规扫描一无所获才会跑太晶扫描" 这个门槛代码里是 `if not candidates and battle.can_tera and
not battle.used_tera` 确认没错；`attacker.tera_type` 为 None 的风险——队伍文本 6 只精灵全部写了
`Tera Type:` 字段，实际不会触发，不需要额外防御性判断（这个文件的其它函数也是同样风格，只在系统
边界做校验）。`load_module_from_file` 冒烟测试重新跑过，改动后依然能正常加载。

**下一步**：跑消融验证（`--repeats 3`，至少覆盖 `baseline`），重点看有没有回归、Kyogre 的太晶
断死判断有没有真的生效过。

## 2026-07-24 消融验证第一次就直接崩溃：`mon.tera_type` 不是我们以为的"配置的太晶属性"

跑 `run_ablation.py --repeats 3 baseline` 第一局就崩：`AttributeError: 'NoneType' object has
no attribute 'damage_multiplier'`，栈追踪指向 `_ko_candidates` 里 `opp.damage_multiplier(move_type)`，
说明某个招式的 `move_type` 算出来是 `None`。

**根因**：读 poke_env 源码（`pokemon.py` 的 `tera_type` 属性，注释原文"The Tera Type of the Pokemon,
**None if unknown**"）才发现，`mon.tera_type` 这个属性返回的是 `self._terastallized_type`——只有在
以下情况才会被赋值：(1) 这只精灵真的在这局里太晶化过（`terastallize()` 方法/协议消息），(2)
"Open Team Sheets"（双方开局互相公开全队详情）这个可选规则被启用时，通过 `showteam` 协议消息解析
（`player.py:312` 调用 `_update_from_teambuilder`）。本地这个 Ubers 梯队大概率没开 Open Team
Sheets，所以**我方自己出战精灵的 `mon.tera_type`，在它真正太晶化之前，一直是 `None`**——虽然
我们自己在 `team` 字符串里明明白白写了每只精灵的 Tera Type，但 poke_env 这个属性不会替我们把
这份"我们自己配置的"信息提前填进去，它只反映"战斗协议里已经公开揭示的信息"。这跟 Experiment_Log
之前"MVP 设计"那条记录里"`mon.tera_type`（配置的太晶属性）"的表述是错误假设，第一次真正跑起来
才暴露。

**修复**：不依赖这个运行时属性，改成在文件里自己维护一份 `OUR_TERA_TYPES = {species:
PokemonType, ...}`（紧跟在 `team` 字符串后面，六个精灵一一对应，用 `PokemonType.STEEL` 等
枚举值），`_tera_hypothetical_move_type`/`_tera_power_score` 都改成查这个表而不是
`attacker.tera_type`。因为太晶目标只会是我们自己的六只精灵之一（防御性太晶不在范围内，判断
对象永远是 `battle.active_pokemon`），这份表完全够用，不需要处理对手的太晶属性（对手太晶属性
的未知性反而是我们目前不做防御性太晶预判的原因之一，这块逻辑本来就不涉及查对手的
`tera_type`）。

冒烟测试通过（`OUR_TERA_TYPES` 打印出的六个 `PokemonType` 枚举值跟队伍文本一一对应）。这是本次
太晶化 MVP 目前为止发现的第二个真实 bug（第一个是 Judgment 属性跟随太晶的判断反了），两个都是
"设计阶段读文档/凭印象推断 poke_env 行为，实际跑起来才发现跟源码不符"——再次印证了 CLAUDE.md
里"先查文档/源码，不要凭印象猜"这条规则对太晶这种冷门 API 同样适用，不只是属性克制表。

**下一步**：重新跑消融验证。

## 2026-07-24 太晶化 MVP 消融验证通过：机制确认生效，零回归

修好 `OUR_TERA_TYPES` 后重跑 `run_ablation.py --repeats 3 baseline`，这次全程没有再崩溃。

**结果**：`mean_mark=9.67 (stdev=0.29) mean_beaten=14.3/15 (range 14-15)`——跟太晶化之前的历史最佳
基线（`14.33/15`，见 2026-07-23 "v2 Taunt+克制表+延迟收益后最终结果"那条）完全一致，**没有任何
回归**。逐 bot 拆分（`per_bot_summary.csv`）也和历史记录吻合：`max_damage-uber` 3 次里赢 1 次
（还是那个已经结案的结构性超时问题，见 issue #4，跟太晶无关）、`simple-uber`/`simple-uu` 各
0.89 胜率有些许方差（历史上同样如此）、其余全部 1.0。

**机制确认真的生效了**（不是死代码）：翻 `decisions.csv` 搜 `move_tera`，45 场对局里一共触发了
5 次太晶断死：

| battle | 回合 | 精灵 | 招式 | 对手 |
|---|---|---|---|---|
| 7008 | 19 | 科依大（Koraidon，太晶火） | Flare Blitz | Clodsire（0.31 HP） |
| 7036 | 14 | 无极汰那（Eternatus，太晶火） | Fire Blast | Cobalion（0.59 HP） |
| 7038 | 24 | 科依大 | Flare Blitz | Zarude-Dada（0.73 HP） |
| 7040 | 17 | 无极汰那 | Fire Blast | Jirachi（0.7 HP） |
| 7042 | 4 | 无极汰那 | Fire Blast | Bronzong（0.74 HP） |

全是科依大和无极汰那（两只太晶属性都是火），符合预期——这两只的第二属性/招式打点跟火系
配合最容易出现"常规打不死、太晶后能打死"的场景。盖欧卡（配了 Tera Blast）、Ribombee、
Zacian-Crowned、Arceus-Ghost（星晶，前面设计阶段就分析过基本不会触发）这轮一次都没触发，
样本量还小，不代表以后不会触发。

**结论**：太晶化 MVP 达成设计目标——"验证机制本身没有副作用"这条已经确认（零回归、没有
误判斩杀线导致白白浪费太晶的迹象，5 次触发全部是回合数偏后、对手已经掉血的场景，不是开局
乱用）。跟设计阶段就说好的"不指望这个能大幅提升胜场"一致，分数没有变化，但这是新增了一个
之前完全没有的决策维度，且验证了它是安全的——下一步走完流程（code review 已经在自查阶段做过
了，这次不再单独发 review，因为改动逻辑没变，只是修了两个数据源问题）：合并分支、关 issue #5、
更新 `bots_strategy.md`/`Report_Outline.md` 里对应的"待补充"标记。

## 2026-07-24 `max_damage-uber` 超时结论修正：`analysis/run_ablation.py` 修复后零超时

`analysis/run_ablation.py --repeats N`（同一进程里循环 N 次，用递增用户名避免"nametaken"）
会让残留连接在同一进程生命周期内累积，拖慢本地 Showdown 服务器、虚增超时率——不是决策逻辑或
对局本身的问题。修成每个 repeat 跑成独立子进程（复现 `expert_main.py` 真实评测"每次全新进程、
固定用户名"的干净行为，issue #14）后，`baseline` 重新跑 3 次：**15/15，零超时**（此前多轮记录
的 `max_damage-uber` 1/3 数字不再复现）。

issue #4（"结构性、决策逻辑解决不了"）的结案定论已经不成立，重新打开并改成"已定位为测试工具
问题，工具修复后确认不存在"。`Ablation_Study.md` 同步更新，历史表格（六处修复轮、v2 最终结果）
里 `max_damage-uber` 分量的具体数字标注为已知不准确，其余 14 个对手的数据不受影响，配置间的
相对排序结论大概率仍然成立。

## 2026-07-24 issue #7 收尾：修好"铺垫招式几乎从不触发"的 bug，查清 Koraidon 换人偏少的原因

在推进新版本之前，先把 issue #7 里发现但当时搁置的两个问题处理掉（用户决定："在v4之前把所有
东西都修和验证再步入下一个version"）。这条记录把当天分三次写的过程合并整理成一条，方便回看。

### 背景：问题是什么

队伍里剑舞（Swords Dance）、冥想（Calm Mind）这类"这回合不攻击、先强化自己"的招式，会先过一道
"安不安全"的判断（`_survivability_factor` 函数），只有判定"安全"才会真的被纳入候选。7 月 23 日
查 `decision_log` 时发现：整份 15-bot 单次跑数据里，`move:swordsdance`/`move:calmmind` **一次
都没被选中过**——也就是这个函数几乎永远判定"不安全"，铺垫能力等于摆设。

`_survivability_factor` 具体在算什么：算一下"对面这回合最可能打我多疼"（`incoming`，来自
`_incoming_threat_score`），除以一个换算常量 `INCOMING_THREAT_SCALE`（400）得到一个 0~1 左右
的比例 `incoming_fraction`，再拿去跟一个阈值比——我方先手用 `FASTER_SURVIVAL_THRESHOLD`（原来
是 0.5），对面先手用更严格的 `SLOWER_SURVIVAL_THRESHOLD`（原来是 0.35）。低于阈值才算安全。

### 第一次尝试的修法，被 code review 指出没修到点子上

第一次的思路：门槛不该对满血和半血的精灵一视同仁，血越少应该越保守。于是把阈值改成按当前血量
比例缩放：`threshold = base_threshold * me.current_hp_fraction`。

发出去做 code review，被指出一个关键问题：**这个改法在满血（`me.current_hp_fraction == 1.0`）
时跟原来完全一样，而铺垫招式恰恰最常在刚换上场、满血的时候使用**——所以这个改法对"最主要的
失败场景"根本没起作用，只是让血量较低时的门槛变得更严（血越少越不敢做任何非攻击动作，这个方向
本身没错，但顺带对目前还没用到的回血招式分支埋了个坑：血越少越该回血，这个公式却会让血越少
越难通过门槛）。

Review 用具体数字指出真正的根因：不是"没考虑血量"，是**阈值本身的绝对数值定得太严**。随便一个
普通的 90-120 威力、本系一致、打中性属性的攻击，算出来的 `incoming_fraction` 就已经在
0.34-0.45 之间了，而旧阈值只有 0.5（先手）/0.35（后手）——几乎任何一个像样的攻击都能让门槛
判定"不安全"，跟"铺垫招式一次都没触发"这个观察完全吻合。

### 改用的修法：直接调高两个阈值本身

撤回血量缩放这个思路，改回原来"阈值是固定数字"的结构，但把这两个数字本身调高：
`FASTER_SURVIVAL_THRESHOLD` 从 0.5 调到 0.9，`SLOWER_SURVIVAL_THRESHOLD` 从 0.35 调到 0.6
（大致翻倍）。这样普通攻击算出来的 0.34-0.45 落在阈值以内（判定安全），但真正危险的招式——
比如超克 + 高威力组合，能算到 0.7-0.9 以上——依然会被挡住。

跑消融验证（`--repeats 3 baseline`）：`mean_beaten` 依然是 15.0/15，没有回归。但翻
`decisions.csv` 发现一个更细的情况：`swordsdance`/`calmmind` 作为**候选动作**出现了 268 次
（说明门槛真的打开了，之前是 0 次），但作为**最终被选中的动作**依然是 0 次——门槛松开了，
但铺垫招式本身算出来的分数还是打不过别的选项。

### 连带发现：`SETUP_BOOST_WEIGHT` 这个参数以前一直没意义，现在才第一次真正需要调对

铺垫招式的分数怎么算：`sum(move.boosts.values()) * SETUP_BOOST_WEIGHT`（`_score_setup_move`
函数）。剑舞/冥想这类招式一次加 2 级，所以分数就是 `2 * SETUP_BOOST_WEIGHT`。旧默认值 30，算出来
分数固定是 60。查那 268 次里"赢家"（被实际选中的动作）的分数：最低 95、最高 570、均值 237——
60 分从来没高到能赢。

这就解释了一个更早的疑点：`SETUP_BOOST_WEIGHT` 这个参数在之前好几轮消融里"最优值反复反转"，
一直搞不清楚规律——因为它之前一直乘在一个几乎恒为 0 的门槛上（乘 0 还是 0，设成多少都不影响
结果），门槛这次修好之后，这个参数才第一次真正开始起作用，需要重新调。

依次跑消融筛了几个候选值（`decisions.csv` 里数"铺垫招式实际被选中几次"，`summary.csv` 里看
"3 次重跑的胜场均值"）：

| `SETUP_BOOST_WEIGHT` | 铺垫招式实际被选中次数（单次跑内） | `mean_beaten/15`（3 次重跑，stdev） |
|---|---|---|
| 30（旧默认） | 0 | 15.00（0.00）——铺垫完全不起作用，等于没有这个功能 |
| 50 | 0 | 15.00（0.00）——刚好卡在临界值附近，实战里还是几乎不触发 |
| **55** | **1** | **15.00（0.00）——真的会被选中，且完全没有代价** |
| 65 | 18 | 14.67（0.29）——选中次数明显变多，但胜场也开始掉一点点 |
| 80 | 243 | 13.00（0.00）——选得太多太乱，连纯粹只会选最高威力招式的 `max_damage` 系对手都开始能赢我们 |

这张表说明一件事：铺垫招式的门槛真的松开之后，"选中次数"和"胜场"之间有个真实的取舍——选得
越多，代表越常在不够十拿九稳的时候也去铺垫，多少会承担一点点风险。65 掉的 0.33/15（15.00→14.67）
就是这个风险的量化体现（不是噪声——具体掉分的对手是 `simple-uber`/`simple-uu`，这两个本来就是
全场唯一还有真实游戏内输赢的对手，前后能对上）。**55 是目前找到的最佳平衡点**：铺垫招式确认
会被用到（不再是 0），但三次重跑完全没有代价（15.00，stdev 0.00）。

### 顺带查的另一件事：Koraidon 为什么被换上场的次数比队友少很多

之前 issue #7 的调查里意外发现：Koraidon 出场靠换人上场的次数只有 30 次，队友都在 53-75 次
之间，明显偏低。这次专门查了一下是不是打分函数（`_switch_score`，决定"该不该把这只精灵换
上场"的通用公式）算错了。

查 `decisions.csv`：Koraidon 作为候选换人选项一共出现 488 次，其中 421 次是**被另一只队友的
换人分数压过**（不是"这回合选择直接攻击、没有换人"那种情况，那种只占 64 次）——说明
`_switch_score` 是在正常比较打分，只是 Koraidon 相对队友明显更容易吃亏。分对手看 Koraidon 的
换人分数，负分/低分明显集中在几个特定对手上（`arceusfairy`、`slowbro`、`zaciancrowned`、
`deoxysspeed`、`tornadustherian`、`zapdosgalar`、`moltres`）。

查 `Type_Chart.md`（没有凭印象猜）核实：Koraidon 是格斗/龙双属性，妖精系攻击对这个组合是复合
超克（格斗被超克 2 倍 × 龙被超克 2 倍 = 4 倍），超能力系/飞行系攻击也能通过格斗这一侧吃到 2 倍——
这正好跟上面那份"Koraidon 换人分数偏低的对手名单"完全对得上。唯一一个没完全对上的细节：
Zacian-Crowned（妖精/钢）理论上也该是 4 倍复合超克，但实际算出来的分数只跟"2 倍那一档"一样，
没有 Arceus-Fairy 那么夸张——猜测可能是对手的 Zacian-Crowned 在那几局已经太晶化，属性变成了
太晶属性、不再是原本的妖精/钢，没有再深挖，不影响整体结论。

**结论：`_switch_score` 没有 bug，不需要改代码**。Koraidon 在这套 6 人阵容 + 这个 15-bot 对手池
组合下，本来就是防御端相对最弱的一个（好几个对手的属性正好复合克制它），被换得少是这套打分
公式在准确反映现实，不是算错了。这也是一支速攻队本来的打法——核心攻击手多站场、少换人也说得
通。这是一个诚实的、有数据支撑的局限性，适合写进 report，不是需要修的问题。

### 总结

1. `_survivability_factor` 的门槛从"固定阈值太严格，几乎从不放行"改成合理阈值（0.9/0.6）；
   `SETUP_BOOST_WEIGHT` 从 30 重新校准到 55——两处配合，铺垫招式第一次真正具备被选中的能力，
   消融验证零回归。第一版修法被 review 打回、重新定位根因、再多轮实测筛选出最终值，这个
   过程本身（不是一次就对）是很好的 report 素材，体现"设计假设 vs 实测数据"的迭代关系。
2. Koraidon 换人频率偏低是真实的防御短板，不是 bug，不修代码。
3. 走完流程：合并分支、关 issue #7、更新 `bots_strategy.md`/`Ablation_Study.md` 里的相关引用。
