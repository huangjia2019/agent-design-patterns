<p style="font-size: 0.9rem; color: var(--color-text-faint); margin-bottom: 1.75rem;">
<a href="https://adpsagent.com/zh/patterns/" style="color: var(--color-text-muted);">模式矩阵</a>
<span style="margin: 0 0.45rem;">/</span>模式白皮书<span style="margin: 0 0.45rem;">/</span>R1
            </p>

<header class="publication-head">
<p class="publication-series">ADPS Agent 设计模式白皮书</p>
<h1>R1 · Chain-of-Thought · 思维链</h1>
<p class="publication-deck">管理接口允许保留的 reasoning 摘要、决策依据、结构化输出和模型元数据，支持审计、回查与跨模型兼容。</p>
</header>

<table>
<tbody>
<tr>
<td style="text-align: left;"><strong>坐标</strong></td>
<td style="text-align: left;">推理 Reasoning × 链式 Chain（传）</td>
</tr>
<tr>
<td style="text-align: left;"><strong>成本</strong></td>
<td style="text-align: left;">可变（随 reasoning effort、模型接口和留痕策略变化）</td>
</tr>
<tr>
<td style="text-align: left;"><strong>模式组</strong></td>
<td style="text-align: left;">推理模式</td>
</tr>
<tr>
<td style="text-align: left;"><strong>模式简介</strong></td>
<td style="text-align: left;">管理接口允许保留的 reasoning 摘要、决策依据、结构化输出和模型元数据，支持审计、回查与跨模型兼容。</td>
</tr>
</tbody>
</table>

---

## 问题

模型输出结论时，如果系统没有保留决策依据、证据和执行 trace，错误发生后就难以 debug，也无法满足审计回查要求。Agent 的推理过程具有灰盒特征，需要由工程层补充可观测记录。

Chain-of-Thought 在这里指 reasoning trajectory 的工程管理，包括可用摘要的存储、证据绑定、跨模型 fallback 和按任务复杂度控制 reasoning effort。“Let's think step by step”属于提示方法；当前 reasoning model 还可能返回结构化 reasoning 字段、摘要或受保护 token，系统需要按各接口能力统一处理。

## 坐标说明：推理 × 链式

- **纵轴 · 推理**：CoT 管理从输入证据到输出决策之间可获得的 reasoning 产物。不同接口可能只提供公开摘要、结构化字段或受保护 token，工程层不能假定自己能看到模型的完整内部推理。
- **横轴 · 链式**：推理本身是一条线性 trajectory，从输入走到输出，中间每一步都依赖前一步（思考 → 中间结论 → 最终答案）。这是天然的链式结构，不是并行撒网，也不是循环迭代。

## 解决方案与机制

推理 trajectory 应作为结构化数据管理。实现需要覆盖以下四项职责：

1. **持久化**：保存接口与组织政策允许留存的 reasoning 摘要、证据引用、决策、模型元数据和执行 trace，并按 trace\_id 索引。私有推理 token 不应被复制到审计库。
2. **跨模型归一**：不同 reasoning model 返回公开摘要、结构化字段或受保护 reasoning token 的方式不同。入库前 normalize 成统一 schema，并保留 provider、model、接口版本和可见性元数据。
3. **跨模型 fallback strip**：thinking block 的签名跟生成它的模型绑定。主模型限流切到 fallback 模型时，fallback 模型不接受其他模型的签名，必须先 strip 掉所有不兼容的 thinking block 再发，否则整个请求被拒、Agent 调用失败。
4. **effort 控制**：thinking 是付费 token，但更多 thinking 不一定更高质量。给一个 effort 控制曲面（off / low / medium / high / max），让简单任务用 low、复杂任务用 high。

reasoning model 输出的解释可能是事后生成的合理化描述，不能直接视为模型内部计算的完整记录。CoT 可作为可观测性信号，关键决策仍需外部证据和独立验证。

## 适用场景

- **多跳逻辑、需要解释的判断**：理赔审核、合同风险识别、信贷决策，每个结论都要能向监管解释"依据是什么"。
- **合规留痕场景**：金融、医疗、法律工作流可能要求保存输入证据、适用规则、审批记录、模型元数据和决策依据。具体留存范围由适用法规、组织政策与模型接口共同确定。
- **教学与调试场景**：可以展示经过处理的 reasoning 摘要和中间结论，帮助定位错误步骤。

## 已知失效方式

- **给 reasoning model 机械叠加 step instruction**：模型已经具备内部推理机制时，额外要求逐步展开未必改善结果，还可能增加 token 或干扰原有策略。应通过任务集对照，而不是把固定话术视为通用增益。
- **fallback 时不 strip thinking**：主模型挂掉切 fallback 时不清理跨模型签名，整个请求被拒、Agent 调用失败。这种 incident 平时不暴露，一旦主模型限流就集中爆发。
- **trace 只写日志文件**：需要回查某个 case 的输入证据、适用规则、模型版本和最终决策时，散在日志文件里的记录很难拼接。应使用结构化 trace，并按 trace\_id 查询。
- **所有任务一个 effort 跑**：简单任务（"今天周几"）和复杂任务（"这份合同有什么风险"）用同一个 effort，既浪费了简单任务的 token，又委屈了复杂任务的质量。
- **延迟敏感场景开高 effort thinking**：extended thinking 可能增加首响应时间。实时交互应按渠道延迟预算关闭或降低 effort，并将深度分析移到异步路径。

