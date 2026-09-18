<p style="font-size: 0.9rem; color: var(--color-text-faint); margin-bottom: 1.75rem;">
<a href="https://adpsagent.com/zh/patterns/" style="color: var(--color-text-muted);">模式矩阵</a>
<span style="margin: 0 0.45rem;">/</span>模式白皮书<span style="margin: 0 0.45rem;">/</span>M1
            </p>

<header class="publication-head">
<p class="publication-series">ADPS Agent 设计模式白皮书</p>
<h1>M1 · Hierarchical Retention · 分层保留</h1>
<p class="publication-deck">按作用域、功能类型和访问成本组织 Agent 记忆，并用显式的准入、晋升、降级和退出规则维护当前工作集。</p>
</header>

<table>
<tbody>
<tr>
<td style="text-align: left;"><strong>坐标</strong></td>
<td style="text-align: left;">记忆 Memory × 层级 Hierarchy（分）</td>
</tr>
<tr>
<td style="text-align: left;"><strong>成本</strong></td>
<td style="text-align: left;">中（多层存储与加载开销）</td>
</tr>
<tr>
<td style="text-align: left;"><strong>模式组</strong></td>
<td style="text-align: left;">记忆模式</td>
</tr>
<tr>
<td style="text-align: left;"><strong>模式简介</strong></td>
<td style="text-align: left;">按作用域、功能类型和访问成本组织 Agent 记忆，并用显式的准入、晋升、降级和退出规则维护当前工作集。</td>
</tr>
</tbody>
</table>

---

## 问题

Agent 启动时需要加载不同作用域的信息：公司安全政策长期适用于全员，用户偏好随用户保留，会话进度只在当前任务有效，工具结果通常一轮后过期。将这些信息全部写入同一个 prompt，容易超出 token 预算，也会降低关键信息的可见性。

分层保留把几种容易混在一起的关系拆开：作用域决定谁可以看到，功能类型决定内容怎样使用，访问层决定存取成本。Agent 只把当前任务需要的 working set 装入 context，其余内容保留引用并按需读取。

## 坐标说明：记忆 × 层级

- **纵轴 · 记忆**：该模式管理跨会话、跨用户和跨项目的信息，对应 working、session 和 long-term 等记忆层级。
- **横轴 · 层级**：各层存在作用域和覆盖关系。外层提供默认值，内层可以覆盖外层；数据可在 hot、warm 和 cold 层之间迁移。

## 解决方案与机制

1. **先标作用域**：使用 `user / project / team / tenant / organization / session / turn` 决定所有者、可见范围和写权限。作用域不能随着内容进入热缓存而扩大。
2. **再分功能类型**：区分 working、episodic、semantic、procedural 和 meta-memory。它们分别服务当前任务、历史事件、稳定知识、已验证流程和系统自我记录，读取触发点并不相同。
3. **最后选择访问层**：根据延迟、频率、容量和成本，把内容放入 hot、warm 或 cold 层。每层可以使用不同后端，也可以在同一后端中采用不同索引、TTL 和加载策略。
4. **按预算组装 working set**：启动时加载稳定规则和必要目标，任务运行中再按需读取会话、项目和长期内容。每个来源有独立预算，低优先级历史不能挤掉目标、约束和当前证据。
5. **用多因素控制升降级**：命中频次只能说明常用，不能说明正确。晋升和保留评分至少考虑 recency、usefulness、reliability、risk 和 review status。安全政策、撤销名单等低频高风险内容使用硬保留规则，不参与普通淘汰。
6. **分离读取与发布路径**：在线 Agent 可以实时读取，也可以把新内容写入候选区。进入项目级、用户级或组织级活动记忆前，需要经过 schema、来源、作用域、冲突和风险检查，并以新版本发布，保留替代关系和回滚点。

## 适用场景

- **跨会话、跨用户、跨项目复用的 agent**：编程教练、长期助手、企业内部 agent，需要记得"这个用户是谁、这个项目在干嘛、上次聊到哪"。
- **多租户 SaaS agent**：作用域分层天然带来隔离，用户 A 的偏好不会污染用户 B 的会话，项目 X 的规则不会带到项目 Y。金融、医疗、合同审阅这类不能容忍租户串数据的场景尤其依赖这一点。
- **企业级开发者 agent**：Claude Code 的多层 CLAUDE.md 就是这个模式，写 CLAUDE.md 的人本身在做记忆架构师，把安全规则、个人偏好、项目规则分别放在不同层。

## 已知失效方式

- **把不同分层维度画成一棵树**：作用域、功能类型和访问层回答不同问题。把三者压成 user / project / session 一条层级后，权限、内容用途和冷热迁移会互相牵制。
- **用户层缺少 schema**：如果 Agent 用自由文本记录“小李会装饰器”，同一概念会逐渐产生多种写法，降低 retrieval 命中率。高频字段应使用 typed schema。
- **把命中率当正确率**：错误记忆被反复使用后会得到更高评分，形成自我强化。晋升必须同时检查来源可靠性、任务结果和审核状态。
- **淘汰低频高风险规则**：安全政策、合规约束和撤销名单可能长期不命中，但一旦需要就不能缺席。这类内容应使用独立保留策略。
- **全部按启动注入设计**：用户层和项目层适合启动注入，会话层适合渐进读取，临时层适合实时拼装。三种 access pattern 混成一种后，会话越长，历史内容越容易挤占当前任务的上下文预算。
- **完全无状态的场景强行分层**：单次问答、一次性 ETL 转换不需要跨会话记忆。
- **运行期直接改写高层记忆**：线上任务中的临时判断未经确认就覆盖长期内容，错误会跨会话传播且难以复现。自动写入应先进入候选区，再由独立发布过程生效。
- **遗忘策略硬编码**：设备信号、合规记录和长期偏好的保留目标不同。TTL、衰减、压缩、归档和删除应按记忆类型与业务政策配置。
- **eviction 不留 reason log**：合规（GDPR right-to-be-forgotten）和 debug 都要求能证明"删了什么、为什么删、什么时候删"，没有日志就证明不了。

