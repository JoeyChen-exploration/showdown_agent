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

**目标 / 假设**：把 `_choose_move` 从随机换成 `1st_strategy.md` 里设计好的 v1 规则系统，验证是否能把
`max_damage`/`random` 档的胜率从"看运气"变成"稳定拿下"，并看看 `simple` 档能不能开始破防。

**改动**：
- 队伍：不变（Ribombee/Koraidon/Arceus-Ghost/Zacian-Crowned/Eternatus/Kyogre），Ribombee 道具确认保持
  `Focus Sash`（中途写代码时手滑改成过 Heavy-Duty Boots，复查时改了回来，用户已经明确表示不换道具）。
- 代码（`players/wche652.py`）：
  - 硬短路规则：这回合有招式能斩杀对面就直接用（多个可斩杀选项里优先选没反作用力的）。
  - Ribombee 固定开局脚本：第 1 回合无脑放 Sticky Web；第 2 回合按"对面是草系→直接 U-turn / 否则查换人评分决定 U-turn 还是放 Stun Spore"。
  - 通用单回合价值打分：换人评分（进攻端 `_power_score` 最大值 - 防御端类型倍率 × 60），铺垫招式打分（强化幅度 × 速度感知的"扛不扛得住"存活系数），其余伤害招式按 `base_power × STAB × 属性倍率` 打分，所有合法动作统一比较取最高分。
  - 太晶（Tera）本版不触发，按 `1st_strategy.md` 里"明确延后到 v2"的决定。
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
2. 补 `1st_strategy.md` 里还没细化的部分：打分公式权重的进一步校准、Arceus-Ghost/Eternatus 的角色定位。
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
1. `_find_ko_move` 不看威力这个问题留到下一个 version 再改（已记进 `1st_strategy.md` 待细化清单）。
2. 重新跑全部 9 组消融配置（这次命名冲突和报错处理都修好了）。

---

## 2026-07-21 9 组消融实验跑完

**目标 / 假设**：修复命名冲突 bug 后重新跑全部 9 组消融配置（`baseline`/`no_hard_ko`/
`no_opening_script`/铺垫权重×2/换人防御权重×2/换人成本×2）。

**结果**：完整的配置列表、结果总表、逐条信号解读、`max_damage-uber` 超时问题的分析和处理方式，
单独写了一份文档：[Ablation_Study_v1.md](Ablation_Study_v1.md)（不在这里重复，避免两份文档打架）。

**观察 / 结论（摘要，完整版见上面链接）**：硬短路 KO 规则有正贡献；铺垫打分权重存在"甜区"
（默认值 30 两侧都更差，调高到 45 是全场最差的一组）；换人相关权重在测试范围内不敏感；
`simple-uu`/`max_damage-uber` 是贯穿多组配置的"摇摆"对手；`max_damage-uber` 这场经常打到
39-42 回合、逼近 90 秒超时墙——**跟用户确认过，不会为了让本地消融数据更干净就放宽这个超时常量**，
因为正式评测用的就是这个 90 秒，放宽了本地测的就不代表真实评测环境，这个问题要留到 v2 从"让打法
更果断、避免拖成拉锯战"这个方向解决。

**下一步**：见 `Ablation_Study_v1.md` 的"下一步"部分（复盘 `simple-uu`/`max_damage-uber` 的
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
解读、更新后的敏感度分类，写进了 `Ablation_Study_v1.md` 新增的"2026-07-22 多次重跑确认结果"一节
（不在这里重复）。

**观察 / 结论（摘要，完整版见 `Ablation_Study_v1.md`）**：
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
`Ablation_Study_v1.md` 和 `Report_Draft.md` 3.2-3.4 节现在描述的已经不是当前这版智能体的真实行为。
跟用户确认过，方向是**重新跑一遍完整消融**（7 组配置 × 3 次重跑）拿到基于修复后代码的准确数据，
再重写这几份文档——这个也是很好的报告素材，"从真实对局日志定位到一个方向搞反的核心 bug、修复、
量化改进"这条线，比单纯调参数的消融实验更能体现专家系统"观察 → 推理 →改进"的方法论。

**下一步**：
1. 后台重新跑 7 组配置 × 3 次重跑消融（用修复后的代码）。
2. 跑完后重写 `Ablation_Study_v1.md` 的多次重跑章节和 `Report_Draft.md` 3.2-3.4 节，数据和结论
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
1. 用这份新数据重写 `Ablation_Study_v1.md`、`Report_Draft.md` 3.2-3.4 节（撤掉待更新标记），
   `Report_Outline.md` 同步。
2. `SWITCH_DEFENSE_WEIGHT`（30/60/90，之前判定"不敏感"）建立在同一个错误公式上，之前的"不敏感"
   结论也不可信，值得找机会重新测一次（issue #8）。
3. `baseline` 标准差变大这件事先记下来，等以后有机会再跑更多次重跑确认是不是真实效应。

---

## 2026-07-23 v1 遗留的另外两个已知 bug 一起修：对手速度估算、KO 判断威力盲区

**目标 / 假设**：`_switch_score` 那个方向反的 bug 修完之后，用户提出"既然发现了一个 bug，就把 v1
现存的已知 bug 一次修完，严谨一点，再重新跑一遍消融"，不要修一个跑一次、来回折腾。盘点 1st_strategy.md
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
修一个跑一次），跑完更新 `Ablation_Study_v1.md`/`Report_Draft.md`。

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
3. 用 `SETUP_BOOST_WEIGHT=15` 更新 `Ablation_Study_v1.md`/`Report_Draft.md` 3.3 节当前有效数据。

---

## 2026-07-23 `SWITCH_DEFENSE_WEIGHT` 重测（issue #8）

**结果**：`switch_defense_weight_30`/`switch_defense_weight_90` 各 3 次重跑，均 14.00/15——
跟 `baseline`（默认值 60，同样 14.00）打平，`90` 这组标准差是 0（比 baseline 自己的 0.50 还稳）。

**结论**：30/60/90 全部并列最高。旧的"不敏感"结论（筛选轮测的，那时 `_switch_score` 还有方向反了
的 bug）修复后重新验证依然成立，但原因变了——不是公式本身没有区分度，是换人打分修正之后这个权重
在这个范围内确实不太影响最终胜场。不再往这个参数上投入精调预算，`SWITCH_DEFENSE_WEIGHT` 维持
默认值 60。完整数据见 `Ablation_Study_v1.md`。

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
2. 用 `baseline`（当前默认参数）作为最终数据源重写 `Ablation_Study_v1.md`/`Report_Draft.md`
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
