# a · 审批门 Approval Gate

> 模式 · 治理（Governance）× 路由（Router）
>
> [English README](README.md)

## 问题

一份薪酬工件已经通过协作验收，只能说明内容符合上游契约。银行付款还需要回答另外四个问题：

1. 这项动作应该自动放行、交给人审，还是直接拒绝
2. 谁能审批，提案人能不能审批自己
3. 两人复核是否真的来自两个不同的人
4. 提案或策略变化以后，旧审批还能不能继续使用
5. 审批人声称的角色是否来自可信身份目录

## 模式

`ApprovalGate` 先用确定性策略评估 `ActionProposal`，第一次路由到三条路径：

```text
AUTO_ALLOW | HUMAN_REVIEW | DENY
```

如果进入人审，`ApprovalPolicy.approval_tiers` 再按金额档位路由签字角色。同一份提案和
同一版策略重复进入门时，系统返回原票据，不清空已有签署，也不顺延有效期。

高风险路径生成有有效期的 `ApprovalTicket`。每次签署记录审批人、角色、决定和时间。全部必需
角色由不同的人完成后，门才签发 `GovernanceReceipt`。回执同时绑定提案摘要和策略摘要，提案
还携带已验收工件的内容摘要。金额、工件内容或审批策略任一变化，旧回执都会失效。

`role_resolver` 从 IAM 或组织权限目录读取审批人的真实角色，调用方不能靠自报角色获得审批权。
无人审批、审批超时、审批人拒绝都按拒绝处理。票据进入允许或拒绝终态后不再接受新签署。

修改审批策略也要经过审批门。`install_policy()` 只接受绑定新策略内容的变更提案，并用当前
生效的旧策略复核审批回执，随后才允许安装新版策略。

## 公共接口

| 对象 | 职责 |
|---|---|
| `ApprovalPolicy` | 自动放行、人审和硬拒绝边界 |
| `ApprovalTier` | 第二次路由使用的金额档位与签字角色 |
| `ApprovalTicket` | 版本绑定、带有效期的人审任务 |
| `ApprovalAttestation` | 一个审批人的角色与决定 |
| `ApprovalEvaluation` | 路由结果、回执和可选工单 |
| `ApprovalGate` | 风险路由、maker-checker 与最终授权 |

跨治理模式共用的提案和回执位于
[`../boundary_contract.py`](../boundary_contract.py)。

## 运行

```bash
uv run python governance/a-approval-gate/example.py
uv run pytest governance/a-approval-gate/test_pattern.py -q
uv run python governance/payroll-lab/approval_gate_lab.py
uv run python governance/payroll-lab/approval_gate_lab.py --changed
uv run python governance/payroll-lab/approval_gate_lab.py --policy-change
```

## 它在双轴里的位置

治理（Governance）× 路由（Router）。它选择一条责任路径，爆炸半径控制负责限制影响范围，渐进承诺负责判断 Agent
当前拥有什么权限，可观测性负责保存完整因果证据。
