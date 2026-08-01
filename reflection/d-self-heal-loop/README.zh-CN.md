# Self-Heal Loop

Self-Heal Loop 是一个有界修复事务：

`diagnose -> fix -> review -> atomic apply -> verify -> compensate`

Generator-Critic 评估一次提案；Self-Heal 从确定性失败信号开始，可以重复修复，但必须受稳定性预算约束。

## 合约与安全证明

`Patch.digest` 绑定规范化文件路径和可执行的 `payload`，不依赖 description。每次 diagnose、fix、review、verify 前后都会读取无副作用的状态摘要。原子 apply 返回回执；任何非成功出口都会按逆序补偿可寻址 apply，并读取最终摘要。只有回滚回执和最终状态同时证明恢复，trace 才会宣称已恢复；缺失证明或回滚失败会如实转为人工交接。

| 公开项 | 合约 |
| --- | --- |
| `HealStatus` | `FIXED`、`BLOCKED_BY_CRITIC`、`ROLLED_BACK_REGRESSION`、`ROLLED_BACK_NO_PROGRESS`、`MAX_ROUNDS_HUMAN_HANDOFF`、`STAGE_ERROR_HUMAN_HANDOFF`、`ROLLBACK_FAILED_HUMAN_HANDOFF` |
| 回执 | `PatchReview`、`ApplyReceipt`、`VerificationReceipt`、`RollbackReceipt` |
| Trace 记录 | `StageError`、`HealRound`、`HealTrace` |
| 回调 | `DiagnoseFn(FailureSignal)`、`FixFn(str)`、`ReviewFn(Patch, FailureSignal)`、`ApplyFn(Patch)`、`VerifyFn(ApplyReceipt)`、`RollbackFn(ApplyReceipt)`、`StateDigestFn()` |

核心允许经过绑定 review 的测试文件补丁。独立示例和 payroll 适配器会拒绝它，因为对账测试属于应用层安全策略。

## 文件

- `pattern.py`：框架无关的合约和事务引擎
- `test_pattern.py`、`test_transaction_contract.py`：行为与对抗性证明
- `example.py`：小型确定性 source-only 示例
- `../payroll-lab/self_heal_lab.py`：基于快照的教学场景

## 参考实现

[`shared.py`](shared.py)、[`langgraph/tutorial.ipynb`](langgraph/tutorial.ipynb)
和 [`langchain/tutorial.ipynb`](langchain/tutorial.ipynb) 提供共享的确定性
fixture，以及这份合约的两种框架视图。两套 notebook 都使用经过加固的
receipt/digest 合约，并按固定顺序执行同一组七个场景：`convergence`、
`critic_block`、`no_progress`、`regression`、`round_budget`、`stage_error` 和
`rollback_failure`。

## Notebook 验证

`JUPYTER_PATH` 会把 `python3` 固定到项目 venv，避免陈旧的用户级 kernelspec
误选到另一个解释器。

```bash
env JUPYTER_PATH="$PWD/.venv/share/jupyter" \
  MODEL_PROVIDER=ernie MODEL_NAME=ernie-5.1 \
  OPENAI_API_KEY= ANTHROPIC_API_KEY= ERNIE_API_KEY= \
  uv run pytest --nbmake --nbmake-kernel=python3 --nbmake-timeout=120 \
  reflection/d-self-heal-loop/langgraph/tutorial.ipynb \
  reflection/d-self-heal-loop/langchain/tutorial.ipynb
```

## 运行与验证

```bash
uv run pytest reflection/d-self-heal-loop -q
uv run python reflection/d-self-heal-loop/example.py
uv run pytest reflection/payroll-lab/test_self_heal_lab.py reflection/payroll-lab/test_ui_service.py -q
uv run python reflection/payroll-lab/self_heal_lab.py
uv run python reflection/payroll-lab/self_heal_lab.py --meltdown
```
