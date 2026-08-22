# 轻量协作实验

这里是一组无密钥、可快速复现的协作模式教学入口。相邻模式目录中的完整实现继续负责生产接口与异常边界。

## 从克隆到打开工作台

工作台只使用 Python 标准库。第一次运行可以从克隆公开 Repo 开始：

```bash
git clone https://github.com/huangjia2019/agent-design-patterns.git
cd agent-design-patterns
python3 collaboration/light_labs/web_app.py
```

浏览器打开 `http://127.0.0.1:8098`。选择第 32 到 35 讲或 B1 加餐，点击“运行对照实验”，页面会真实调用对应的确定性 Lab，同时显示原始做法、加入模式后的结果和逐步检查轨迹。

如果只想运行命令行版本，可以继续使用下文各讲的独立命令。

## 技术简报委派实验

三位研究员共同准备一页多 Agent 框架简报。模糊委派会让三个人都查同一个方向。明确委派把简报拆成拓扑、状态和交接三个责任面。只有三个方向各出现一次，并且每张资料卡都带来源，父 Agent 才接收结果。

运行实验：

```bash
python3 collaboration/light_labs/editorial_delegation_lab.py
```

运行测试：

```bash
pytest -q collaboration/light_labs
```

`research()` 使用确定性资料卡，使两次结果稳定可复现。接入真实模型或 Agent 框架时，只替换这个执行接缝，保留委派契约和验收规则。

## DeepSeek Harness 接入

DeepSeek AI 在 2026 年 8 月发布了 DeepSeek Harness。当前官方定位仍是 Developer Preview，核心思路是“everything is a plugin”。它通过统一的 `ctx.subagents` 接缝连接 `spawn`、`fork`、ACP、Codex、Claude Code 和 dsh SDK 等子 Agent provider。

`dsh_editorial_delegation/` 把三个责任面绑定到独立的 dsh `spawn` 子 Agent，并增加确定性的 `brief_gate`。dsh 负责子会话、工具可见性和生命周期，组合覆盖和重复检查仍由业务闸负责。这个分工很重要：Harness 提供运行机制，协作模式定义业务上怎样才算交付合格。

准备好 DeepSeek Harness 源码环境后运行：

```bash
DSH_SOURCE=/path/to/deepseek-harness \
  bash collaboration/light_labs/dsh_editorial_delegation/run_web.sh
```

具体步骤与边界见 `dsh_editorial_delegation/README.zh-CN.md`。

## 其余三个协作模式实验

技术编辑部的故事会在三个小实验里继续：

```bash
python3 collaboration/light_labs/editorial_gather_lab.py
python3 collaboration/light_labs/editorial_review_lab.py
python3 collaboration/light_labs/editorial_handoff_lab.py
```

| 实验 | 稳定复现的故障 | 加入的工程契约 |
|---|---|---|
| 扇出聚合 | 扁平多数票抹掉工作区共享边界 | 类型化证据、覆盖、冲突与来源 |
| 对抗评审 | 两条阻断意见被记录，发布仍继续 | 结构化异议与版本绑定回执 |
| 交接链 | 核查结论在交接中丢失，旧说法被发布 | 不可变接力棒、阶段所有权与内容绑定 |

四个 Lab 都使用确定性夹具来解释协作契约，不把固定输出冒充真实模型评测。

## Harness 并发与业务聚合加餐

`runtime_business_gather_lab.py` 专门演示一条容易混淆的边界：Harness 可以并发启动 Worker、等待返回、记录超时和异常，薪酬系统仍要自己定义“这些结果能否形成可信结论”。

实验把两层接口分开：

| 层 | 实现 | 负责的问题 |
|---|---|---|
| 运行层 | `AsyncFanOutHarness` | 并发上限、超时、调用状态、墙钟时间 |
| 证据层 | `PayrollEvidenceGatherer` | 来源覆盖、周期和币种、血缘去重、人数与金额恒等式 |

运行全部五个场景：

```bash
python3 collaboration/light_labs/runtime_business_gather_lab.py
```

只看“三路调用全部成功，业务仍然拒绝”的场景：

```bash
python3 collaboration/light_labs/runtime_business_gather_lab.py --scenario unexplained-gap
```

五个场景分别覆盖健康对账、银行超时、重复血缘、单位错位和无法解释的金额差。替换 OpenAI Agents SDK、Anthropic Subagent 或 DeepSeek Harness 时，只替换 `EvidenceProvider.collect()` 的执行适配器，`EvidenceCard` 与业务聚合规则保持不变。

## 实验边界

这组实验检查责任覆盖、保留证据的聚合、评审控制效果、版本化交接，以及运行状态与业务结论的分账。它们不检查来源时效、事实准确性、模型质量或生产权限。DeepSeek Harness adapter 展示了真实子代理接缝，实际模型行为仍取决于凭证、provider、提示与网络条件。
