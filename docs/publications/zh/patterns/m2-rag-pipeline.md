<p style="font-size: 0.9rem; color: var(--color-text-faint); margin-bottom: 1.75rem;">
<a href="https://adpsagent.com/zh/patterns/" style="color: var(--color-text-muted);">模式矩阵</a>
<span style="margin: 0 0.45rem;">/</span>模式白皮书<span style="margin: 0 0.45rem;">/</span>M2
            </p>

<header class="publication-head">
<p class="publication-series">ADPS Agent 设计模式白皮书</p>
<h1>M2 · RAG Pipeline · 检索增强生成</h1>
<p class="publication-deck">将大规模知识源组织为带来源、版本和权限的多路索引，并由检索 Harness 按任务完成查询、导航、重排和证据装配。</p>
</header>

<table>
<tbody>
<tr>
<td style="text-align: left;"><strong>坐标</strong></td>
<td style="text-align: left;">记忆 Memory × 链式 Chain（传）</td>
</tr>
<tr>
<td style="text-align: left;"><strong>成本</strong></td>
<td style="text-align: left;">中（索引 + 检索 + 可选重排）</td>
</tr>
<tr>
<td style="text-align: left;"><strong>模式组</strong></td>
<td style="text-align: left;">记忆模式</td>
</tr>
<tr>
<td style="text-align: left;"><strong>模式简介</strong></td>
<td style="text-align: left;">将大规模知识源组织为带来源、版本和权限的多路索引，并由检索 Harness 按任务完成查询、导航、重排和证据装配。</td>
</tr>
</tbody>
</table>

---

## 问题

企业知识库包含大量文档、工单、日志和业务对象，无法常驻 LLM 的 context window。RAG 在写入侧建立可追溯索引，在读取侧按当前任务检索证据，并将 input 之外的事实临时加入 context。

生产级 RAG 除了单次召回，还要处理查询改写、反例检索和跨语料验证。Agent 可以评估首轮结果，在证据不足时修改 query，并对候选结论执行反向查询。

## 坐标说明：记忆 × 链式

- **纵轴 · 记忆**：RAG 管理 declarative knowledge，将 input 之外的事实按需加载到当前 context。
- **横轴 · 链式**：原始材料依次经过解析、标注、索引；在线请求依次经过查询规划、过滤、召回、融合、重排和证据装配。Agent 可以在证据不足时改写 query 再走一轮，公开矩阵仍以这条链式主干作为唯一坐标。

## 解决方案与机制

1. **写入侧先治理再建索引**：解析文档、日志和结构化对象时，同时记录 source、owner、permission、valid time、version 和原文位置。chunk 与摘要是派生产物，不能丢掉原文指针。
2. **建立多路入口**：正文、摘要、实体、时间事件、标识符和关系路径可以建立不同索引。错误码、ID 和专有名词优先精确匹配或结构化查询；开放语义问题使用 BM25、向量检索和重排；关系问题使用图或导航。
3. **由 Retrieval Harness 选择路径**：`EvidenceRequest` 描述问题、时间范围、作用域和证据要求。Harness 决定执行 search、browse、navigate、lookup 或直接读取编译产物，并记录选择过程。
4. **权限、时间和版本过滤前置**：先排除无权访问、已经失效或被新版本替代的内容，再执行融合和重排。相似度不能把过期制度重新抬回当前上下文。
5. **输出证据包而不是文本堆**：返回 `EvidenceBundle`，其中包含支持证据、反例、来源位置、版本、置信信息和 `RetrievalTrace`。生成阶段可以判断证据是否充分，也可以明确拒答。
6. **允许有界的多步检索**：复杂问题可以拆分子 query、改写查询、寻找反例和跨语料验证。轮数、token、工具调用和总时长都要设置上限。

## 适用场景

- **大规模自然语言知识库**：学术文献综述、法律案例库、客服 FAQ。数据量大、包含同义词和隐含关系、更新频率可控时，适合采用 RAG。
- **跨多文档的复杂查询**：需要从多个来源综合答案、需要可追溯引用的场景。
- **企业 know-how 组织**：将 wiki、Confluence、Slack、邮件和工单中的知识统一治理，使 Agent 能按任务检索。

## 已知失效方式

- **知识源未经治理**：wiki 文档互相矛盾、关键决策缺失、版本过期或同义词未统一时，建索引只会让这些问题更容易被召回。
- **把所有数据强行向量化**：精确标识符、结构化字段和版本条件在向量检索中容易失真。检索侧至少要保留精确全文、结构化查询和原文读取能力。
- **编译产物脱离原文**：摘要、Wiki 或实体关系更新后无法回到原始位置，系统就无法证明结论来源。
- **静态文档与动态事件共用一种切分**：制度文档、会话记录和工具事件的粒度、更新时间和有效期不同，统一 chunk 策略会造成延迟或语义断裂。
- **检索工具增加但调度策略不收敛**：search、browse、图查询和直接读取同时暴露，Harness 却不记录为什么选择某条路径，失败后无法判断问题出在查询规划、索引、重排还是阅读。
- **索引时效跟不上任务**：代码和高频业务状态可能在索引完成前已经变化。需要当前工作区真值时，应直接查询 live source，例如仓库搜索、数据库或业务 API。
- **停留在一查一答**：第一次没查到关键信息时，naive RAG 要么直接说不知道，要么 silently 编造。生产级 RAG 必须能改写 query 再查。
- **只优化召回精度**：embedding 模型的离线分数无法代替查询改写和证据验证。召回指标改善后，仍需评估最终答案的正确性、完整性和引用质量。
- **引用不可追溯**：学术、法律、医疗场景里，每个结论都要能追到原始 chunk 加页码，这是合规的必要条件。

