<p style="font-size: 0.9rem; color: var(--color-text-faint); margin-bottom: 1.75rem;"><a href="https://adpsagent.com/zh/patterns/" style="color: var(--color-text-muted);">模式矩阵</a><span style="margin:0 0.45rem;">/</span><a href="https://adpsagent.com/zh/patterns/m1-hierarchical-retention/" style="color: var(--color-text-muted);">M1 分层保留</a><span style="margin:0 0.45rem;">/</span>蓝皮书</p>

<header class="publication-head">
<p class="publication-series">ADPS 企业 Agent 系统蓝皮书 · 模式实践切片</p>
<h1>M1 · 分层保留 · 东方屹腾执行型 Agent</h1>
<p class="publication-deck">L1 保存当前输入，L2 保存任务事实，L3 保存跨任务经验并回指原始记录。</p>
</header>

<table>
<thead>
<tr>
<th style="text-align: left;">字段</th>
<th style="text-align: left;">值</th>
</tr>
</thead>
<tbody>
<tr>
<td style="text-align: left;">主模式</td>
<td style="text-align: left;">M1 分层保留 Hierarchical Retention（记忆 × 层级）</td>
</tr>
<tr>
<td style="text-align: left;">结合模式</td>
<td style="text-align: left;">M4 失败日记 · M3 进度追踪</td>
</tr>
<tr>
<td style="text-align: left;">案例</td>
<td style="text-align: left;">上海东方屹腾科技 · HR/薪酬 SaaS · 服务 2 万+ 企业 · 执行型 Agent</td>
</tr>
<tr>
<td style="text-align: left;">对应白皮书</td>
<td style="text-align: left;"><a href="https://adpsagent.com/zh/patterns/m1-hierarchical-retention/">/zh/patterns/m1-hierarchical-retention/</a></td>
</tr>
<tr>
<td style="text-align: left;">源</td>
<td style="text-align: left;">梁博 AICon 逐字稿第七章 · PPT 第 26–27 页</td>
</tr>
<tr>
<td style="text-align: left;">工程结论</td>
<td style="text-align: left;">L1 保存当前输入，L2 保存任务事实，L3 保存跨任务经验；L3 只在关键推理边界召回，并通过 ID 回指 L2 原始事实。</td>
</tr>
</tbody>
</table>

---

## 场景约束

薪资组配置、算薪、代发和员工入职等任务会跨十余次模型调用。当前步骤、当前任务和历史任务需要不同粒度的信息。若全部放入同一上下文，成本和噪声会随任务长度增加；若只保留摘要，审计时又无法核对原始事实。

## 分层模型

| 层级 | 内容 | 存储 | 访问方式 |
| --- | --- | --- | --- |
| L1 | 当前推理所需的最小上下文 | 内存 | 直接注入 |
| L2 | 当前任务的里程碑和原始事实 | 关系型数据库 | 按任务或 ID 精确读取 |
| L3 | 从成功和失败中提炼的经验 | 向量数据库 | 按语义相似度召回 |

L3 条目保存对应的 L2 事实 ID。检索阶段先返回经验摘要；需要确认形成经验的具体条件时，再按 ID 读取 L2。这种按引用加载的方式与操作系统内存分页的原则相近。

## 写入流程

L2 在关键里程碑完成时追加事实。L3 在任务成功或失败后由反思流程生成，内容包括：

- 适用的任务类型和前置条件；
- 采用的 Skill 或处理策略；
- 成功结果或失败原因；
- 下次执行建议；
- 来源任务、L2 事实 ID 和生成版本；
- 可信度、审核状态和失效条件。

L3 写入前应执行去重和可信度校验。一次偶发结果不能直接升级为长期经验；失败原因未确认时，可以先保留为待验证条目。

## 召回边界

L3 集中在三类入口召回：

1. 链式推理首次调用；
2. ReAct 首轮；
3. 任务规划开始前。

链路中间的常规步骤使用当前任务状态，不重复检索 L3。召回结果进入 ReasonContext，并与 Anchor 同时呈现。历史经验只提供候选判断，不能覆盖当前用户目标和实时健康状态。

## 案例运行

若以往薪资组配置已经验证某个 Skill 有效，新任务可以优先评估该 Skill。若历史任务在某 API 处失败，规划器可以在正式流程前插入健康检查节点。健康检查的当前结果仍是执行依据，历史失败记录不直接阻断任务。

## 失效信号

- 每个推理步骤都查询 L3；
- L3 保存整段原始日志，没有可复用判断；
- L3 没有来源引用，无法回到 L2 核对；
- 单次偶发结果未经验证便写入长期经验；
- 相似经验覆盖当前 Anchor；
- L1 持续累积历史内容，失去最小上下文属性。

## 验证指标

- L3 在关键入口以外的额外召回次数；
- 正向经验命中后的规划收敛时间；
- 负向经验触发健康检查后避免的无效前序执行；
- L3 命中准确率、过期率和人工驳回率；
- L3 到 L2 来源引用的完整率；
- 分层后的 Token、延迟和存储成本。

## 与白皮书的对应

M1 白皮书要求按作用域和时间尺度分层，并为每层选择独立后端。东方屹腾用数据库承载 L2 精确事实，用向量索引承载 L3 语义检索，并以 ID 完成按需加载。

## 迁移条件

同类任务会重复出现、历史成功或失败能够改变新计划、且前序执行成本较高时，L3 具有实际收益。一次性任务或相似度很低的任务可以先实现 L1 和 L2，不必建设经验向量库。

<div class="document-citation">
<p><strong>引用建议：</strong>ADPS、梁博，《东方屹腾 · 分层保留》，企业 Agent 系统蓝皮书 v0.4，2026-08-02。</p>
<p><a href="https://adpsagent.com/zh/cases/">案例报告目录</a> · <a href="https://adpsagent.com/zh/patterns/">模式目录</a> · <a href="https://creativecommons.org/licenses/by/4.0/" rel="license noopener" target="_blank">CC BY 4.0</a></p>
<p class="publication-disclaimer"><strong>证据边界：</strong>本页是完整案例的模式切片，记录特定系统约束下的实现选择。案例方提供的实现与效果信息未经过独立审计，不构成通用性能承诺。</p>
</div>

<!-- PAGE-CHRONICLE:START -->

<section aria-labelledby="page-chronicle-title" class="page-chronicle">
<h2 id="page-chronicle-title">溯源记录</h2>
<dl>
<div><dt>来源记录</dt><dd><a href="https://adpsagent.com/zh/cases/liangbo-execution-agent/">东方屹腾执行型 Agent 案例</a>；案例提供：梁博</dd></div>
<div><dt>来源日期</dt><dd><time datetime="2026-06-19">2026-06-19</time></dd></div>
<div><dt>本页首次公开</dt><dd><time datetime="2026-07-30">2026-07-30</time></dd></div>
</dl>
<p><a href="https://adpsagent.com/zh/chronicle/#patterns-m1-hierarchical-retention-cases-liangbo">在 ADPS Chronicle 中查看</a></p>
</section>

<!-- PAGE-CHRONICLE:END -->
