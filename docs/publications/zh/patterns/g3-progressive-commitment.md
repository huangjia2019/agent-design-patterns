<p style="font-size: 0.9rem; color: var(--color-text-faint); margin-bottom: 1.75rem;"><a href="https://adpsagent.com/zh/patterns/">模式矩阵</a><span style="margin: 0 0.45rem;">/</span>模式白皮书<span style="margin: 0 0.45rem;">/</span>G3</p>

<header class="publication-head">
<p class="publication-series">ADPS Agent 设计模式白皮书</p>
<h1>G3 · Progressive Commitment · 渐进承诺</h1>
<p class="publication-deck">按能力、场景、资源和版本管理权限的晋级、维持、降级与退役。</p>
</header>

渐进承诺管理带版本的局部自治权。它不把整个 Agent 标成“可信”或“不可信”，而是分别记录某个版本在某项能力、场景、资源和环境中的权限。

## 坐标与授权单元

**治理 × 链式。**影子运行、建议、受限执行和扩大范围存在证据前置关系；事故、依赖变化或版本切换又会让链条后退。

```
authority_key = (
    agent_version,
    capability,
    scenario,
    resource_scope,
    environment
)
```

同一薪酬 Agent 的“校验批次”和“提交批次”应是两条授权记录。前者可以自动化，后者仍可保留审批。

## 自治档位

<table><thead><tr><th>档位</th><th>允许行为</th><th>主要证据</th></tr></thead><tbody>
<tr><td>Shadow</td><td>读取真实输入，输出不影响业务</td><td>与现有流程对照、覆盖与失败分类</td></tr>
<tr><td>Recommend</td><td>生成建议或草稿，由人采用</td><td>采纳、修订差异与长尾错误</td></tr>
<tr><td>Bounded Execute</td><td>在硬边界内自动执行低影响或可逆动作</td><td>外部验收、撤回、边界触发与事故</td></tr>
<tr><td>Expanded Execute</td><td>扩大对象、频率或场景，仍保留硬上限</td><td>稳定窗口、分层样本与业务结果</td></tr>
<tr><td>Frozen / Retired</td><td>停止新增副作用，保留审计和回滚</td><td>事故、版本过期、责任人缺失或试点结束</td></tr>
</tbody></table>

## 三层证据

任务与结果说明目标和下游采用；Agent 过程说明规划、工具、记忆和恢复是否按合同工作；基础组件说明模型、工具、存储和策略是否健康。平均成功率无法替代这三层证据，也容易掩盖高风险长尾。

## 运行实例

薪酬 Agent v7 的校验能力先在 Shadow 与人工对照，再进入 Recommend。常规批次表现稳定，但新入职和跨地区税务仍有差异，因此只给常规批次 Bounded Execute。提交能力继续停在 Recommend，由 G1 审批。付款工具换版后，校验能力的授权证书冻结并回到 Shadow，其他未受影响能力维持原档位。

## 权限处置

每次评审可以 promote、hold、narrow、demote 或 retire。降级不只由事故触发；评测覆盖中断、依赖变化、错误率上升、责任人离岗和长期无调用，都可能让原权限失去依据。

## 常见失效

- 给整个 Agent 一个全局等级；
- 只设计升级，不设计冻结与退役；
- 挑选容易样本或只看平均成功率；
- 模型、工具或策略换版后继承旧授权；
- Agent 可以写自己的证据和权限证书；
- 晋级后立即放满流量。

## 验证

检查授权是否绑定版本、能力、场景和资源；观察晋级后短期回退、降级时延、版本继承与退役完整性；确认扩大自治后人工负担确实下降。

<div class="document-citation">
<p><strong>引用建议：</strong>ADPS，《G3 · Progressive Commitment · 渐进承诺》，Agent 设计模式白皮书 v0.4，2026-08-19。</p>
<p><a href="https://adpsagent.com/zh/patterns/">模式目录</a> · <a href="https://adpsagent.com/zh/workshops/governance-2026-08-18/">治理研讨会</a> · <a href="https://creativecommons.org/licenses/by/4.0/" rel="license noopener" target="_blank">CC BY 4.0</a></p>
<p class="publication-disclaimer"><strong>使用边界：</strong>本页为公开评审稿。模式定义与分类可供讨论和引用；运行实例用于说明机制，具名实践另见案例库。</p>
</div>

<!-- PAGE-CHRONICLE:START -->

<section aria-labelledby="page-chronicle-title" class="page-chronicle">
<h2 id="page-chronicle-title">溯源记录</h2>
<dl>
<div><dt>来源记录</dt><dd>ADPS 模式白皮书；先行工作与参考资料见正文</dd></div>
<div><dt>本页首次公开</dt><dd><time datetime="2026-06-07">2026-06-07</time></dd></div>
</dl>
<p><a href="https://adpsagent.com/zh/chronicle/#patterns-g3-progressive-commitment">在 ADPS Chronicle 中查看</a></p>
</section>

<!-- PAGE-CHRONICLE:END -->