## 验证指标

- **Reasoning token 占比**：按任务类型观察 thinking token 在总调用中的占比。相对基线显著升高时检查 over-thinking，显著降低时用评测确认是否出现推理不足。
- **fallback strip 成功率**：主模型切换 fallback 时，跨模型不兼容的 thinking 字段应被完整清理。任何失败都可能导致调用错误，需要单独告警。
- **trace 可回查率**：检查历史决策能否按 trace\_id 找回允许留存的 reasoning 摘要、输入证据和模型元数据。合规要求由具体业务政策确定。

## 最小实现

```
任务进来 → 按复杂度选 effort 档（off / low / medium / high / max）
模型返回可留存摘要 / 结构化决策 / 模型元数据 → normalize 成统一 schema → 进结构化 trace
若主模型限流 fallback：
    strip 掉所有跟目标模型不兼容的 thinking block，再发请求
审计取数双视图：
    审计视图  → 允许留存的 reasoning 摘要 + 证据 + 最终决策 + fallback 链
    客户视图  → 脱敏依据摘要，不暴露受保护 reasoning 细节
返回 final_answer + audit trace（按 trace_id 索引，按留存政策保存）
```

生产实现不应为 reasoning model 重复添加 step instruction；effort 作为 per-request 或 per-task 配置；标签归一规则随模型接口更新；trace 写入结构化 trace bus，支持长期回查。

## 场景化示例

梁博团队的执行型 Agent 将解释性信息和可执行的 answer 分开。接口允许留存的摘要、证据和模型元数据进入 trace，answer 则是由下游程序解析的 JSON 决策对象。answer 字段驱动后续动作，trace 用于审计回查。

JSON 解析失败时，系统执行预定义的安全默认动作，避免随机重试。answer 执行 schema 强校验，解析失败进入监控，审计材料按接口可见性和组织留存政策保存。

## 相邻模式

- **复杂度路由（R2）**：CoT 的 effort 控制调整单次调用的推理深度，复杂度路由进一步选择模型和任务级档位。
- **并行探索（R3）**：并行的每一条分支内部通常就是一条思维链，并行是在 CoT 之上叠加的"多采样"。
- **迭代假设验证（R4）**：迭代的每一轮也是一条思维链，迭代是把多条思维链在时间维度串起来反复修正。
- **双模架构（R5）**：Reasoner 运行完整推理链，Talker 只承担低延迟交互。

## 工程判断

Chain-of-Thought 的工程重点是管理推理产物的生命周期，包括存储、摘要、证据绑定、审计和跨模型兼容。对外可见的是可审计摘要与依据，不是模型的私有推理 token。

## 企业证据

以下现场记录说明该模式在具体业务约束下如何实现。案例结论只在文中声明的系统边界内成立。

<ul style="list-style: none; margin: 0.5rem 0 1rem 0; padding: 0;">
<li style="margin-bottom: 0.6rem; line-height: 1.55;"><a href="https://adpsagent.com/zh/patterns/r1-chain-of-thought/cases/liangbo/" style="font-weight: 600;">东方屹腾 · 思维链</a><span style="color: var(--color-text-muted);"> — 每轮推理输出叙事结论和一个可映射到程序动作的下一步控制信号。</span></li>
</ul>

<p style="font-size: 0.88rem; color: var(--color-text-muted);">案例收录要求说明业务约束、实现结构、已知失败和迁移边界。参见 <a href="https://adpsagent.com/zh/join/">贡献与评审规则</a>。</p>

<div class="document-citation">
<p><strong>引用建议：</strong>ADPS，《R1 思维链》，Agent 设计模式白皮书 v0.3，2026-07-30。</p>
<p><a href="https://adpsagent.com/zh/patterns/">模式目录</a> · <a href="https://github.com/huangjia2019/agent-design-patterns" rel="noopener" target="_blank">参考实现</a> · <a href="https://creativecommons.org/licenses/by/4.0/" rel="license noopener" target="_blank">CC BY 4.0</a></p>
<p class="publication-disclaimer"><strong>文档状态：</strong>本页为公开评审稿。模式定义与分类可供讨论和引用；场景化示例用于说明机制，不代表已经核验的企业案例。具名实践另见<a href="https://adpsagent.com/zh/cases/">案例库</a>。ADPS 欢迎业界提交带来源、测量口径和发布授权的案例。</p>
</div>

<!-- PAGE-CHRONICLE:START -->

<section aria-labelledby="page-chronicle-title" class="page-chronicle">
<h2 id="page-chronicle-title">溯源记录</h2>
<dl>
<div><dt>来源记录</dt><dd>ADPS 模式白皮书；先行工作与参考资料见正文</dd></div>
<div><dt>本页首次公开</dt><dd><time datetime="2026-06-07">2026-06-07</time></dd></div>
</dl>
<p><a href="https://adpsagent.com/zh/chronicle/#patterns-r1-chain-of-thought">在 ADPS Chronicle 中查看</a></p>
</section>

<!-- PAGE-CHRONICLE:END -->
