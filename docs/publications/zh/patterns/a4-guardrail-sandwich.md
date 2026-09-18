<p style="font-size: 0.9rem; color: var(--color-text-faint); margin-bottom: 1.75rem;">
<a href="https://adpsagent.com/zh/patterns/" style="color: var(--color-text-muted);">模式矩阵</a>
<span style="margin: 0 0.45rem;">/</span>模式白皮书<span style="margin: 0 0.45rem;">/</span>A4
            </p>

<header class="publication-head">
<p class="publication-series">ADPS Agent 设计模式白皮书</p>
<h1>A4 · Guardrail Sandwich · 护栏三明治</h1>
<p class="publication-deck">在有副作用或高风险的动作前后执行 pre-check 和 post-check，控制准入并验证结果。</p>
</header>

<table>
<tbody>
<tr>
<td style="text-align: left;"><strong>坐标</strong></td>
<td style="text-align: left;">行动 Action × 层级 Hierarchy（分）</td>
</tr>
<tr>
<td style="text-align: left;"><strong>成本</strong></td>
<td style="text-align: left;">横切（跨切关注点，开销随风险分级浮动）</td>
</tr>
<tr>
<td style="text-align: left;"><strong>模式组</strong></td>
<td style="text-align: left;">行动模式</td>
</tr>
<tr>
<td style="text-align: left;"><strong>模式简介</strong></td>
<td style="text-align: left;">在有副作用或高风险的动作前后执行 pre-check 和 post-check，控制准入并验证结果。</td>
</tr>
</tbody>
</table>

---

## 问题

生产级 Agent 需要在动作执行前控制准入，并在执行后验证结果。设想一个对公转账 Agent 把邮件中的收款账号识别错误并直接提交。该流程缺少调用前的账号、金额和客户意图校验，也缺少调用后的到账与合规复核。

Guardrail Sandwich 为 destructive 动作增加结构化的事前和事后审查。风险包括目标劫持、工具误用、参数误识别和动作组合绕过；具体控制应映射到组织自己的威胁模型与合规要求。

## 坐标说明：行动 × 层级

- **纵轴 · 行动**：它包装的是 agent 的动作执行——在工具调用的前、中、后插入护栏，属于行动端的执行控制。
- **横轴 · 层级**：pre-guard → tool call → post-guard 是一个层级包装结构，与 Web 框架的 middleware 完全同源——一层夹一层，外层先于内层执行、后于内层收尾。它和规划-执行（A2）虽同涉分层，但方向不同：A2 是"战略-战术"分层（先想后干），A4 是"安全-执行"分层（先审后干）。

## 解决方案与机制

hook 可以统一包装不同工具，避免在每个工具中重复实现检查。Coding Agent 的生命周期 hook 中，与该模式直接相关的包括：

- **PreToolUse**：工具调用前触发，可以根据框架契约阻断、改参数或补充 context。典型用途包括路径 allowlist、命令 denylist、quota 检查和 approval gate。
- **PostToolUse**：工具调用后触发，不能 undo 已发生的动作，只能验证 output、提示下一步、触发审计或 saga 回滚。典型用例是 output schema 校验、敏感数据扫描、副作用确认。

落地有三条关键纪律：

- **按 risk\_level 分级**：只读、普通写入、destructive 和 CRITICAL 动作使用不同检查组合；高风险动作再接 Approval Gate。hook 配置文件本身就是 Agent 的风险地图。
- **hook 顺序按"便宜先、贵的后"**：RBAC 检查（一次 dict 查询）排前面快速失败，AML 扫描（要查反洗钱库）排后面，省算力。
- **分阶段部署**：先用 monitor mode 只记录不阻断，再用 soft enforcement 阻断明确违规并标记边缘 case，经过评审后进入 full enforcement。每一阶段的持续时间由误报、漏报和业务风险决定。

## 适用场景

- **有副作用且错调代价高的动作**：转账、删数据、发消息、调外部 API。读操作（read file、search、fetch 只读）不必套——每加一层都是额外的延迟开销。
- **强合规的垂直领域**：金融、医疗、法律和政府场景中的金额阈值、处方剂量或制裁名单等确定性约束，可以编码进 pre-check；复杂判断仍需专业审核。
- **与 Approval Gate 配合的混合把守**：低风险动作走 sandwich 自动放行，高风险动作 sandwich 加人工审批双重把守。

## 已知失效方式

