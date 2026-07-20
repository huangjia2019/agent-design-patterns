# d · 交接链 Handoff Chain

> 模式坐标：**协作 × 链式**
>
> [English README](README.md)

## 要解决的问题

专才 Agent 经常按固定顺序协作：意图、核算、资金检查、打款、回执。直接共享一个字典，会留下
四道缺口：

1. 当前棒漏交字段，错误拖到几棒以后才发作。
2. 上游已有同名字段，当前棒什么都不交也可能被算作履约。
3. 阶段直接修改共享对象，可以绕过棒上不回改。
4. 键虽然存在，类型、证据、生产者或业务值可能是错的。

交接链把每道接缝变成一次提交边界。

## 契约链

```text
任务契约（TaskContract）
  -> 不可变接力棒 r0
  -> 阶段增量（StageDelta）
  -> 接力棒 r1 + 阶段回执（StageReceipt）
  -> ...
  -> 验收回执（AcceptanceReceipt）
```

每个 `StageSpec` 声明 `requires` 与 `provides`。每个交付字段只有一份 `FactRule`，
其中写明唯一生产者、运行时类型、证据要求和可选的语义校验器。

阶段拿到的是与主对象脱离的只读 `BatonView`，只能返回 `StageDelta`。编排器验完增量，
才创建下一版不可变接力棒。

## 接缝不变量

- 开始前，所有 `requires` 都已经提交。
- 当前阶段必须亲自交出全部 `provides`。
- 未声明字段直接拒绝。
- 每个事实只有一个生产者，同值重复写入也不允许。
- 类型、证据和业务语义在生产该值的接缝检查。
- 每次提交生成 `StageReceipt`，绑定输入与输出指纹。
- 失败保留上一版检查点。重试从失败阶段继续，并得到相同的 `stage_run_id`。

## 文件

| 文件 | 内容 |
|:--|:--|
| [`pattern.py`](pattern.py) | 通用不可变接力棒、字段所有权、接缝校验、回执、检查点与静态链。 |
| [`example.py`](example.py) | 使用通用接口的旅行小例子，无需 API key。 |
| [`test_pattern.py`](test_pattern.py) | 精确交付、所有权、只读快照、语义校验、回执与重试的不变量。 |
| [`../payroll-lab/handoff_chain_lab.py`](../payroll-lab/handoff_chain_lab.py) | 第 35 讲薪酬 Lab：从意图走到回执，以及错误值实验。 |
| [`langgraph/`](langgraph/) | 把同一提交边界接进线性图。 |
| [`claude-agent-sdk/`](claude-agent-sdk/) | 把专才子代理适配成 `StageFn`。 |

## 运行

```bash
python collaboration/d-handoff-chain/example.py
pytest collaboration/d-handoff-chain/test_pattern.py -q

python collaboration/payroll-lab/handoff_chain_lab.py
python collaboration/payroll-lab/handoff_chain_lab.py --wrong-value
pytest collaboration/payroll-lab/test_handoff_chain_lab.py -q
```

错误值实验先使用一份薄契约。键、生产者、类型和证据全部正确，因此错误薪酬总额仍被支付。
同样的五棒换成正式放行契约后，`net_total` 因无法对上控制账本而死在 `settle` 接缝。
编排器能严格执行已声明语义，无法替契约制定者补写遗漏规则。

## 静态链与动态交接

这个实现属于预先编排的专才流水线。动态对话 Handoff 还需要目标白名单、上下文过滤、
权限转移和活跃 Agent 生命周期控制。

## 生产边界

同一检查点上的 `stage_run_id` 可以作为稳定幂等键，但参考实现没有提供持久化数据库、
分布式锁、签名证据、补偿引擎或 Outbox。带外部副作用的阶段必须消费幂等键并持久化执行结果，
再返回 `StageDelta`。
