<p style="font-size: 0.9rem; color: var(--color-text-faint); margin-bottom: 1.75rem;">
<a href="https://adpsagent.com/zh/patterns/" style="color: var(--color-text-muted);">模式矩阵</a>
<span style="margin: 0 0.45rem;">/</span>模式白皮书<span style="margin: 0 0.45rem;">/</span>A5
            </p>

<header class="publication-head">
<p class="publication-series">ADPS Agent 设计模式白皮书</p>
<h1>A5 · Minimal Tool Set · 最简工具集</h1>
<p class="publication-deck">按当前任务缩小可见工具集，通过合并、下沉和按需加载减少选择干扰。</p>
</header>

<table>
<tbody>
<tr>
<td style="text-align: left;"><strong>坐标</strong></td>
<td style="text-align: left;">行动 Action × 约束 constraint（跨切，不属于任何单一拓扑）</td>
</tr>
<tr>
<td style="text-align: left;"><strong>成本</strong></td>
<td style="text-align: left;">低（砍工具本身省 token，是净收益）</td>
</tr>
<tr>
<td style="text-align: left;"><strong>模式组</strong></td>
<td style="text-align: left;">行动模式</td>
</tr>
<tr>
<td style="text-align: left;"><strong>模式简介</strong></td>
<td style="text-align: left;">按当前任务缩小可见工具集，通过合并、下沉和按需加载减少选择干扰。</td>
</tr>
</tbody>
</table>

---

## 问题

工具注册表持续膨胀后，名称相近、参数重叠的工具会争夺模型注意力。面对“我的订单什么时候到”这类问题，Agent 可能在多个订单工具之间反复试错，把推理预算花在选择接口上。

Minimal Tool Set 要求每次 dispatch 只暴露完成当前任务所需的工具。工具总量可以很大，但默认候选集应按角色、任务阶段和权限动态缩小，并通过 Tool Search 按需扩展。

## 坐标说明：行动 × 约束

这是本模块里唯一一个不落在具体拓扑列上的模式，需要专门说清楚。

- **纵轴 · 行动**：它管的是行动端的工具数量，属于动作设计，所以纵轴落在行动模块。
- **横轴 · 约束**：最简工具集不规定动作的拓扑结构，而是限制单次可见工具总量。它作为 cross-cutting 约束附着在 A1 等结构模式上，减少 router 的选择空间和 schema 对 context 的占用。

## 解决方案与机制

工具名称、描述和 schema 会占用 context，也会增加近义工具之间的选择干扰。可见工具数没有跨模型、跨任务通用的甜区，应在固定回放集上逐步增加候选工具，找到选择质量、覆盖率和 token 开销开始恶化的拐点。

砍工具的策略有三条：

<table>
<thead>
<tr>
<th style="text-align: left;">策略</th>
<th style="text-align: left;">做法</th>
</tr>
</thead>
<tbody>
<tr>
<td style="text-align: left;">删低频</td>
<td style="text-align: left;">长期未使用的工具进入下线评审，而不是永久占用默认候选集</td>
</tr>
<tr>
<td style="text-align: left;">合并相似</td>
<td style="text-align: left;">语义与参数高度重叠的工具进入合并评审（如 query_order_detail / query_order_status / query_logistics 合成 query_order）</td>
</tr>
<tr>
<td style="text-align: left;">下沉次要</td>
<td style="text-align: left;">低频但有用的工具（OCR、PDF 解析、图片翻译）放进专门的 sub-agent</td>
</tr>
</tbody>
</table>

渐进披露（progressive disclosure）用于保留低频工具的可达性：核心工具常驻，扩展工具通过 Tool Search 或专门 sub-agent 按需加载。具体默认集合由角色、阶段、权限和回放数据确定。

## 适用场景

- **延迟敏感、准确率敏感的用户体验场景**：客服、对话、消费级 agent。这是 Minimal Tool Set 价值最高的地方。
- **接入外部工具协议时控制单次暴露**：底层目录可以很大，但单次 dispatch 只暴露当前任务需要的候选，并保留罕见工具的发现入口。
- **多职能 agent 拆分前的体检**：当一个 agent 的工具逼近上限，往往是该拆 sub-agent 的信号。

什么时候不适用：复杂代码任务或多职能企业流程可能需要更宽的工具面。若精简后任务覆盖率下降，应改用动态发现和角色分组，而不是追求固定数量。

## 已知失效方式

- **把“全能”当目标**：按系统能力罗列工具会让候选集持续膨胀。应围绕用户任务和结果组织工具，并按阶段缩小范围。
- **合并时丢了语义边界**：把语义差别大的工具硬合成一个，会让单个工具的 description 变模糊，selection 反而更难。合并的前提是功能真的高度重叠。
- **删除低频工具但没有按需入口**：罕见任务将无法访问相应能力。应将低频工具下沉，并保留 Tool Search。
- **砍完不复盘**：工具集会随新功能重新膨胀，需要固定 review 和 evict 机制。

