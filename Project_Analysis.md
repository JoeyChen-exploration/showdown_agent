# 项目解析：Pokemon Showdown Expert Agent（COMPSYS 726）

> 这是给人看的项目背景文档，不会被 Claude Code 自动加载。
> Claude Code 每个 session 自动读取的是精简版的操作规则，见 [CLAUDE.md](CLAUDE.md)。

## 这是什么

UoA COMPSYS 726 的课程作业：在 [Pokemon Showdown](https://pokemonshowdown.com/) 对战模拟器上，
实现一个 **专家系统**（expert system）智能体，用 Gen9 Ubers 规则的对战格式，
去打赢一系列难度递增的内置 bot。明确禁止使用机器学习方法——评分依据是
[expert system 的定义](https://en.wikipedia.org/wiki/Expert_system)，即基于规则/知识推理，
而不是学出来的模型。

## 代码结构

```
showdown_agent/scripts/
├── players/
│   └── rename.py          # 唯一允许编辑的文件；提交前改名为学号，如 hwil292.py
├── bots/                   # 评测用的内置对手，不可编辑
│   ├── random.py           # RandomPlayer 包装
│   ├── max_damage.py       # 无脑选伤害最高的招式
│   ├── simple.py           # poke_env 自带的 SimpleHeuristicsPlayer
│   └── teams/               # 5 档队伍强度：uber / ou / uu / ru / nu
├── expert_main.py          # 本地评测入口：python expert_main.py --upi <upi>
├── expert_competition.py   # 班级对战竞赛用的脚本
├── submission_sanity.py    # 提交前的沙箱自检（建虚拟环境、装依赖、试导入）
├── file_write_detection.py # AST 静态扫描，检测 upi.py 里有没有写盘代码
└── move_completed.py / pull_results.py  # 评测辅助脚本
```

`bots/` 里三种策略（random / max_damage / simple）× 5 种队伍强度（uber/ou/uu/ru/nu），
组合成 15 个固定难度的对手梯队，见 `expert_main.py` 里的 `BOT_STYLE_ORDER` / `BOT_TEAM_ORDER`。

## 要改的文件：`players/upi.py`

自动评分系统**只读取这一个文件**，其余文件一律不生效也不该动。硬性要求：

- 保留 `CustomAgent` 类名和 `_choose_move(self, battle)` 的函数签名（框架靠这两个东西初始化/调用智能体）。
- `choose_move` 本身不要改——它已经做好了 `active_pokemon`/`opponent_active_pokemon` 为空时兜底走
  随机移动的逻辑，真正要写的策略在 `_choose_move` 里。
- `teampreview` 决定出场顺序，目前模板固定返回 `"/team 1"`。
- 队伍字符串（`team = """..."""`）要用 [Showdown Teambuilder](https://play.pokemonshowdown.com/teambuilder)
  导出的 Gen9 Ubers 格式文本。

## 评分机制

**本地/课程组评测**（`expert_main.py` 的 `run_tournament`）：智能体依次挑战 15 个固定 bot，
每场用 `poke_env.cross_evaluate` 打 3 局取胜率，胜率 > 0.5 记为击败该 bot。根据击败的 bot 数量
排出名次（1~16），再按名次映射分数表（第 1 名 10.0%，往后递减到第 16 名 0.0%，见 README）。
单场超过 90 秒（`MATCH_TIMEOUT_SECONDS`）算超时判负；出现未捕获异常也会中断整个梯队评测并判负。

**班级竞赛**（额外加分，非主评分）：Swiss 轮次淘汰赛，最后 16 强打单败淘汰赛，第 1 名 5% 加分，
往后递减到 Top 16 各 1%。

## 提交前的两道红线

1. **禁止任何写盘代码**——`file_write_detection.py` 用 AST 扫描 `upi.py`，抓 `open(..., "w"/"a"/"x"/"+")`
   以及 `.write()`/`.to_csv()`/`.dump()` 等写入类调用，命中就可能直接判零分。调试用的日志/统计数据
   只能 print 到终端，不能写文件。
2. **`requirements.txt` 必须自动生成**（`pipreqs`），且不能有同一个包的多个版本号冲突，
   否则 `submission_sanity.py` 的沙箱安装会失败。

提交前跑一遍沙箱自检：

```bash
cd showdown_agent/scripts
python submission_sanity.py --agent-file players/<upi>.py --requirements-file players/requirements.txt
```

## 提交方式

不走 GitHub PR。最终交付是把 `<upi>.py` + `requirements.txt` 上传到课程组指定的 Google Drive 文件夹
（文件夹以 upi 命名），最后修改时间即视为提交时间，可反复更新到截止日期前。

这个仓库本身 fork 自课程组的 `UoA-CARES/showdown_agent`（只读参考模板），
origin 已切到自己的 GitHub 账号 `JoeyChen-exploration/showdown_agent`，仓库里的 git 历史
只是自己管理开发过程用的，跟真正的作业提交是两回事。

顺带一提：`.gitignore` 里把 `players/*` 整个忽略掉了，只保留 `rename.py` 这一个例外——也就是说
自己写的 `upi.py` 默认不会被 git 追踪、也不会被 push 到 fork 上，这是模板仓库本来的设计。
