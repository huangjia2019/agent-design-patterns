<p style="font-size: 0.9rem; color: var(--color-text-faint); margin-bottom: 1.75rem;">
<a href="https://adpsagent.com/zh/patterns/" style="color: var(--color-text-muted);">模式矩阵</a>
<span style="margin: 0 0.45rem;">/</span>模式白皮书<span style="margin: 0 0.45rem;">/</span>M5
            </p>

<header class="publication-head">
<p class="publication-series">ADPS Agent 设计模式白皮书</p>
<h1>M5 · Procedural Memory · 程序性记忆</h1>
<p class="publication-deck">将已验证的做法发布为可命名、可触发、可版本化的指令或可执行资产，并在依赖变化后重新认证。</p>
</header>

<table>
<tbody>
<tr>
<td style="text-align: left;"><strong>坐标</strong></td>
<td style="text-align: left;">记忆 Memory × 层级 Hierarchy（分）</td>
</tr>
<tr>
<td style="text-align: left;"><strong>成本</strong></td>
<td style="text-align: left;">中（蒸馏 + 索引 + lifecycle 管理）</td>
</tr>
<tr>
<td style="text-align: left;"><strong>模式组</strong></td>
<td style="text-align: left;">记忆模式</td>
</tr>
<tr>
<td style="text-align: left;"><strong>模式简介</strong></td>
<td style="text-align: left;">将已验证的做法发布为可命名、可触发、可版本化的指令或可执行资产，并在依赖变化后重新认证。</td>
</tr>
</tbody>
</table>

---

## 问题

同一类任务即使已经成功执行多次，Agent 仍可能在每次请求中重新读取 reference、重复试错并执行相同路径。原因是执行结果没有转化为可复用的流程资产。

程序性记忆在任务成功后提取触发条件、执行步骤、工具依赖和验收规则，保存为可复用 skill。后续同类任务可以加载该 skill，减少重新探索。它也为组织 process 提供机器可读、可审查的表达形式。

## 坐标说明：记忆 × 层级

- **纵轴 · 记忆**：它把成功工作流封装为可复用的"技能",对应认知科学里的 procedural memory（程序性记忆，"怎么做"），区别于 declarative memory（陈述性记忆，"知道什么",即 RAG 的对象）。
- **横轴 · 层级**：技能库按 atomic skill、composite skill 和 workflow 分层组织，上一层可以组合下一层能力。

## 解决方案与机制

1. **三阶段加载**：启动时只加载每个 skill 的 name 和 description（discovery）；任务匹配后再读取完整 SKILL.md（activation）；执行阶段按需加载脚本和资源。该设计避免技能库内容在启动时全部占用 context。
2. **两种来源**：人精心写（Anthropic Agent Skills 路线，审过、版本化、进 git）和 agent 自动蒸馏（Hermes 路线，干完任务自己写）。来源字段影响信任级别。
3. **自动蒸馏**：复杂任务成功完成后，Agent 分析 trajectory、识别可复用模式（输入、工具序列、输出格式），写成候选 skill。是否触发应依据任务复杂度、复用价值和人工纠错情况，而不是固定的工具调用次数。
4. **人机同读格式**：使用 markdown 和 YAML frontmatter，使人工审查、git diff 和 Agent 加载共用同一份源文件。
5. **两级固化形态**：指令型资产使用 SKILL.md、runbook 或 workflow 描述步骤，运行时仍允许 Agent 判断例外；可执行资产把稳定计算或操作编译成代码，运行时只负责意图匹配、参数校验和调用。确定性要求高且任务空间可枚举时，后者能减少生成波动，但仍需要权限、回执和失败处理。
6. **首次验证与认证**：候选 skill 先在 replay、shadow 或受控环境中运行，使用已知成功样本、失败样本和边界条件验证。通过后进入 `active`，并记录 reviewer、evidence 和 dependency versions。
7. **lifecycle 管理**：跟踪 use\_count、success\_rate、人工纠错和依赖版本。触发条件、工具 schema 或底层服务变化后进入 `needs_revalidation`；低质量或长期不用的资产退出活动集，但保留撤销原因和回退版本。

## 适用场景

- **周期性、模板性任务**：同一类任务反复出现、有相对稳定的成功路径、有明确的入口出口条件。集群配置变更、批量重启和备份恢复等标准运维事件是常见应用。
- **企业 process 沉淀**：律所的客户分级逻辑、医院的急诊分诊流程和企业退款流程可以写入 SKILL.md，形成可复用、可审查的组织资产。
- **需要带判断执行的场景**：skill 提供默认流程，Agent 仍需根据当前 context 决定是否调整步骤或退出 skill 进入 explore。

## 已知失效方式

