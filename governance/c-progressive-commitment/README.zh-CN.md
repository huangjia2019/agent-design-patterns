# c · 渐进承诺 Progressive Commitment

> 模式 · 治理 × 链式
>
> [English README](README.md)

## 问题

新 Agent 不该在第一天拿到完整生产权限，跑得久也不能自动等同于可信。模型升级、策略更新和
权限变化还会让历史成绩失去可比性。

## 模式

权限沿一条有序链逐级开放：

```text
OBSERVE -> RECOMMEND -> SHADOW -> LIMITED -> AUTONOMOUS
```

每次晋升只前进一步，需要当前权限版本下的新鲜证据窗口和独立管理员批准。运行证据带唯一
`run_id`、来源、评估切片和时间，重复证据、过期证据和切片缺失都不能支持晋升。
`PromotionRequest` 绑定整个证据窗口的摘要。申请之后窗口一旦变化，管理员必须重新审查。
晋升以后证据清零，重新积累。`AuthorityCredential` 绑定 Agent、权限级别、权限版本和策略摘要。

权限凭证只给出能力上限。真实外部动作仍要携带审批门和爆炸半径回执。关键事故会立即降到
`OBSERVE`，旧凭证随版本变化失效。升权者和降权者都由可信角色解析器校验，每次变化写成
`AuthorityTransition`。

策略构造还会验证这条链确实逐级开放：后一级不能丢掉前一级已有动作，真实执行的金额和人数
上限不能缩小，`AUTONOMOUS` 也不能悄悄移除 `LIMITED` 已要求的上游控制。晋级批准与事故
降权必须遵守当前凭证和申请的时间顺序。

## 公共接口

| 对象 | 职责 |
|---|---|
| `CapabilityProfile` | 每一级可做什么、金额和人数上限 |
| `RunOutcome` | 带身份、来源、切片和时间的单次评估证据 |
| `EvidenceWindow` | 当前权限版本下的运行证据 |
| `PromotionRequest` | 绑定完整证据窗口、一次只晋升一级的申请 |
| `AuthorityCredential` | 版本化权限凭证 |
| `AuthorityTransition` | 升权或降权的版本化变化记录 |
| `ProgressiveCommitment` | 入组、记分、晋升、授权和降级 |

## 运行

```bash
python3 governance/c-progressive-commitment/example.py
pytest governance/c-progressive-commitment/test_pattern.py -q
python3 governance/payroll-lab/progressive_commitment_lab.py
python3 governance/payroll-lab/progressive_commitment_lab.py --variant
```

## 它在双轴里的位置

治理 × 链式。当前一级的证据是进入下一级的前置条件，不能跳级，也不能继承上一版本的成绩。
