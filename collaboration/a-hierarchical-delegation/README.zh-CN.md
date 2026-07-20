# a · 层级委派 Hierarchical Delegation

> 模式 · 协作 × 层级
>
> [English README](README.md)

## 问题

薪酬主管要完成 800 人月末结算，又不能把每个工人的原始过程塞进同一个上下文。拆花名册
很容易，可信委派还要回答四个问题：

1. 每个工人拿到的是哪一个任务版本
2. 交回的结果是否覆盖了分配给它的花名册
3. 谁依据什么证据接收了这份结果
4. 每批都合规以后，组合总额是否越过全局约束

## 模式

主管持有一个根 `TaskContract`，再把它拆成互不重叠的子契约。每个子任务都沿协作模块的
共用边界接口流动：

```text
TaskContract -> HandoffEnvelope -> ArtifactEnvelope -> AcceptanceReceipt
```

工人把 `SalaryBatchResult` 放进工件信封。信封绑定子契约摘要和指定接收者。
`SafetyBoundary` 检查契约绑定、持久证据、花名册数量与指纹、金额、置信度、待复核项和
工人结论，最后签发 `AcceptanceReceipt`。验收结论因此成为可保存、可审计的对象。

批次验收结束后，主管再生成根级组合工件。`PortfolioBoundary` 检查单个工人看不到的事实，
包括全量覆盖、未决子批次和组合现金上限。

拓扑还守一条角色纪律：主管负责拆分、派发、汇总和验收，不亲自计算单人工资。

## 公共接口

| 对象 | 职责 |
|---|---|
| `SalaryBatchResult` | 单个工人产生的不可变业务载荷 |
| `BatchAssignment` | 一个子任务交接包及其精确花名册 |
| `SafetyBoundary` | 批次级验收策略和回执签发者 |
| `PayrollPortfolioResult` | 主管对全部子工件与回执的汇总 |
| `PortfolioBoundary` | 根级覆盖与组合约束 |
| `DelegationSummary` | 一次委派运行的完整证据 |
| `SettlementSupervisor` | 带可插拔 `dispatch` 接缝的层级编排器 |

跨模式共用的传输对象位于
[`../boundary_contract.py`](../boundary_contract.py)。

## 文件

| 文件 | 内容 |
|---|---|
| [`pattern.py`](pattern.py) | 框架无关的模式本体与双层验收接口 |
| [`example.py`](example.py) | 确定性的 800 人示例，无需 API key |
| [`test_pattern.py`](test_pattern.py) | 契约、证据、隔离、并发和组合级不变量 |
| [`langgraph/tutorial.ipynb`](langgraph/tutorial.ipynb) | 显式图实现 |
| [`claude-agent-sdk/tutorial.ipynb`](claude-agent-sdk/tutorial.ipynb) | 子代理实现 |

## 运行

```bash
python collaboration/a-hierarchical-delegation/example.py
pytest collaboration/a-hierarchical-delegation/test_pattern.py -v
python collaboration/payroll-lab/hierarchical_delegation_lab.py
python collaboration/payroll-lab/hierarchical_delegation_lab.py --sum-blind
```

## 它在双轴里的位置

协作 × 层级。相邻模式是扇出聚合、对抗评审和交接链。
