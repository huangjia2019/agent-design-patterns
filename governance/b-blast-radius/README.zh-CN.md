# b · 爆炸半径控制 Blast Radius Control

> 模式 · 治理 × 层级
>
> [English README](README.md)

## 问题

一个部门的付款没有越界，多个部门同时付款仍可能冲破公司总额。只在工具调用完成后统计配额，
并发动作已经把副作用做出去了。

## 模式

`BlastRadiusController` 把金额、人数、动作次数、工具和资源范围组织成父子预算树。子节点只能
收窄父节点。外部动作执行前，控制器沿叶子到根节点的完整路径预留容量：

```text
reserve -> begin_effect -> external effect -> confirm_effect
                    \-> unknown -> reconcile
```

预留同时占用叶子和所有祖先预算，因此两个单独合规的兄弟节点不能并发冲破组合上限。稳定
幂等键防止重试重复占用。每次真实外部动作还要把部分预留换成一次性 `EffectPermit`，
最终适配器会重新检查它仍然有效。独立 kill switch 会撤销未消费的预留，并把已经在途、
结果未明的动作留在 `UNKNOWN` 账上等待对账。

子节点的资源前缀可以在父前缀内继续收窄，例如父节点允许 `payroll:`，部门叶子只允许
`payroll:2026-06:department:Engineering`。租约 ID 同时绑定提案摘要，避免相同业务 ID
下的两个不同提案覆盖彼此的预留记录。

## 公共接口

| 对象 | 职责 |
|---|---|
| `BlastBudget` | 金额、人数、次数、动作和资源上限 |
| `ContainmentScope` | 父子层级中的一个控制域 |
| `ContainmentLease` | 执行前已经占住的预算 |
| `EffectPermit` | 一次真实外部效果消费的动态许可 |
| `BlastRadiusController` | 注册、预留、逐笔消费、确认、对账和紧急停止 |
| `GovernanceReceipt` | 预留回执与执行后提交回执 |

## 运行

```bash
python3 governance/b-blast-radius/example.py
pytest governance/b-blast-radius/test_pattern.py -q
python3 governance/payroll-lab/blast_radius_lab.py
python3 governance/payroll-lab/blast_radius_lab.py --overflow
python3 governance/payroll-lab/blast_radius_lab.py --retry-storm
```

薪酬 Lab 从真实 SQLite 工资账本读取 Engineering、Finance 和 Ops 三个部门。前两批预留
成功，第三批自身仍满足部门额度，却因三批合计超过共享执行窗口而在父节点被拒绝。重试风暴
实验让 Ops 批次多跑四遍：无逐笔许可时超付 10,995,840 元，接入一次性许可后实付保持
13,706,097 元，640 次重复提款全部在外部效果前被拒绝。

## 它在双轴里的位置

治理 × 层级。每一层都是上一层的收窄，局部合规必须同时满足全局预算。
