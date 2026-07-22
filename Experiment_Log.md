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
6. （Suggestion，未处理）`CONFIGS` 没有覆盖 `KO_EFFECTIVE_HP_THRESHOLD`/`KO_NEUTRAL_HP_THRESHOLD`
   这两个阈值的消融——如果 report 要讨论 KO 阈值校准（呼应第 1 条），目前没有对应数据。
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

**结果**：7 组配置（`baseline`/`no_hard_ko`/`no_opening_script`/`setup_weight_15`/`setup_weight_45`/
`switch_cost_0`/`switch_cost_50`）× 3 次重跑，后台跑，还没跑完。

**下一步**：跑完之后更新 `Ablation_Study_v1.md`（或者按 issue #1 的文档整理计划，改名成
`Ablation_Study.md` 之后在里面加新章节），把均值/标准差数据换算成"哪个参数值真的更好"的结论，
喂给 issue #8（打分公式权重的系统性校准）。