## 验证指标

- **单 dispatch 工具数**：按任务类型观察实际候选集规模，并通过消融实验找到质量开始下降的拐点。
- **tool description 总 token**：跟踪工具说明占用的 context，并与选择错误、重试和延迟一起分析。
- **默认装载 / 总工具比**：默认候选应保持聚焦，罕见能力通过 on-demand 发现。比例需根据角色与任务分布校准。
- **工具选择准确率**：在同一回放集上比较精简前后，避免只看工具变少而忽略任务覆盖率。

## 最小实现

```
prune(all_tools, stats, policy):
    对每个 tool 打分 = 本地观察窗口内的调用价值、成功率与风险
    按 policy 选择常驻工具，其余转为按需
evict_stale(stats):
    返回长期无有效调用的工具            # 下线候选，仍需人工评审
merge_similar(tools, merge_threshold):
    用 embedding 计算 description 相似度，超过本地阈值时进入合并评审
# 其余工具不删除，转入 sub-agent + 挂到 Tool Search 入口
```

生产实现将 core 工具设为 always-on、extended 工具设为 on-demand；按使用频次和成功率评分；保留 Tool Search 入口。

## 场景化示例

设想一个翻译和本地化 Agent，默认只暴露 translate、detect\_lang、glossary\_lookup、quality\_check、format\_preserve 和 cultural\_adapt 等核心能力。OCR、PDF 解析和图片翻译按输入形态下沉到专用 sub-agent；长期未使用的工具进入下线评审；相似工具接受合并审查；罕见任务通过 Tool Search 临时获取扩展工具。改造效果应在固定回放集上同时比较选择准确率、覆盖率、token 和延迟。

## 相邻模式

- **工具调度（A1）**：A1 负责在候选集中选择工具，A5 负责控制候选集规模。
- **分层保留（记忆模块）**：渐进披露与记忆模块的分层加载同源，都是"核心常驻、其余按需取"的 attention 管理思路。
- **规划-执行（A2）**：当工具逼近上限，拆 sub-agent 往往与 A2 的任务分解同时发生——把次要能力连同它的工具一起下沉。

## 工程判断

最简工具集按当前步骤、身份和风险缩小候选工具范围。这样可以减少选择冲突、上下文占用和越权面，同时保留后续步骤加载其它工具的能力。

## 企业证据

<p class="evidence-empty">当前没有与本模式绑定的公开评审案例。模式定义不因此视为已经获得企业验证。</p>

<p style="font-size: 0.88rem; color: var(--color-text-muted);">案例收录要求说明业务约束、实现结构、已知失败和迁移边界。参见 <a href="https://adpsagent.com/zh/join/">贡献与评审规则</a>。</p>

## 开源实现

[**DeerFlow Guardrail 与双层授权**](https://adpsagent.com/zh/cases/deerflow-guardrail/)按五个公开 PR 展开装配时过滤、运行时授权、可信身份、RBAC 与 RunJournal 的演进，并标出该实现对本模式的覆盖范围。

<div class="document-citation">
<p><strong>引用建议：</strong>ADPS，《A5 最简工具集》，Agent 设计模式白皮书 v0.3，2026-07-30。</p>
<p><a href="https://adpsagent.com/zh/patterns/">模式目录</a> · <a href="https://github.com/huangjia2019/agent-design-patterns" rel="noopener" target="_blank">参考实现</a> · <a href="https://creativecommons.org/licenses/by/4.0/" rel="license noopener" target="_blank">CC BY 4.0</a></p>
<p class="publication-disclaimer"><strong>文档状态：</strong>本页为公开评审稿。模式定义与分类可供讨论和引用；场景化示例用于说明机制，不代表已经核验的企业案例。具名实践另见<a href="https://adpsagent.com/zh/cases/">案例库</a>。ADPS 欢迎业界提交带来源、测量口径和发布授权的案例。</p>
</div>

<!-- PAGE-CHRONICLE:START -->

<section aria-labelledby="page-chronicle-title" class="page-chronicle">
<h2 id="page-chronicle-title">溯源记录</h2>
<dl>
<div><dt>来源记录</dt><dd>ADPS 模式白皮书；先行工作与参考资料见正文</dd></div>
<div><dt>本页首次公开</dt><dd><time datetime="2026-07-18">2026-07-18</time></dd></div>
</dl>
<p><a href="https://adpsagent.com/zh/chronicle/#patterns-a5-minimal-tool-set">在 ADPS Chronicle 中查看</a></p>
</section>

<!-- PAGE-CHRONICLE:END -->
