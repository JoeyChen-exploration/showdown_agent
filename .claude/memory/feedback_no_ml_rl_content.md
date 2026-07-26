---
name: feedback-no-ml-rl-content
description: "在 report/文献/设计讨论里绝不能引入 Reinforcement Learning 或其他 ML 方法/文献——这门课的 Assignment 2 才是 RL，Assignment 1（本项目）明确要求纯规则专家系统"
metadata:
  type: feedback
---

**发生了什么**（2026-07-27）：给 Report_Draft.md 补 peer-reviewed 文献时，计划里放了一篇
Henderson et al. (2018) "Deep Reinforcement Learning that Matters"（AAAI），本意只是想借用它
"要多次重跑看方差"这个统计方法论论点。用户立刻指出："我们不能做 Reinforcement 的内容 那个是
Assignment 2 的 我们现在是 assignment 1 我们主要 focus expert system"——已经进入执行阶段（issue
已开、branch 已建）才被拦下，换成了 Mytkowicz et al. (2009) "Producing Wrong Data Without Doing
Anything Obviously Wrong!"（ASPLOS，系统评测方法论论文，不涉及 ML/RL，而且跟本项目 issue #14
的"消融工具偏差"故事匹配度更高）。

**Why**：这门课把 RL 和专家系统分成两次独立作业（Assignment 1 = 本项目，规则/知识库驱动，明确
禁止机器学习；Assignment 2 = RL）。就算只是"借用"RL 文献里的一个统计方法论论点、不是真的用 RL
方法，光是引用一篇标题带"Reinforcement Learning"的论文，也会让报告读起来像是在暗示这个项目用了
RL 相关思路，跟"这是一个纯规则专家系统"的核心定位（见 Report_Draft.md 顶部醒目提醒块）自相矛盾，
且直接踩了作业边界。

**How to apply**：以后任何时候要给这个项目（report 论证、文献引用、设计类比、术语选择）找外部
支撑材料，先过一遍"这篇/这个概念是不是 ML 或 RL 领域的"——是的话即使论点本身适用也要换成非
ML/RL 的等价来源（经典 AI 教材如 AIMA、系统评测方法论、专家系统原始文献等都是安全区）。这条
不是"这个项目不能用 ML 方法实现"那条已知红线（CLAUDE.md 已有）的重复，而是它的延伸：**连"引用
一篇 ML/RL 论文来支撑一个跟 ML/RL 无关的论点"也不行**，因为报告是要往读者脑子里种"这是纯规则
专家系统"这个印象，沾上 ML/RL 的字眼本身就是风险，不看论文实际讲的是不是 ML 方法。
