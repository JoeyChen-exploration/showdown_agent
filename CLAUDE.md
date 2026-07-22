# 项目上下文

> 这是每个 Claude Code session 自动加载的常驻上下文。项目特有的经验教训不要堆在这里——
> 那些放进 `.claude/memory/` 目录下的独立文件，会由 SessionStart hook 自动注入。
> 这个文件只放"几乎每次都要用到"的短小规则。
> 跨项目通用的偏好已在 `~/.claude/CLAUDE.md`（全局层），这里不用重复。

## 项目背景

COMPSYS 726 课程作业：为 Pokemon Showdown（Gen9 Ubers 格式）实现一个专家系统智能体，
对战内置的分级 bot 梯队拿分。禁止使用机器学习——必须是基于规则/知识的专家系统。
完整背景、评分机制、提交流程见 [Project_Analysis.md](Project_Analysis.md)。

## 技术栈

- 框架：Python 3.12 + [poke_env](https://github.com/hsahovic/poke_env)（对战框架，封装 Pokemon Showdown 协议）
- 对战服务器：本地跑 [pokemon-showdown](https://github.com/smogon/pokemon-showdown)（Node.js），`node pokemon-showdown start --no-security`
- 数据库：无
- 部署平台：无——最终产物是提交到 Google Drive 由课程组离线评测，不是部署上线
- 包管理器：pip（推荐配合 pyenv/venv）

## 项目结构约定

- **只允许改 `showdown_agent/scripts/players/upi.py`**（提交前从 `rename.py` 改名为学号，如 `hwil292.py`）。
  自动评分系统只读取这一个文件，改动其他文件不会生效、也不该改。
- `CustomAgent` 类名、`_choose_move(self, battle)` 的函数签名不能改——评测框架依赖它们初始化和调用。
  可以自由扩展 `CustomAgent` 的其他方法/属性。
- `showdown_agent/scripts/` 下除 `players/` 以外的文件（`expert_main.py`、`bots/`、`submission_sanity.py` 等）
  是评测框架代码，不属于我们要修改的范围。
- 队伍字符串必须是 Gen9 Ubers 格式（[Showdown Teambuilder](https://play.pokemonshowdown.com/teambuilder) 导出）。
- `analysis/`（仓库根目录，2026-07-21 新增）是我们自己的消融实验/复盘工具，**不属于提交范围**
  （只有 `players/<upi>.py` 会被评测系统读取），可以自由读写磁盘、修改。`analysis/run_ablation.py`
  会热加载 `wche652.py`、按配置覆写它顶层的可调常量（`ENABLE_HARD_KO`/`SWITCH_COST` 等），
  跑完整个 15-bot 梯队后把结果、`decision_log`、`battle.observations` 落盘到 `analysis/results/`。

## 编码规范

- **提交前不能有任何写盘代码**——`open(..., "w")`、`.write()`、`.to_csv()` 等一律不行，
  会被 `file_write_detection.py` 静态扫描出来，可能导致零分。终端 print/logging 没问题。
  `file_write_detection.py` 只扫 `--agent-file` 指定的那一个文件（也就是 `players/wche652.py`），
  不扫仓库其他文件——所以 `wche652.py` 里 `self.decision_log`（纯内存 list，append 不算写盘）
  是安全的，真正的落盘操作放在 `analysis/` 下不受限制的分析脚本里做。
- `requirements.txt` 用 `pipreqs` 生成（不要手写），且同一个包不能出现两个不同版本号，
  否则 `submission_sanity.py` 会挡下来。

## 工作流约定

- 本地评测：`python expert_main.py --upi <upi>`（在 `showdown_agent/scripts/` 目录下跑，
  Pokemon Showdown 本地服务器要先起着）。
- **每跑完一轮"改队伍/改策略 → 评测"，把过程和结果记进 [Experiment_Log.md](Experiment_Log.md)**——
  改了什么、为什么改、跑出来的排名/分数/各 bot 胜率、观察到什么规律、下一步打算怎么改。
  这是为了期末 report 能直接从这里整理实验过程，不用最后回忆——不用用户提醒，每轮实验自动记录。
- `_choose_move` 的策略设计（决策架构、打分公式、各精灵的战术角色）记在 [1st_strategy.md](1st_strategy.md)，
  是持续讨论/迭代的设计文档，跟 `Experiment_Log.md`（记跑分结果）分工不同——设计聊完/改了同样自动更新。
- Report（占分 40%，见 [AssessmentDescription.md](AssessmentDescription.md)）要求 Design/Evaluation/
  Reflections 三部分，[Report_Outline.md](Report_Outline.md) 把已有的 log 按这三部分分类、标出缺口——
  以后每次更新 `Experiment_Log.md`/`1st_strategy.md`，顺手看一下 `Report_Outline.md` 里的素材缺口
  有没有被这次更新填上，同步勾掉/更新。报告本体（英文）在 [Report_Draft.md](Report_Draft.md)，
  是正在写的草稿，不是最终排版格式。
- **待办任务清单在 GitHub Issues**（`JoeyChen-exploration/showdown_agent` 仓库，2026-07-21 开始用），
  不在某份 md 文件里——每次开始干活前先看一眼 open issues 有哪些，做完了记得关掉；新的可执行任务
  （不是纯讨论/记录）也开成 issue，不要只写进某份文档的"待办"列表里就算了。
- 提交前必须跑一次沙箱自检：`python submission_sanity.py --agent-file players/<upi>.py --requirements-file players/requirements.txt`。
- 真正的"提交"是把 `<upi>.py` + `requirements.txt` 传到指定 Google Drive 文件夹——**不是 GitHub PR**。
  这个仓库的 git 历史只是我们自己管理开发过程用的，origin 是自己 fork 的
  `JoeyChen-exploration/showdown_agent`（上游是课程组的 `UoA-CARES/showdown_agent`，只读参考，不推送）。
- 每次完成更新/改动之后，自动 view 项目中所有相关文件，检查是否有需要同步的地方并一并更新
  （包括本文件、`.claude/memory/`），保持文档与代码一致——无需用户提醒，自动执行。

## 已知的技术债 / 故意延后的事项

- `teampreview` 目前固定返回 `/team 1`（先手队伍顺序策略延后）。
- 严禁引入任何机器学习方法（作业硬性规则，不是技术债，不要"顺手"加）。
