# c · 渐进发现（Progressive Discovery，占位）

> 专栏第 **02-04** 讲 · 模式 · 感知行 × 循环列
>
> [English README](README.md)

## 状态

占位。代码和可跑 demo 会跟 02-04 讲一起发布。

## 预告

渐进发现就是 agentic search 模式。给 agent 一个它从没见过的代码仓库，怎么从
一无所知到"我知道 bug 在哪个文件"，而不预先把全 repo embedding？三个阶段：
广扫（grep 找 ~30 个候选）、精读（打开 ~5 个）、追链（依赖、测试、调用方）。
一个完整的 forage-focus-deepen 周期，在典型的 2000 文件仓库上代价约 18K token。

更多见 02-04 讲发布后，或者参考
[Boris Cherny 在 X 上那段为何 Claude Code 弃用 RAG 改走 agentic search 的说明](https://x.com/bcherny/status/2017824286489383315)。