## 验证指标

- **Working set 命中率**：Agent 推理所需记忆进入 prompt 的比例。应按任务类型建立本地基线，并结合遗漏证据判断分层或加载策略是否有效。
- **每层 token 占比**（按预算分配）：各层加载到 prompt 的 token 是否在预算内。某层持续超预算，说明该层需要截断或下沉到按需加载。
- **跨层污染事件**：是否出现用户层被单次会话信息污染或租户之间串数据。多租户系统应将任何此类事件按安全事故处理。
- **错误晋升率与人工驳回率**：抽查从候选区进入长期活动集的记录，统计错误作用域、错误事实和低质量概括。
- **过期记忆使用率**：已被新版本替代或超出有效时间的内容仍参与决策的比例。
- **高风险规则保留完整率**：对硬保留内容执行周期性清点，确认没有被普通衰减策略移出可用集。
- **各访问层的命中与延迟**：观察 hot、warm、cold 的召回分布和读取时延，用任务结果判断层级策略是否有效。
- **启动 token 总量**：与未分层的历史加载基线比较，同时检查关键信息是否仍然可见。

## 最小实现

```
MemoryRecord:
    id / kind / scope / source / valid_from / valid_to
    supersedes / trust_status / risk / retrieval_keys

write(candidate):
    validate schema + provenance + scope + sensitive data
    detect conflict and assign candidate|accepted|rejected
    publish accepted record as a new version

read(task):
    enforce tenant and scope filters
    exclude expired and superseded versions
    rank by task relevance + usefulness + reliability + risk
    assemble within per-source token budgets

retire(record):
    decay, archive, revoke, or delete by policy
    append reason + actor + timestamp to audit log
```

后端选择服务于访问特征，不定义记忆语义。即使所有记录暂时放在同一个数据库里，scope、kind、validity 和 trust 也要保持独立字段。

## 场景化示例

设想一个薪酬 SaaS 的执行型 Agent 采用三层记忆。L1 保存当前步骤所需的最小信息集；L2 保存里程碑日志，包括任务进度和刚完成的动作；L3 保存跨任务可复用的判断和流程。三层分别覆盖当前步骤、当前任务和跨任务三个时间尺度。每层有独立的 token 预算，L1 在运行时组装，L3 写入前执行信任校验，避免单次偶然信息进入长期记忆。

## 相邻模式

- **进度追踪（M3）**：Todo list 位于高频更新的会话层，每轮推理都需要读取。
- **RAG（M2）**：分层保留按作用域加载长期已知信息，RAG 按需检索无法常驻 context 的大规模知识。
- **失败日记（M4）/ 程序性记忆（M5）**：两者可以作为长期记忆中的专用分区，分别保存失败记录和已验证流程。
- **语义压缩（感知模块）**：会话层接近 token 上限时，可通过语义压缩减少单层占用。
- **记忆准入（候选）**：M1 规定各层边界，记忆准入负责判断一条候选内容能否进入某个活动层。

## 工程判断

分层保留管理 Agent 的 working set。作用域保证隔离，功能类型决定用途，访问层控制成本，版本与准入防止一次临时判断直接变成长期事实。

## 企业证据

以下现场记录说明该模式在具体业务约束下如何实现。案例结论只在文中声明的系统边界内成立。

<ul style="list-style: none; margin: 0.5rem 0 1rem 0; padding: 0;">
<li style="margin-bottom: 0.6rem; line-height: 1.55;"><a href="https://adpsagent.com/zh/patterns/m1-hierarchical-retention/cases/liangbo/" style="font-weight: 600;">东方屹腾 · 分层保留</a><span style="color: var(--color-text-muted);"> — L1 保存当前输入，L2 保存任务事实，L3 保存跨任务经验并回指原始记录。</span></li>
</ul>

<p style="font-size: 0.88rem; color: var(--color-text-muted);">案例收录要求说明业务约束、实现结构、已知失败和迁移边界。参见 <a href="https://adpsagent.com/zh/join/">贡献与评审规则</a>。</p>

<!-- PATTERN-ENGINEERING-RELATED:START -->

<section aria-labelledby="related-memory-engineering" class="related-case-band">
<p class="related-case-label">模式工程实现</p>
<h2 id="related-memory-engineering"><a href="https://adpsagent.com/zh/patterns/engineering/memory-storage-on-kubernetes/">K8s 中的 Agent 记忆：存储分层与恢复验证</a></h2>
<p>把本模式放进多 Pod 服务，检查权威存储、版本冲突、检索索引和恢复路径。</p>
</section>

<!-- PATTERN-ENGINEERING-RELATED:END -->

<div class="document-citation">
<p><strong>引用建议：</strong>ADPS，《M1 分层保留》，Agent 设计模式白皮书 v0.3，2026-07-30。</p>
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
<p><a href="https://adpsagent.com/zh/chronicle/#patterns-m1-hierarchical-retention">在 ADPS Chronicle 中查看</a></p>
</section>

<!-- PAGE-CHRONICLE:END -->