## 验证指标

- **索引覆盖与时效**：应进入当前版本的材料是否已被解析、标注和发布，更新延迟是否满足业务窗口。
- **检索失败率**：候选中没有相关证据的比例。应在同一评测集上分别定位 indexing、retrieval 和 filtering 问题。
- **证据使用率 / 引用率**：召回内容中实际被 Agent 使用并引用的比例。偏低时检查候选噪声、query 粒度、版本过滤和重排策略。
- **阅读正确率**：正确证据已经进入 context 后，模型是否仍然读错、忽略限制条件或引用了相邻段落。
- **多步检索轮数**：记录迭代检索的实际轮数并设置硬上限。经常顶到上限，可能是任务需要拆分、知识源缺失或首轮召回质量不足。
- **Trace 完整率**：每条公开结论是否能回到查询、候选、过滤原因、原始文档位置和版本。
- **最终综合质量**（业务判定）：由领域专家按照正确性、完整性和引用质量评估 Agent 输出；达到业务设定阈值后再进入生产流程。

## 最小实现

```
写入侧：
    source → parse → chunk/event/entity
           → annotate(source, owner, permission, valid_time, version)
           → full-text + vector + structured/graph indexes + original pointer

读取侧：
    EvidenceRequest(question, scope, time_range, evidence_policy)
      → Retrieval Harness 选择 lookup/search/browse/navigate/read
      → permission + valid-time + version filter
      → exact/BM25/vector/graph candidates
      → fuse + rerank + evidence-sufficiency check
      → EvidenceBundle(support, counter_evidence, citations, trace)

若证据不足：改写或拆分 query，受 max_rounds / token / time 约束
```

生产实现要把索引发布与在线查询分开观测。一次错误答案至少能被定位为知识源、编译、过滤、召回、重排、阅读或合成中的一个阶段。

## 场景化示例

设想一个学术文献综述 Agent。只用关键词时，候选范围过宽；只用 embedding 时，结果又集中在已有主题簇，较新的交叉研究和反例容易被漏掉。后续版本先拆分研究问题，再执行迭代改写、反例检索和跨语料验证；peer-reviewed 论文、预印本和内部材料分库管理，证据权重由机构自己校准；每条结论都定位到原始 chunk、页码和版本。这个场景的重点是证据链与索引治理，不能用一个脱离评测集的“召回提升”数字代替。

## 相邻模式

- **分层保留（M1）**：M1 按作用域加载长期已知信息，RAG 按需检索无法常驻 context 的大规模知识。
- **程序性记忆（M5）**：RAG 检索 declarative memory，M5 复用 procedural memory。
- **上下文分诊（感知模块）**：RAG 产生候选片段，上下文分诊决定候选片段的加载优先级。
- **渐进发现（感知模块）**：渐进发现用于探索陌生信息空间的结构，RAG 用于从已建立索引的知识库中召回片段。
- **知识编译（候选）**：M2 关注当前任务怎样取得证据，知识编译关注原始材料怎样在写入侧形成可导航、可检索的资产。

## 工程判断

RAG 是一条证据供应链。知识源、索引、检索调度、版本过滤、阅读和引用中的任一环节失真，最后的生成都可能看起来流畅却无法成立。

<!-- ADPS-BLUEBOOK-SLOT -->

<!-- PATTERN-ENGINEERING-RELATED:START -->

<section aria-labelledby="related-memory-engineering" class="related-case-band">
<p class="related-case-label">模式工程实现</p>
<h2 id="related-memory-engineering"><a href="https://adpsagent.com/zh/patterns/engineering/memory-storage-on-kubernetes/">K8s 中的 Agent 记忆：存储分层与恢复验证</a></h2>
<p>把本模式放进多 Pod 服务，检查权威存储、版本冲突、检索索引和恢复路径。</p>
</section>

<!-- PATTERN-ENGINEERING-RELATED:END -->

<div class="document-citation">
<p><strong>引用建议：</strong>ADPS，《M2 检索增强生成》，Agent 设计模式白皮书 v0.3，2026-07-30。</p>
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
<p><a href="https://adpsagent.com/zh/chronicle/#patterns-m2-rag-pipeline">在 ADPS Chronicle 中查看</a></p>
</section>

<!-- PAGE-CHRONICLE:END -->
