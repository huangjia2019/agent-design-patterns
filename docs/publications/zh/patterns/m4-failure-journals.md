<p style="font-size: 0.9rem; color: var(--color-text-faint); margin-bottom: 1.75rem;">
<a href="https://adpsagent.com/zh/patterns/" style="color: var(--color-text-muted);">模式矩阵</a>
<span style="margin: 0 0.45rem;">/</span>模式白皮书<span style="margin: 0 0.45rem;">/</span>M4
            </p>

<header class="publication-head">
<p class="publication-series">ADPS Agent 设计模式白皮书</p>
<h1>M4 · Failure Journals · 失败日记</h1>
<p class="publication-deck">分离原始失败事实、候选诊断和已验证 lesson，只在后续相似任务中召回适用且仍有效的经验。</p>
</header>

<table>
<tbody>
<tr>
<td style="text-align: left;"><strong>坐标</strong></td>
<td style="text-align: left;">记忆 Memory × 循环 Loop（转）</td>
</tr>
<tr>
<td style="text-align: left;"><strong>成本</strong></td>
<td style="text-align: left;">中（结构化存储 + 召回检索）</td>
</tr>
<tr>
<td style="text-align: left;"><strong>模式组</strong></td>
<td style="text-align: left;">记忆模式</td>
</tr>
<tr>
<td style="text-align: left;"><strong>模式简介</strong></td>
<td style="text-align: left;">分离原始失败事实、候选诊断和已验证 lesson，只在后续相似任务中召回适用且仍有效的经验。</td>
</tr>
</tbody>
</table>

---

## 问题

许多 Agent 系统保存任务进度，却不跨会话保留失败记录。会话结束后，错误现象、错误判断和补救过程随 context 一起消失，后续相似任务可能重复同一错误。例如，Agent 完成主任务后将测试环境配置写入生产配置，之后又在另一个项目中执行了相同操作。

失败日记将这类事件保存为可检索记录。难点在写入侧：错误现象是事实，根因和 lesson 是判断。模型刚失败后给出的解释可能同样错误，不能在一次调用里同时完成诊断和长期发布。

## 坐标说明：记忆 × 循环

- **纵轴 · 记忆**：它把"失败"作为持久化学习材料跨调用累积，是长期记忆里的反例库——一面记成功（程序性记忆），一面记失败（失败日记）。
- **横轴 · 循环**：失败记录在本次任务写入，在后续任务读取并更新，形成跨调用的 outer loop。

## 解决方案与机制

失败日记由三层记录和一条召回链组成：

1. **Failure Event 保存不可变事实**：记录输入引用、工具调用、错误、系统版本、权限范围和原始 trace。后续诊断通过新记录关联，不能回写篡改事件。
2. **Candidate Diagnosis 保存待验证解释**：记录推测根因、可能修复、提出者、置信信息和适用范围。自动生成内容默认处于 `candidate`，不进入主动召回集。
3. **Verified Lesson 保存已发布经验**：通过复现、测试、规则校验或人工审核后，发布 prevention rule、recall condition、valid version 和失效条件。lesson 可以被新版本替代或撤销。
4. **按任务边界召回**：在任务启动、能力边界入口或高风险工具调用前，先按 tenant、scope、system version 和 failure signature 过滤，再按风险与相关性重排。系统只主动注入 `accepted` 且仍适用的 lesson。
5. **从使用结果回写证据**：记录 lesson 是否被取回、是否被采用、是否避免了重复失败。新反例进入候选诊断，不直接覆盖原记录。

原始事件、诊断和 lesson 使用不同保留策略。事件按审计要求保存，候选诊断可以较快清理，已验证 lesson 需要版本和适用范围管理。

## 适用场景

- **生产级长期运行的 agent**：跑数月、反复处理同类任务的 agent。哪些失败要记、哪些任务来时要翻出来，是它的核心价值所在。
- **多租户 SaaS agent**：跨租户错位这类高风险失败要做特殊处理——永不淘汰、每次任务启动强制召回、连续多条触发报警。task signature 用"租户加意图"双因子，一个租户的失败不该让另一个租户收到无关提醒。
- **高风险不可逆操作的 agent**：错误代价大、同样的错不能犯第二次的场景。DevOps、金融、合同处理。

## 已知失效方式

