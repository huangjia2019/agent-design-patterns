请为编辑部准备一页“多 Agent Harness 协作边界”技术简报。

1. 使用 `research_topology` 研究团队拓扑与任务调度。
2. 使用 `research_state` 研究上下文、会话与状态隔离。
3. 使用 `research_handoff` 研究跨 Agent 交接与正式工件。
4. 每位研究员只交一张 JSON 资料卡，必须包含：
   `worker_id`、`lane`、`claim`、`source_id`、`source_url`。
5. 收齐三张卡后调用一次 `brief_gate`，不得由研究员自己宣布组合通过。
6. `brief_gate.accepted` 为 true 时才生成简报。否则列出缺席、重复或无效卡片并停止。

最终简报只写三段：

- 拓扑：谁协调，谁执行
- 状态：哪些信息共享，哪些信息隔离
- 交接：消息与正式工件怎样区分

每段保留来源链接。不要修改文件，不要继续派生新的子 Agent。
