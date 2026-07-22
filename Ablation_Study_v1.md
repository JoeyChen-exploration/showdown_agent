# 消融实验记录：v1 决策系统（2026-07-21）

> 用 `analysis/run_ablation.py` 对 `players/wche652.py` v1 版本的几个关键常量/开关做的消融实验。
> 每组配置跑一次完整 15-bot 梯队（`n_challenges=3`），改一个参数、其余保持默认。原始数据在
> `analysis/results/<config>/`（`per_bot.csv`/`decisions.csv`/`events.csv`），这份文档是对结果的
> 解读和记录。

## 配置列表

| 配置名 | 改动 |
|---|---|
| `baseline` | 不改，v1 默认值 |
| `no_hard_ko` | 关闭硬短路 KO 规则（`ENABLE_HARD_KO=False`） |
| `no_opening_script` | 关闭 Ribombee 固定开局脚本（`ENABLE_RIBOMBEE_OPENING=False`） |
| `setup_weight_15` / `setup_weight_45` | 铺垫打分权重从默认 30 改成 15 / 45 |
| `switch_defense_weight_30` / `switch_defense_weight_90` | 换人评分的防御风险权重从默认 60 改成 30 / 90 |
| `switch_cost_0` / `switch_cost_50` | 换人成本从默认 25 改成 0 / 50 |

## 结果总表

| 配置 | 排名 | Mark | 胜场 | 输给了谁 |
|---|---|---|---|---|
| **baseline** | #2 | 9.5 | 14/15 | `simple-uu` |
| no_hard_ko | #3 | 9.0 | 13/15 | `simple-uu`、`max_damage-uber` |
| no_opening_script | #2 | 9.5 | 14/15 | `max_damage-uber` |
| setup_weight_15 | #3 | 9.0 | 13/15 | `simple-uu`、`max_damage-uber` |
| **setup_weight_45** | #4 | 8.5 | 12/15 | `simple-uu`、`simple-nu`、`max_damage-uber` |
| switch_defense_weight_30 | #2 | 9.5 | 14/15 | `max_damage-uber` |
| switch_defense_weight_90 | #2 | 9.5 | 14/15 | `max_damage-uber` |
| switch_cost_0 | #2 | 9.5 | 14/15 | `max_damage-uber` |
| switch_cost_50 | #3 | 9.0 | 13/15 | `simple-uu`、`max_damage-uber` |

## 读出来的信号

1. **硬短路 KO 规则有正贡献**：`no_hard_ko` 比 `baseline` 少赢一场（13/15 vs 14/15）。即使这条规则
   本身有已知瑕疵（不看招式威力，见 `1st_strategy.md` 待细化清单），关掉它整体表现仍然更差，
   说明"能斩杀就直接斩杀"这个短路判断本身方向是对的，瑕疵不影响它净贡献为正。
2. **铺垫打分权重像是有个"甜区"**：默认值 30 两侧（15 和 45）表现都更差，其中调高到 45 是全场
   最差的一组（12/15，多输了 `simple-nu`）。说明默认值不是拍脑袋碰巧对的，而是调得太激进
   （更频繁地铺垫）反而会在不该铺垫的时候浪费回合，这是个值得写进报告 Evaluation/Design 部分的
   具体量化证据。
3. **换人相关的两个参数在测试范围内不敏感**：`SWITCH_DEFENSE_WEIGHT`（30/60/90）和
   `SWITCH_COST=0`（vs 默认 25）跟 baseline 结果完全一样（都是 14/15，输给 `max_damage-uber`）。
   `SWITCH_COST=50` 才开始表现变差。说明当前胜率的瓶颈可能不在换人逻辑这个方向，继续往这个方向
   调权重边际收益可能有限。
4. **`simple-uu` 和 `max_damage-uber` 是两个"摇摆"对手**：9 组配置里反复在赢/输之间切换，
   是目前最不稳定的两个对手，值得优先复盘 `decision_log` 看具体输在哪个环节。
5. **`no_opening_script` 跟 `baseline` 战绩打平（都是 14/15），但输的对手不一样**（`baseline` 输
   `simple-uu`，`no_opening_script` 输 `max_damage-uber`）——这不能直接解读成"开局脚本没用"，
   更可能是**样本量太小**（每组配置只跑了一次 15-bot 梯队，每场只有 3 局）导致的噪声，
   跟 `Report_Outline.md` 里已经记过的"样本量偏薄"缺口是同一个问题。要真正判断开局脚本的贡献，
   需要同一配置多跑几轮取胜率区间，而不是单次结果直接比较。

## `max_damage-uber` 超时问题（规则内的真实约束，不是要绕开的东西）

**现象**：9 组配置里，8 组在 `max_damage-uber` 这场超时判负（`MATCH_TIMEOUT_SECONDS=90` 秒内 3 局
打不完），只有 `baseline` 这一组赢了。查 `baseline` 自己打这场的 `decision_log`，回合数跑到
39-42 回合——远超一般对局的 15-30 回合，说明这个对局（对面带 `Arceus-Fairy`，冥想+生命种子，
很难磨穿）本身容易演变成拖很久的拉锯战，天然贴近 90 秒墙钟的边缘，配置之间的微小差异就可能
决定是否卡进超时。

**处理方式（已确认）**：`MATCH_TIMEOUT_SECONDS` 是 `expert_main.py` 里的评测规则常量，
正式评分用的就是这个 90 秒——**不在我们自己的分析脚本里放宽它**，即使只是为了让本地消融数据
更"干净"也不改，因为那样测出来的表现不代表真实评测环境下会发生什么。90 秒当成硬约束、
当成需要在策略层面解决的问题：**如果 v2 迭代要处理这个问题，方向应该是"让打法更果断、
避免陷入拉锯战"**（比如面对高耐久回血流对手时的专门判断），而不是想办法拖长时间限制。

## 这一轮的定位：筛选实验，不是最终调参结论

这 9 组配置每组只跑了一次，**目的是低成本筛出哪些变量真的敏感、值得投入更贵的多次重跑去精调**，
不是直接给出"最优参数值"。按这个目的分类：

- **敏感，值得优先精调**（对应 GitHub issue #8）：
  - `ENABLE_HARD_KO`——关掉少赢一场，有清楚信号。
  - `SETUP_BOOST_WEIGHT`——默认值 30 两侧（15、45）都更差，明显的"甜区"形状。
  - `SWITCH_COST`——50 掉一场，0 没变化，方向上有信号。
- **看起来不敏感，先不投入更多精调预算**：
  - `SWITCH_DEFENSE_WEIGHT`——30/60/90 结果完全一样。
- **信号被单次结果的噪声盖住，需要多次重跑才能判断，不能现在下结论**：
  - `ENABLE_RIBOMBEE_OPENING`——`no_opening_script` 跟 `baseline` 战绩打平（都 14/15），但输的
    对手不一样，说不清是真的没用还是运气。

## 下一步

1. 复盘 `simple-uu`（贯穿多组配置的摇摆对手）和 `max_damage-uber`（超时问题）这两场的
   `decision_log`，具体定位输/超时的回合和原因。（GitHub issue #6）
2. 消融实验补充多次重跑机制（GitHub issue #2），优先用在上面筛出来的敏感变量上
   （`ENABLE_HARD_KO`/`SETUP_BOOST_WEIGHT`/`SWITCH_COST`），以及信号不明确的 `ENABLE_RIBOMBEE_OPENING`。
3. v2 迭代时把"如何更快结束拉锯战"作为一个专门的设计目标，直接回应这次发现的超时问题。
   （GitHub issue #4）
