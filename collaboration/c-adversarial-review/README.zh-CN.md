# c · 对抗评审 Adversarial Review

> 模式坐标：**协作 × 循环**
>
> [English README](README.md)

## 要解决的问题

多加一个评审 Agent，还不能形成可靠的放行控制。工程上至少有三道缺口：

1. 作者、修改者和评审者可能仍由同一个身份承担。
2. 异议清单为空，只能说明检查过的规则没有报错，无法证明必查规则都有人检查。
3. `r0` 的评审结果可能被错误地拿去放行修改后的 `r1`。

对抗评审把提异议和做放行决定分开。评审者只交带规则编号和证据的结构化异议。确定性闸门
同时检查评审规则覆盖、评审者健康状态和阻断级异议，三项都合格才放行。

## 契约链

实现沿用协作模块共同的对象链：

```text
任务契约（TaskContract）
  -> 工件信封（ArtifactEnvelope）
  -> 评审请求（ReviewRequest）
  -> 评审回执（ReviewReceipt）
  -> 验收回执（AcceptanceReceipt）
```

`ReviewReceipt` 同时绑定：

- 任务契约摘要
- 工件编号、修订号和内容指纹
- 评审规则版本
- 已检查与缺失的规则编号
- 评审者身份、故障和异议

循环顺序是 `评审 -> 修改 -> 再评审`。最后一次允许的评审不会再生成一份来不及复审的新工件。

## 放行条件

`ReviewGate` 只认这条确定性规则：

```python
receipt.complete and not receipt.blockers
```

`receipt.complete` 表示必查规则没有缺口，评审者也没有故障。评审者有权提出异议，没有权签发
通过。

## 文件

| 文件 | 内容 |
|:--|:--|
| [`pattern.py`](pattern.py) | 通用的契约绑定评审面板、闸门、回执、独立性检查与有界修订循环。 |
| [`example.py`](example.py) | 旅行场景的小型通用示例，无需 API key。 |
| [`test_pattern.py`](test_pattern.py) | 覆盖规则、身份、版本绑定、评审故障、修订与升级的不变量测试。 |
| [`../payroll-lab/adversarial_review_lab.py`](../payroll-lab/adversarial_review_lab.py) | 第 34 讲薪酬 Lab：三类评审、版本化规则、确定性闸门与双付盲区。 |
| [`langgraph/`](langgraph/) | 用显式回边连接评审循环。 |
| [`claude-agent-sdk/`](claude-agent-sdk/) | 用独立子代理连接模型评审者。 |

## 运行

```bash
python collaboration/c-adversarial-review/example.py
pytest collaboration/c-adversarial-review/test_pattern.py -q

python collaboration/payroll-lab/adversarial_review_lab.py
python collaboration/payroll-lab/adversarial_review_lab.py --blind-spot
pytest collaboration/payroll-lab/test_adversarial_review_lab.py -q
```

盲区实验会故意使用一份只要求检查工资单状态的窄规则。系统会据此放过重复员工。换成正式
放行规则后，同一个评审员会因为缺少重复项检查和总额对账而被闸门扣住。结论很明确：
**闸门可以严格执行规则，但无法替规则制定者补齐风险目录。**

## 生产边界

参考实现检查声明的身份编号和 Python callable 是否分离。它无法证明进程隔离、模型独立、
证据真实性，也无法证明评审者真的执行了自己声明的每一项检查。生产系统还要补工作负载身份、
签名证据、规则治理、超时重试、遥测和人工升级。

## 双轴坐标

对抗评审位于**协作 × 循环**。反思模块的生成批评模式用于评价并改进一个 Agent 的产出。
本模式把独立评审身份和放行边界带进多个责任主体共同处理的工件。
