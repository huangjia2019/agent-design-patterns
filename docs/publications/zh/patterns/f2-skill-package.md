<p style="font-size: 0.9rem; color: var(--color-text-faint); margin-bottom: 1.75rem;">
<a href="https://adpsagent.com/zh/patterns/" style="color: var(--color-text-muted);">模式矩阵</a>
<span style="margin: 0 0.45rem;">/</span>模式白皮书<span style="margin: 0 0.45rem;">/</span>F2
            </p>

<header class="publication-head">
<p class="publication-series">ADPS Agent 设计模式白皮书</p>
<h1>F2 · Skill Package · 技能包</h1>
<p class="publication-deck">将反复验证成功的工作流封装为可命名、可加载、可版本化的 skill，并用完整发布周期管理它的进入、共存、回滚和退役。</p>
</header>

<table>
<tbody>
<tr>
<td style="text-align: left;"><strong>坐标</strong></td>
<td style="text-align: left;">反思 Reflection × 路由 Route（选）</td>
</tr>
<tr>
<td style="text-align: left;"><strong>成本</strong></td>
<td style="text-align: left;">中高（封装、隔离评测、发布和持续维护）</td>
</tr>
<tr>
<td style="text-align: left;"><strong>模式组</strong></td>
<td style="text-align: left;">反思模式</td>
</tr>
<tr>
<td style="text-align: left;"><strong>模式简介</strong></td>
<td style="text-align: left;">将反复验证成功的工作流封装为可命名、可加载、可版本化的 skill，并用完整发布周期管理它的进入、共存、回滚和退役。</td>
</tr>
</tbody>
</table>

---

## 问题

Agent 可能反复完成同一类任务，却每次都从零开始：重读相同 reference，重复相同试错，再走一遍已经验证过的路径。根因是任务结束后没有留下可调用的能力资产。

Skill Package 把"做对的事"凝固成一份结构化资产，通常由 YAML frontmatter（name、description、triggers）、markdown body（steps、gotchas、examples）和 bundled scripts 组成。下次同类任务到来时，Agent 路由到对应 skill，直接加载主路径。它和 Generator-Critic 的区别在颗粒度：后者改的是单次输出，Skill Package 沉淀的是跨任务能力。ACT-R 认知架构把这件事称为 proceduralization，也就是将陈述性知识编译为程序性技能。

## 坐标说明：反思 × 路由

- **纵轴 · 反思**：Skill Package 将多次成功执行后提炼出的流程固化为资产，跨任务复用。
- **横轴 · 路由**：新任务根据 triggers 路由到匹配的 skill，未命中时进入通用流程。skill 内部仍可采用原子到复合的分层和 Discovery、Activation、Execution 三阶段加载。

## 解决方案与机制

一个 Skill Package 系统由两条流水线构成：

1. **加载流水线**：启动时只暴露 skill 的 name 和简短 description；任务命中后加载完整 `SKILL.md`；执行时再按需加载 bundled scripts。具体 context 开销由目录规模和 tokenizer 决定，应在本地测量。
2. **发布流水线**：一条路径由人编写并经过 review、版本管理和测试；另一条路径由 Agent 在出现足够的复用、复杂度和成功证据后辅助提炼。两条路径最终都要经过 candidate → 安全审查 → 隔离评测 → 共存评测 → 小流量试用 → 发布 → 监控 → 修订、合并或退役。

可操作的工程纪律包括：把关键约束放在醒目位置；能写成 deterministic script 的步骤不交给模型临场判断；提供 worked example；为 skill 配测试；持续查看使用和结果证据，清理过期或低价值资产。

隔离评测回答“这项 skill 单独能不能完成任务”，共存评测回答“它进入现有 skill 集合后会不会选错、抢占或互相干扰”。研讨会中提到的难点集中在第二问：一个 skill 单测通过，和其他 skill 同时加载后仍可能触发错误路由；最终结果变差时，还要判断问题来自主 Agent、skill 内容、触发描述，还是宿主 Harness。

## 适用场景

- **反复出现且流程相对稳定的任务**：运维 runbook（批量重启集群、配置变更）、客服分诊 SOP、销售标准流程——同类任务高频出现，流程不天天变。
- **需要可观测和复用的企业流程**：将隐性流程写入 SKILL.md，供员工和 Agent 使用，并支持 review 和版本管理。
- **错代价高、值得固化的关键流程**：金融审批流程、事故响应步骤这类做错代价大的流程，固化成 skill 比每次靠 agent 临场发挥稳。

## 已知失效方式

- **不稳定任务被固化为 skill**：开放域研究、一次性任务、快速变化流程和判断密集任务通常不适合固化。Skill Package 适用于重复出现、流程稳定且错误代价较高的任务。
- **skill library 污染**：Agent 自蒸馏的低质量 skill 不经 curation 直接进库，会在后续召回中误导其他 Agent。候选 skill 应进入低信任 namespace，经过回放、试用和人工评审后再发布。
- **skill 过期**：基础设施变了但 skill 没跟着改，agent 按过期 skill 执行反而错，运维场景尤其常见。防法是成功率监控加自动告警加版本绑定（SKILL.md 里标 tested\_with）。
- **description 失配**：description 写得太泛或太窄，agent 召回时挑错 skill 或该用没用。description 必须含具体场景，triggers 列表要够细。
- **隔离通过、共存退化**：新 skill 单独测试表现正常，进入生产目录后与既有 skill 争抢触发条件。发布前要跑组合任务和冲突用例，并保留快速回滚版本。
- **归因含混**：任务失败后只记录“skill 失败”，却没有保存路由候选、实际加载内容、模型版本和 Harness 版本，后续无法判断该改哪一层。

