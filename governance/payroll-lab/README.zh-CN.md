# Payroll Governance Lab

薪酬治理模块第 36—40 讲的统一实验台。它接住一份真实的协作边界工件，再对照两条桥：

```text
无治理：AcceptanceReceipt -> Payment

完整链：Accepted Artifact
      -> ActionProposal
      -> Approval Gate
      -> Blast Radius Reservation
      -> Progressive Authority
      -> Payment Adapter
      -> Trace Audit
```

第一条桥故意展示一个真实接口误用：把“工件通过验收”当成“动作获得授权”。第二条桥要求
付款适配器重新校验三张版本绑定的治理回执。

第 36 讲还提供一组互补实验：保持 798 人、13,706,097 元的已验收工件不变，只把组合
现金线从 1300 万放宽到 3000 万。原始放行回执没有记录采用了哪一版尺度，治理侧的
`PolicyRef` 与 `policy_digest` 会让策略变化进入证据链。

第 39 讲把纸面授权接进提案边界：`payroll.disburse` 只有在上游任务契约包含
`propose:payment` 时才能形成行动提案。这一层静态范围约束“任务可以申请什么”，渐进承诺的
版本化凭证再约束“当前 Agent 实际可以执行什么”。

## 文件

| 文件 | 内容 |
|---|---|
| `governance_payroll_imports.py` | 用唯一模块名加载本地文件，避免多个课程 Lab 的 `bench.py` 在全仓测试中碰撞 |
| `bench.py` | 月末薪酬事实、协作工件适配与 SQLite 控制账本 |
| `governance_lab.py` | 无治理桥、完整治理链、补回两张工资单与策略变更过门实验 |
| `ungoverned_policy_lab.py` | 策略盘点、静默改闸与策略摘要实验 |
| `run_governance_module.py` | 模块级 CLI |
| `approval_gate_lab.py` | 第 37 讲 |
| `blast_radius_lab.py` | 第 38 讲 |
| `progressive_commitment_lab.py` | 第 39 讲，真实部门证据、影子运行、限量金丝雀与事故降权 |
| `observability_harness_lab.py` | 第 40 讲 |
| `web_app.py` | FastAPI 教学工作台 |

## 运行

```bash
uv run python governance/payroll-lab/run_governance_module.py --mode naive
uv run python governance/payroll-lab/run_governance_module.py --mode governed
uv run python governance/payroll-lab/run_governance_module.py --mode changed
uv run python governance/payroll-lab/run_governance_module.py --mode policy-drift
uv run python governance/payroll-lab/approval_gate_lab.py --changed
uv run python governance/payroll-lab/approval_gate_lab.py --policy-change
uv run python governance/payroll-lab/blast_radius_lab.py --overflow
uv run python governance/payroll-lab/blast_radius_lab.py --retry-storm
uv run python governance/payroll-lab/progressive_commitment_lab.py
uv run python governance/payroll-lab/progressive_commitment_lab.py --variant
uv run pytest governance -q
```

启动网页工作台：

```bash
uv sync --extra ui
uv run python governance/payroll-lab/web_app.py --port 8767
```

浏览器打开 `http://127.0.0.1:8767`。
