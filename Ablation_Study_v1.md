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

## 下一步（筛选轮，历史记录，已被下面的多次重跑轮部分取代）

1. 复盘 `simple-uu`（贯穿多组配置的摇摆对手）和 `max_damage-uber`（超时问题）这两场的
   `decision_log`，具体定位输/超时的回合和原因。（GitHub issue #6）
2. 消融实验补充多次重跑机制（GitHub issue #2），优先用在上面筛出来的敏感变量上
   （`ENABLE_HARD_KO`/`SETUP_BOOST_WEIGHT`/`SWITCH_COST`），以及信号不明确的 `ENABLE_RIBOMBEE_OPENING`。
3. v2 迭代时把"如何更快结束拉锯战"作为一个专门的设计目标，直接回应这次发现的超时问题。
   （GitHub issue #4）

---

## 2026-07-22 多次重跑确认结果（GitHub issue #2，`--repeats 3`）

对筛选轮标记为"敏感"或"信号不明确"的 7 组配置（`baseline`/`no_hard_ko`/`no_opening_script`/
`setup_weight_15`/`setup_weight_45`/`switch_cost_0`/`switch_cost_50`）各重跑 3 次完整
15-bot 梯队，取均值/标准差。`switch_defense_weight_30/90`（筛选轮判定不敏感）没有重跑，
沿用筛选轮的单次数据。原始数据：`analysis/results/<config>/per_bot_summary.csv`（每个对手
的均值/标准差胜率）、`analysis/results/summary.csv`（每个配置的聚合结果）。

### 结果总表

| 配置 | mean_mark | stdev_mark | mean_beaten/15 | 胜场区间 |
|---|---|---|---|---|
| **baseline** | 9.17 | 0.29 | 13.33 | 13–14 |
| no_hard_ko | 9.00 | 0.00 | 13.00 | 13–13 |
| **no_opening_script** | **9.50** | **0.00** | **14.00** | 14–14 |
| **setup_weight_15** | **9.50** | **0.00** | **14.00** | 14–14 |
| setup_weight_45 | 8.83 | 0.29 | 12.67 | 12–13 |
| switch_cost_0 | 9.00 | 0.00 | 13.00 | 13–13 |
| switch_cost_50 | 9.33 | 0.29 | 13.67 | 13–14 |

### 读出来的信号（更新/取代筛选轮的对应结论）

1. **`max_damage-uber` 的输赢在这些参数上完全不敏感，筛选轮 baseline 那次"赢"是噪声**：
   `baseline` 单次跑出的 1/3 胜场（mean_winrate=0.33, **stdev=0.58**，3 次重跑里有明显分歧）是
   目前全表标准差最大的一格；而其余全部 6 组配置都是稳定的 **0/3**（stdev=0）。也就是说，筛选轮
   报告里"9 组配置 8 组输给 `max_damage-uber`、只有 baseline 赢"这个对比，看起来像 baseline
   有什么特殊优势，实际上更可能是 baseline 那一次单次跑（那时候还没有多次重跑机制）刚好卡在
   90 秒超时墙的有利一侧，纯属运气。**这进一步确认了 `Ablation_Study_v1.md` 前面"超时问题"一节
   的判断**：这场对局的胜负目前主要由是否卡进 90 秒超时决定，不由这 7 个参数决定，需要 issue #4
   那种"让打法更果断"的结构性改动才能真正改善，继续在这几个权重上找也没用。
2. **`ENABLE_RIBOMBEE_OPENING` 的信号被筛选轮的噪声掩盖了，多次重跑后是清楚的正向信号**：
   筛选轮判定"打平、说不清"，但重跑 3 次后 `no_opening_script` 稳定在 **14/15（stdev=0）**，
   比 `baseline` 的 13.33/15（stdev=0.29）高了一整场，而且区间不重叠（14–14 vs 13–14 有一点点
   重叠但均值方向一致、标准差趋近于 0）。机制上看是一次**换手交易**：关掉开局脚本后 `simple-uu`
   从稳定输（baseline: mean_winrate=0.33, 0/3）变成稳定赢（mean_winrate=1.00, 3/3），代价是
   `max_damage-uber` 从偶尔能赢（baseline 1/3）变成稳定输（0/3）——但上一条已经确认这场本来就
   是超时噪声决定的，不是真的因为开局脚本，所以这笔交易接近纯赚：多赢一场稳定的 `simple-uu`，
   没有真正牺牲什么。
