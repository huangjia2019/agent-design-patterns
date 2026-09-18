<p style="font-size: 0.9rem; color: var(--color-text-faint); margin-bottom: 1.75rem;"><a href="https://adpsagent.com/zh/patterns/" style="color: var(--color-text-muted);">模式矩阵</a><span style="margin:0 0.45rem;">/</span><a href="https://adpsagent.com/zh/patterns/r2-complexity-based-routing/" style="color: var(--color-text-muted);">R2 复杂度路由</a><span style="margin:0 0.45rem;">/</span>蓝皮书</p>

<header class="publication-head">
<p class="publication-series">ADPS 企业 Agent 系统蓝皮书 · 模式实践切片</p>
<h1>R2 · 复杂度路由 · 东方屹腾执行型 Agent</h1>
<p class="publication-deck">入口分类器生成有限控制信号，意图网关按成本和风险选择执行链。</p>
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
<td style="text-align: left;">R2 复杂度路由 Complexity-Based Routing（推理 × 路由）</td>
</tr>
<tr>
<td style="text-align: left;">结合模式</td>
<td style="text-align: left;">P1 上下文分诊 · G1 审批门</td>
</tr>
<tr>
<td style="text-align: left;">案例</td>
<td style="text-align: left;">上海东方屹腾科技 · HR/薪酬 SaaS · 服务 2 万+ 企业 · 执行型 Agent</td>
</tr>
<tr>
<td style="text-align: left;">对应白皮书</td>
<td style="text-align: left;"><a href="https://adpsagent.com/zh/patterns/r2-complexity-based-routing/">/zh/patterns/r2-complexity-based-routing/</a></td>
</tr>
<tr>
<td style="text-align: left;">源</td>
<td style="text-align: left;">梁博 AICon 逐字稿第三章 · PPT 第 9–12 页</td>
</tr>
<tr>
<td style="text-align: left;">工程结论</td>
<td style="text-align: left;">入口分类器把自然语言转换为有限控制信号，意图网关据此选择不同成本和风险的执行链。</td>
</tr>
</tbody>
</table>

---

## 场景约束

企业 HR 与薪酬入口会收到不同类型的请求：领域外闲聊、薪资表分析、薪资组配置、算薪或代发。若所有请求都进入链式推理和行动编排，简单请求会占用不必要的模型和工具成本，高风险事务也缺少独立治理入口。

复杂度路由在主循环入口完成分类，并把请求分配到深度不同的执行链。

## 控制信号

早期系统使用四个枚举：

| 信号 | 下游处理 |
| --- | --- |
| `chat` | 固定答复或低成本对话 |
| `analyze` | 一次推理，必要时增加 RAG |
| `resolve` | 链式推理、行动或规划执行 |
| `unknown` | 澄清、拒绝或安全兜底 |

随着场景增加，枚举演化为 `task`、`information`、`produce`、`chat` 等类型，并增加第二层业务场景绑定，用于推荐相关 Skill 和工具候选。枚举由下游流程倒推，不直接复用其他产品的分类。

## 路由流程

<pre><code class="language-text">用户输入
  -&gt; 受 Schema 约束的意图分类
  -&gt; 输出校验
  -&gt; 意图网关
  -&gt; chat / analyze / resolve / unknown 执行链
</code></pre>

分类器固定在一到两次模型调用内完成。输出必须符合 Schema，无法解析或置信度不足时转入 `unknown`。意图结论的自然语言摘要写入叙事状态，离散枚举进入控制平面。

会话仍保持 `pre / middle / post` 三段边界：

- `pre` 接收输入并完成意图分类；
- `middle` 执行所选能力链；
- `post` 合成结果并返回。

Orchestrator 管理三段流程，意图网关只负责从信号映射到执行链。

## 案例运行

“你叫什么名字”可以在 `chat` 链路结束；上传薪资表并请求说明进入 `analyze`，按需检索领域知识；搭建薪资组进入 `resolve`，继续使用 R1 链式推理和行动模块。代发等敏感事务在后续控制信号中进入审批门。

第二层场景绑定可以提前缩小 Skill 和工具候选，但不能跳过工具准入、参数校验和审批。

## 失效信号

- 分类结果是一段描述，没有离散枚举；
- 未知输出直接进入默认重链路；
- 所有请求都被路由到最高成本路径；
- 枚举过细，入口分类承担了完整业务规划；
- 业务分类和工具准入混为同一步；
- 路由结果没有进入事件时间线，无法分析误分流。

## 验证指标

- Schema 解析成功率和 `unknown` 比例；
- 各路由档位的流量分布；
- `chat`、`analyze` 被误送入 `resolve` 的比例；
- 事务请求被误送到轻链路的比例；
- 各档平均 Token、延迟和工具调用次数；
- 二层场景绑定后的候选工具缩减率与正确率。

## 与白皮书的对应

R2 白皮书以信号提取、分类和分档执行描述复杂度路由。东方屹腾按动作类型和执行链深度分类，而非只按模型档位分类；`unknown` 承担解析失败和低置信度的回退。

## 迁移条件

自然语言入口对应多条成本、能力或风险差异明显的下游流程时，应使用复杂度路由。入口已经结构化，或所有请求使用同一流程时，可以直接进入主链。信号枚举、兜底和路由指标必须在上线前定义。

<div class="document-citation">
<p><strong>引用建议：</strong>ADPS、梁博，《东方屹腾 · 复杂度路由》，企业 Agent 系统蓝皮书 v0.4，2026-08-02。</p>
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
<p><a href="https://adpsagent.com/zh/chronicle/#patterns-r2-complexity-based-routing-cases-liangbo">在 ADPS Chronicle 中查看</a></p>
</section>

<!-- PAGE-CHRONICLE:END -->