- **任务一次性、没有重复执行场景却硬上**：纯 demo、prototype、一次性脚本，失败被丢弃没问题。失败日记的价值在重复任务，没有重复就没有召回收益。
- **只使用 free-text**：仅记录 task、error 和 timestamp，无法稳定分类和查询。原始事件和诊断都需要 schema，开放说明只能作为补充字段。
- **把模型解释当成事实**：同一个 Agent 在失败后立即生成 root cause 和 prevention rule，并直接写入长期记忆。错误诊断会让后续任务稳定避开正确路径。
- **低价值记录持续累积**：每次轻微异常都形成 lesson，召回噪声会随时间上升。只有达到复用价值和风险门槛的候选才进入验证队列。
- **召回只看语义相似度**：文本相似不代表条件相同。tenant、工具版本、权限、环境和失败阶段应先做结构化过滤，再执行语义召回。
- **旧 lesson 跨版本继续生效**：底层 API、数据 schema 或流程已经变化，历史修复仍被注入。lesson 必须声明适用版本和失效条件。
- **高风险失败与普通失败共用策略**：跨租户数据泄露和 API timeout 的严重程度不同。高风险失败应独立告警、永久保留，并在相关任务中强制召回。

## 验证指标

- **重复失败率**：同类任务中重复出现相同失败的比例。应按 failure signature 比较版本前后变化，不能用数据库记录量代替运行结果。
- **候选转正率与驳回原因**：统计 Candidate Diagnosis 通过复现或审核成为 Verified Lesson 的比例，并分析错误根因、范围过宽和证据不足。
- **召回准确率与漏召回率**：观察已发布 lesson 是否在适用任务中出现，是否错误进入不适用的任务。
- **Lesson 采纳与避免失败率**：记录 Agent 是否采用被召回的 lesson，以及同一 failure signature 是否因此消失。与不注入日记的回放基线比较。
- **过期 lesson 使用率**：已被替代、撤销或超出适用版本的 lesson 仍参与决策的比例。
- **高风险失败计数**：跨租户错位等安全边界事件必须独立监控和告警，不设“可接受的小比例”。

## 最小实现

```
FailureEvent:
    event_id / task_signature / category / stage / error
    input_refs[] / tool_calls[] / system_version / trace_ref / occurred_at

CandidateDiagnosis:
    diagnosis_id / event_id / hypothesis / proposed_fix
    proposed_by / confidence / applicability / status(candidate|rejected|verified)

VerifiedLesson:
    lesson_id / diagnosis_id / prevention_rule / recall_conditions[]
    valid_from / valid_to / applies_to_versions[] / supersedes / review_evidence[]

recall(task):
    filter accepted lessons by tenant + scope + version + risk
    retrieve by failure signature and semantic relevance
    return lessons + source events + recall trace
```

生产实现要保证 FailureEvent append-only，并把候选诊断和正式 lesson 分库或分状态管理。审核过程、发布人、验证证据和替代关系都进入审计链。

## 场景化示例

设想一个多租户 SaaS 客服 Agent 反复遇到工具超时、权限错误和跨租户错位。工具 trace 与业务版本先写成 FailureEvent；模型提出的“token 过期”只进入 Candidate Diagnosis。复现确认后，系统把“刷新凭证并重新校验 tenant\_id”发布为带版本范围的 Verified Lesson。任务启动时先按租户、工具版本和意图过滤，再召回相关 lesson；无法确认的新类别进入 `needs_review`。效果通过重复失败、误召回和过期 lesson 使用情况评估。

## 相邻模式

- **程序性记忆（M5）**：失败日记保存已知失败路径，程序性记忆保存经过验证的成功流程。
- **进度追踪（M3）**：进度追踪维护当前任务步骤，失败日记跨任务保存失败记录。
- **分层保留（M1）**：失败日记是长期记忆层里的专门分区，其分层留存策略正是分层思想在失败档案上的应用。
- **Self-Heal Loop（行动模块）**：自愈循环处理当前任务中的失败；失败日记将失败信号持久化并在后续任务中召回。
- **版本化记忆（候选）**：失败事件保持不可变，诊断和 lesson 通过版本、替代和撤销关系演进。

## 工程判断

失败日记的价值来自发布过程。原始事件提供证据，候选诊断允许推翻，Verified Lesson 才能跨任务复用。缺少这三层，错误经验会比遗忘传播得更稳定。

## 企业证据

<p class="evidence-empty">当前没有与本模式绑定的公开评审案例。模式定义不因此视为已经获得企业验证。</p>

<p style="font-size: 0.88rem; color: var(--color-text-muted);">案例收录要求说明业务约束、实现结构、已知失败和迁移边界。参见 <a href="https://adpsagent.com/zh/join/">贡献与评审规则</a>。</p>

<div class="document-citation">
<p><strong>引用建议：</strong>ADPS，《M4 失败日记》，Agent 设计模式白皮书 v0.3，2026-07-30。</p>
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
<p><a href="https://adpsagent.com/zh/chronicle/#patterns-m4-failure-journals">在 ADPS Chronicle 中查看</a></p>
</section>

<!-- PAGE-CHRONICLE:END -->
