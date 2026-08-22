# 用 DeepSeek Harness 跑层级委派

这个 overlay 把无密钥的技术简报实验接到 DeepSeek Harness。三个专职子 Agent 分别研究拓扑、状态和交接，父 Agent 收齐资料卡后调用确定性的 `brief_gate` 做组合验收。

本例按 DeepSeek Harness 2026 年 8 月 13 日发布时的官方源码接口编写。该项目当前仍标注为 Developer Preview，后续版本可能发生兼容性变化。课程因此把业务契约留在本目录，把 dsh 接入收敛在 overlay 和启动脚本里。

它把职责分成两层：

- dsh 负责创建独立子会话、绑定 provider、限制委派深度并结算运行
- `brief_gate` 负责检查责任覆盖、重复方向和来源字段

## 先跑无密钥基线

从 `agent-design-patterns` 根目录运行：

```bash
python3 collaboration/light_labs/editorial_delegation_lab.py
```

基线会稳定复现两组结果：模糊委派只有 `coverage=1/3`，责任委派达到 `coverage=3/3`。

## 准备 DeepSeek Harness

按照 dsh 官方仓库的源码运行说明完成安装并配置模型凭证。然后从本目录启动 Web UI：

```bash
DSH_SOURCE=/path/to/deepseek-harness \
  bash collaboration/light_labs/dsh_editorial_delegation/run_web.sh
```

脚本会把 `brief_gate.ts` 临时放进 dsh 官方约定的 `scratch-plugin` 目录，再生成 overlay。退出后临时插件会被清理，公开文件里不写入本机路径或模型凭证。

打开 dsh Web UI 后，把 `prompt.zh-CN.md` 中的任务交给父 Agent。

## Overlay 加了什么

同一个 `spawn` provider 被绑定为三个不同的模型工具：

| 工具 | 责任面 | 运行约束 |
|---|---|---|
| `research_topology` | 协作拓扑与调度 | 前台等待，最大委派深度 1 |
| `research_state` | 上下文与状态隔离 | 前台等待，最大委派深度 1 |
| `research_handoff` | 跨 Agent 交接 | 前台等待，最大委派深度 1 |

每个子 Agent 都有独立 persona。`toolFilter` 会从子 Agent 可见工具中移除委派与组合验收工具，避免 Worker 自己继续组队或给自己的结果签发组合通过。

父 Agent 最后调用 `brief_gate`，输入三张卡：

```json
{
  "cards": [
    {
      "worker_id": "atlas",
      "lane": "topology",
      "claim": "...",
      "source_id": "...",
      "source_url": "https://..."
    }
  ]
}
```

只有 `topology`、`state`、`handoff` 各出现一次，并且每张卡都有结论与 HTTP(S) 来源时，闸门才返回 `accepted: true`。

## 为什么仍保留 Python Lab

真实模型输出受模型版本、凭证、网络与资料变化影响，不适合承担教学中的确定性断言。Python Lab 证明委派结构和验收规则，dsh overlay 展示真实子 Agent 的运行接缝。二者回答的问题不同，可以并行保留。

## 当前边界

- `brief_gate` 检查来源字段是否存在，不验证来源内容真假或时效。
- persona 约束输出语义，最终是否遵循仍取决于模型。闸门负责拒绝坏工件。
- `spawn` provider 支持底层 `outputSchema`，通用模型侧 `dsh-tool-subagent` 当前未把它暴露成实例配置。本例让子 Agent 返回 JSON，再由闸门验证。
- `toolFilter` 是 dsh 工具可见性和执行拒绝边界，不代替业务 IAM、数据权限或审批系统。
- 本例没有实现父子 token 预算守恒、来源抓取缓存和人工升级队列。