3. **`SETUP_BOOST_WEIGHT` 的"甜区"形状被重跑确认了，但下边界比默认值 30 更好**：
   `setup_weight_15` 同样稳定在 14/15（stdev=0），机制跟 `no_opening_script`几乎一样——也是
   `simple-uu` 从稳定输变成稳定赢（mean_winrate=0.89, 3/3）。`setup_weight_45` 则被重跑坐实是
   全场最差（12.67/15），而且不只是重复筛选轮的"多输 `simple-nu`"，重跑后看到的是 `simple-uu`
   稳定输（跟 baseline 一样 mean_winrate=0.33）**外加** `max_damage-uu` 开始不稳定
   （mean_winrate=0.67, stdev=0.33, 2/3）——铺垫权重调太高不仅没有在原本就输的对手上翻盘，
   反而在原本稳赢的对手上引入了新的不确定性。
4. **`SWITCH_COST` 方向不再像筛选轮那样清楚，重跑后接近中性偏正**：`switch_cost_50` 均值
   13.67/15，比 baseline 的 13.33 略高，但标准差没降到 0（区间还是 13–14）——细看是因为
   `simple-uu` 变成稳定赢（跟前两条同一个模式，mean_winrate=0.67, 3/3）的同时，新引入了
   `simple-ou` 的不稳定（mean_winrate=0.78, **stdev=0.38，全表第二大**，2/3）。`switch_cost_0`
   跟 baseline 比是稳定变差（13/15, stdev=0，`simple-uu` 稳定输且 winrate 比 baseline 更低）。
   跟筛选轮"50 掉一场、0 没变化"的结论方向一致，但现在看两个方向都不是免费的：调高换人成本用
   `simple-ou` 的稳定性换 `simple-uu` 的稳定性，不是单纯的正向改动。
5. **一个值得跟进的观察：三种不同机制的改动（关闭开局脚本 / 调低铺垫权重 / 调高换人成本）都独立地
   把 `simple-uu` 从稳定输翻成稳定赢**，说明 baseline 输给 `simple-uu` 可能不是某一个单一原因，
   而是这几个参数在当前默认值组合下共同把某类招式选择推向了错误方向。三条路径改的是完全不同的
   决策环节（开局脚本走的是固定脚本分支，铺垫权重和换人成本都在 `_best_scored_action` 的打分
   公式里，但影响的是不同候选动作类别），却指向同一个对手结果，值得复盘 `simple-uu` 的
   `decision_log`（issue #6）具体看这几组配置在同一回合选了什么不同的动作，而不是只看聚合胜负。

### 更新后的分类（喂给 issue #8：打分公式权重的系统性校准）

- **确认敏感、且方向明确，值得当作 v2 默认值候选**：
  - `ENABLE_RIBOMBEE_OPENING=False`（关闭开局脚本）—— 14/15, stdev 0，目前样本里最干净的正向信号。
  - `SETUP_BOOST_WEIGHT=15`（下调，而不是维持默认 30）—— 同样 14/15, stdev 0。
  - 两者效果高度相似（同样的机制：`simple-uu` 翻盘），下一轮值得测试**两者叠加**是否有更大收益，
    还是彼此重叠（issue #8 的具体任务之一）。
- **确认敏感、方向明确是负向**：`SETUP_BOOST_WEIGHT=45`（上调）—— 12.67/15，全场最差，不用再测。
- **确认对这 7 个参数不敏感，需要结构性方案**：`max_damage-uber` 的超时输赢——不再往这几个权重
  上投入精力，转给 issue #4（更快结束拉锯战）。
- **方向不再清楚，需要更细的按对手拆分数据才能判断是否值得改**：`SWITCH_COST`——0 和 50 都各自
  在不同对手上有得有失，不是单纯"越大越好/越小越好"。

## 下一步

1. 复盘 `simple-uu` 的 `decision_log`，对比 `baseline`/`no_opening_script`/`setup_weight_15`/
   `switch_cost_50` 这几组在同一局面下的候选打分差异，搞清楚是不是同一个根因。（issue #6）
2. 测试 `no_opening_script` + `setup_weight_15` 叠加配置，确认是否比单独任一个更好、还是收益重叠。
   （issue #8）
3. `max_damage-uber` 的超时问题不再指望靠调这几个权重解决，转到 v2"更快结束拉锯战"的专门设计。
   （issue #4）