- **任务每次都不一样却硬沉淀**：开放域研究这类任务沉淀不出固定流程，强行做成 skill 是浪费。
- **任务只跑一次**：沉淀成本高于复用收益，不该做。
- **流程尚未稳定就固化**：底层流程持续变化时，skill 会快速过期并误导执行。
- **场景开放时强行重固化**：可执行资产需要可枚举的意图和稳定输入。任务结构持续变化时，维护成本会超过复用收益，应退回指令型资产或继续探索。
- **流程未经梳理**：schema 字段、触发条件和 lifecycle 未定义时，procedural memory 无法稳定工作。应先完成流程梳理。
- **自蒸馏 skill 直接投产**：Agent 自动蒸馏的 skill 应进入试用期，分别按 skill 和 explore 路径执行并比较结果，多次一致后再转为正式版本。自蒸馏项和人工编写项需要不同信任级别。
- **只固化代码，不固化契约**：程序能够运行，却没有前置条件、权限范围、验收、幂等和回滚说明。执行更快，也会更快地产生不可解释的副作用。
- **依赖变化后继续调用**：工具参数、数据 schema 或政策变化，skill 仍保持 active。依赖版本需要进入认证条件并触发失效。
- **库只增不减**：不做 lifecycle，过期低成功率的 skill 持续误导 agent。

## 验证指标

- **复用率**：同类任务命中已有 skill 而非从零 explore 的比例。应结合成功率和人工纠错率判断复用是否真正有效。
- **skill 成功率**：调用某 skill 后任务成功的比例。相对自身基线持续下降时，应检查底层服务、触发条件和验收规则是否变化。
- **token / 时间开销**：将复用 skill 与从零 explore 的同类任务对照，同时检查结果质量，避免用低成本掩盖错误执行。
- **自蒸馏转正率**（业务判定）：自动蒸馏产物通过试用期并转为正式 skill 的比例。偏低说明蒸馏触发条件或质量校验需要调整。
- **认证有效率**：活动资产的工具、schema、政策和测试证据是否仍与当前环境匹配。
- **回退与人工接管率**：执行型资产遇到边界条件后能否停止并转入安全回退，而不是继续猜测。

## 最小实现

```
Skill = SKILL.md 的结构化形态：
    name / description（用于 discovery）/ body（workflow + best practices）
    triggers[] / preconditions[] / steps[] / failure_handling[]
    mode(instruction|executable) / source(human|agent|refined)
    acceptance[] / permissions[] / idempotency / rollback
    dependency_versions{} / status(candidate|active|needs_revalidation|retired)
    review_evidence[] / use_count / success_rate
SkillLibrary：
    discover()                    → 启动只返回 name + description
    activate(task, top_k)         → 匹配 trigger、scope、版本和前置条件
    certify(candidate, replay_set)→ 通过回放、边界样本和人工审核后发布
    mark_used(name, success)      → 执行后记成功率
    distill_from_trajectory(...)  → 满足复杂度、成功和复用价值条件时生成候选 skill
    invalidate_on_dependency(...) → 依赖变化后转 needs_revalidation
    retire(...)                   → 退出活动集并保留回退版本与原因
```

蒸馏只生成候选资产。发布过程验证触发条件、输入范围、权限、验收和回退，并将依赖版本写入认证记录。自蒸馏和人工编写的 skill 使用不同信任级别。

## 场景化示例

设想一个运维团队让 DevOps Agent 处理 Redis 集群配置变更、Kubernetes 批量重启和 PostgreSQL 备份恢复等重复事件。人工编写的 runbook 经 SRE leader review 后进入 `runbooks/`，Agent 自动蒸馏的内容进入 `auto-skills/` 的评审队列。frontmatter 的 triggers 使用关键词或正则，结合规则和 LLM 判断；preconditions 检查访问权限和目标 namespace；每个 step 标记 idempotent 或提供 rollback；自动蒸馏 skill 先走 shadow 或双轨回放，结果稳定且经人工批准后再转为活动版本。是否节省时间和 token，要用同类任务的本地基线验证。

## 相邻模式

- **反思模块 F2 Skill Package（技能包）**：两者共用技能库、SKILL.md、三阶段加载和 lifecycle。M5 描述成功流程如何写入记忆，F2 描述反思验证后如何封装技能。
- **失败日记（M4）**：程序性记忆保存经过验证的成功流程，失败日记保存失败路径。
- **分层保留（M1）**：M1 定义记忆作用域，M5 是长期记忆中的程序性分区；技能库内部也可按 atomic、composite 和 workflow 分层。
- **RAG（M2）**：RAG 管理 declarative memory，M5 管理 procedural memory。
- **审批门与护栏三明治**：可执行程序性记忆缩短了推理路径，但不会取消高风险动作的前置审批、参数校验和后置验收。

## 工程判断

程序性记忆把一次成功变成可复核的能力资产。复用价值来自稳定触发、明确契约和持续认证；单纯把轨迹存下来还不够。

<!-- ADPS-BLUEBOOK-SLOT -->

<div class="document-citation">
<p><strong>引用建议：</strong>ADPS，《M5 程序性记忆》，Agent 设计模式白皮书 v0.3，2026-07-30。</p>
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
<p><a href="https://adpsagent.com/zh/chronicle/#patterns-m5-procedural-memory">在 ADPS Chronicle 中查看</a></p>
</section>

<!-- PAGE-CHRONICLE:END -->