- **Composition Bypass（组合绕过）**：单个动作都被允许，例如读文件、编码内容和写入外部 URL，组合起来却可能造成数据外泄。除了单点 hook，还要增加 session 级 scope analyzer，检查动作序列是否构成已知攻击路径。
- **Sandwich Overhead Tax（夹层税）**：所有工具一律套完整检查会让低风险动作承担不必要的延迟。应按 risk\_level 选择 guard 组合，并记录每层开销。
- **Schema Drift（schema 漂移）**：pre-check 校验的 schema 和下游工具实际期望的不一致，导致 pre 通过、tool 跑挂。应对是用 OpenAPI / JSON Schema 做 single source of truth，两边从同一份 schema 生成校验逻辑。

Guardrail Sandwich 需要持续维护 hook 顺序、风险分级和 schema 的 single source of truth。仅安装 hook 不能替代治理流程。

## 验证指标

- **block 率**：monitor、soft enforcement 和 full enforcement 分阶段观察，并抽样分析被阻断请求中的真违规和误报。
- **误执行率**：按业务动作和风险等级统计错误调用、错误参数和越权执行。高风险动作不设可容忍的背景错误率。
- **夹层延迟开销**：按 risk\_level 分解各个 hook 的延迟。低风险读操作与高风险写操作应采用不同的检查组合。
- **审计留档完整率**：trace\_id 应串联 PRE、TOOL 和 POST。留存期限按所在行业、地区和组织政策配置。

## 最小实现

```
wrap(tool, ctx):
    for hook in pre_hooks:            # 顺序: 便宜先，贵的后
        verdict = hook(ctx)
        若 verdict.block → 短路返回 blocked + trace
        若 verdict.改参数 → 更新 ctx.args
    result = tool(**ctx.args)          # 在隔离 sandbox 内执行
    for hook in post_hooks:
        verdict = hook(ctx, result)
        若 verdict.rollback → 触发 saga inverse，返回 rolled_back
        若 verdict.改结果 → 更新 result
    返回 ok + result + 完整 trace（每个 hook 的 passed/reason/延迟）
```

生产实现应覆盖所有 destructive 工具；hook 保持 idempotent；trace\_id 写入数据库，作为审计串联键。

## 场景化示例

设想一个银行对公转账 Agent 给 destructive 工具套上 sandwich。PRE 层执行 RBAC、按银行政策配置的金额与风险分级、收款账号白名单和制裁名单扫描；TOOL 层使用幂等键并记录外部回执；POST 层执行反洗钱检查、结果核对、必要时 saga 补偿并写入审计账本。hook 顺序必须由法务、风控和业务共同确认。换到医疗场景，控制项会变成角色权限、处方剂量、病史约束、禁忌与药物相互作用，结构仍是执行前准入、执行中约束、执行后核验。

## 相邻模式

- **工具调度（A1）**：A1 的 quota 和 state refresh 位于 dispatch 内部，A4 在 dispatch 前后提供通用检查。
- **规划-执行（A2）**：A2 plan 里的审批节点和合规校验，落地时常由 A4 的 pre-check 实现。
- **Approval Gate（治理模块）**：同源但分工不同。Approval Gate 是 human-in-loop（等人按批准），A4 是 deterministic check（机器直接做规则匹配）。两者常配合——低风险走 sandwich，高风险 sandwich 加 Approval Gate。
- **失败日记（记忆模块）**：组合绕过、记忆中毒这类失败不能只靠单次动作护栏处理，还要结合跨任务失败记录和审计。

## 工程判断

Guardrail Sandwich 在动作前、执行中和动作后分别设置检查与约束。三层需要独立记录结果，并为失败动作提供拒绝、回滚或人工接管路径。

## 企业证据

<p class="evidence-empty">当前没有与本模式绑定的公开评审案例。模式定义不因此视为已经获得企业验证。</p>

<p style="font-size: 0.88rem; color: var(--color-text-muted);">案例收录要求说明业务约束、实现结构、已知失败和迁移边界。参见 <a href="https://adpsagent.com/zh/join/">贡献与评审规则</a>。</p>

## 开源实现

[**DeerFlow Guardrail 与双层授权**](https://adpsagent.com/zh/cases/deerflow-guardrail/)按五个公开 PR 展开装配时过滤、运行时授权、可信身份、RBAC 与 RunJournal 的演进，并标出该实现对本模式的覆盖范围。

<div class="document-citation">
<p><strong>引用建议：</strong>ADPS，《A4 护栏三明治》，Agent 设计模式白皮书 v0.3，2026-07-30。</p>
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
<p><a href="https://adpsagent.com/zh/chronicle/#patterns-a4-guardrail-sandwich">在 ADPS Chronicle 中查看</a></p>
</section>

<!-- PAGE-CHRONICLE:END -->