## 验证指标

- **skill 命中率**：任务到来时能否召回合适 skill。误召回和漏召回应分别归因到 description、triggers、索引或任务分类。
- **skill 成功率**：调用 skill 后任务是否通过验收。相对自身基线持续下降时，检查底层服务和流程是否变化。
- **library 健康度**：随着库增长，观察平均成功率、重复 skill 和失效版本。规模增长伴随质量下降通常说明 curation 不足。
- **加载 token 占比**：观察 discovery、activation 和 execution 各阶段占用，避免未命中的 skill 全量进入 context。
- **共存回归率**：比较新 skill 加入前后的误触发、漏触发、任务成功和 context 成本。
- **发布与回滚证据**：记录候选版本通过了哪些评测、何时进入试用、由谁批准，以及回滚是否恢复到已知状态。

## 最小实现

```
# Stage 1 Discovery: 启动只加载 name + description
catalog = [{"name": s.name, "desc": s.description} for s in library]

# Stage 2 Activation: 任务匹配后加载完整 SKILL.md
matched = top_k(task, library, k=activation_k)   # 在标注任务集上调参

# Stage 3 Execution: 按需加载 bundled scripts, 跟踪成功率
result = run(matched_skill, task)
mark_used(matched_skill, success=result.ok)

# 沉淀: Hermes 风格自动蒸馏 (多重过滤)
if distillation_policy.accepts(task, trace, outcome):
    skill = distill(task, tool_calls)   # 进试用期, 非直接投产

# 发布: 先单测，再验证与现有 skill 的共存
ISOLATED_EVAL(skill, held_out_tasks)
COEXISTENCE_EVAL(skill, active_library, conflict_cases)
PROMOTE(replay_passed and coexistence_passed and approval_granted)

# 运行期: 每次选择都保留归因证据
record_route(candidates, selected_skill, skill_version, harness_version, outcome)

# 生命周期管理
REFINE(usage_evidence_sufficient and quality_declining)
ROLLBACK(blocking_regression)
EVICT(no_effective_use and review_approved)
```

生产实现采用分阶段 loading；自动蒸馏 skill 经过试用期和回放后再转正；人工编写和自动蒸馏使用不同信任级别；隔离评测与共存评测都通过后才进入生产目录。每次调用保留路由和版本证据，出现阻断性回归时回滚到上一稳定版本。

## 场景化示例

设想一个 B2B SaaS 团队把资深销售的稳定做法整理为 SKILL.md：首次接触前查询公开公司信息，电话开场和需求发现使用可审查的流程，异议处理引用话术库，签约前发送决策清单。gotchas 放在文件顶部，确定性步骤使用 bundled scripts，每个环节提供 worked example。核心 SOP 由人工编写并经 sales leader review 后进入 git；自动蒸馏 skill 使用独立 namespace 和较低信任级别；customer-facing skill 必须人工审核；团队定期执行 EVICT、REFINE 或 PROMOTE。业务提升需要由真实销售数据另行验证。

## 相邻模式

- **Procedural Memory（记忆模块 M5）**：落地几乎同构，都是技能库、都用 SKILL.md 形态存程序性知识，区别在设计意图。Skill Package 强调"反思后封装"——agent 反复成功后主动把成功路径提炼固化（post-reflection）；M5 强调"学过就存"——把程序性知识作为记忆写入。前者是反思视角，后者是记忆视角，工程载体重合度很高。
- **Generator-Critic（F1）**：上下衔接。Generator-Critic 是单次任务内的反思，Skill Package 是跨任务的反思，把"做对的事"凝固下来。
- **Experience Replay（F3）**：Skill Package 保存经过验证的可调用单位，Experience Replay 保存范围更宽、未必完成验证的参考资产。运行时可优先匹配 skill，未命中时再检索 experience。
- **RAG（记忆模块）**：RAG 检索 declarative knowledge，Skill Package 复用 procedural knowledge。

## 工程判断

Skill Package 将经过验证的流程、工具和边界条件封装为可触发、可版本化的运行资产。组织可以复用稳定做法，同时保留输入判断、异常处理和退出条件。

## 延伸阅读

- [反思模块总纲：从运行反馈到受控修改](https://adpsagent.com/zh/patterns/reflection/)
- [反思模块第一次研讨会（2026-08-12）](https://adpsagent.com/zh/workshops/reflection-2026-08-12/)
- [Claude Enterprise Skills：测试、隔离、共存与生命周期](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/enterprise)

<!-- ADPS-BLUEBOOK-SLOT -->

<div class="document-citation">
<p><strong>引用建议：</strong>ADPS，《F2 技能包》，Agent 设计模式白皮书 v0.3，2026-07-30。</p>
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
<p><a href="https://adpsagent.com/zh/chronicle/#patterns-f2-skill-package">在 ADPS Chronicle 中查看</a></p>
</section>

<!-- PAGE-CHRONICLE:END -->
