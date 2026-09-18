<p style="font-size: 0.9rem; color: var(--color-text-faint); margin-bottom: 1.75rem;"><a href="https://adpsagent.com/zh/patterns/">模式目录</a><span style="margin: 0 0.45rem;">/</span>横切工程面<span style="margin: 0 0.45rem;">/</span>X3</p>

<header class="publication-head">
<p class="publication-series">ADPS 横切工程面规范</p>
<h1>X3 · Security &amp; Identity · 安全与身份</h1>
<p class="publication-deck">沿 Agent 委派链传播身份，以最小权限和短时凭证约束每次运行。</p>
</header>

**主体、委派、凭证和资源边界**构成 X3 的控制主线。主体确认谁在行动，委派说明它代表谁并获准做什么，凭证把裁决落实到外部系统，资源边界限制权限能够触及的对象、环境和时限。

X3 沿用户、Agent、工作负载、运行、工具和资源传播身份，并把委派、授权和凭证限制在具体能力与环境内。

## 身份链

```
principal → tenant → agent version → workload → session/run
          → intent → approval → short-lived credential → resource
```

每一跳都要保留“谁代表谁、获准做什么、作用于哪个资源、到何时失效”。共享服务账号只能说明请求来自某个进程，无法证明具体用户、Agent 版本和委派链。

## 工程职责

<table><thead><tr><th>职责</th><th>核心问题</th><th>产物</th></tr></thead><tbody>
<tr><td>身份</td><td>当前主体是谁，来自哪个租户和 Agent 版本</td><td>principal、workload identity、run identity</td></tr>
<tr><td>委派</td><td>上游主体允许下游 Agent 代做什么</td><td>能力、资源、环境、时限和不可转授条件</td></tr>
<tr><td>授权</td><td>这次具体 Intent 应当允许、拒绝还是转人审</td><td>allow / deny / ask 裁决与理由</td></tr>
<tr><td>凭证</td><td>如何把裁决落实到外部系统</td><td>短时、窄权限、可撤销凭证</td></tr>
</tbody></table>

## 策略、裁决、执行与证据

策略源维护规则，决策服务针对结构化请求作裁决，G5 钩子流水线在不可绕过的节点执行，X1 保存请求、裁决、状态差异和外部回执。四者写在同一个 handler 中，会把规则版本、运行身份和审计边界缠在一起。

## 生命周期

<table><thead><tr><th>阶段</th><th>安全与身份控制</th></tr></thead><tbody>
<tr><td>登记</td><td>登记负责人、能力、风险级别、租户与可访问资源</td></tr>
<tr><td>设计与评测</td><td>定义最小权限，运行越权、拒绝、凭证泄露和跨租户负例</td></tr>
<tr><td>灰度</td><td>只读或沙箱身份，限制频率、金额、批量和资源范围</td></tr>
<tr><td>运行</td><td>按 Intent 签发短时凭证，恢复时重新验证前置条件</td></tr>
<tr><td>复验与退役</td><td>按异常和回归结果收窄授权；撤销旧版本与离职主体的访问</td></tr>
</tbody></table>

## 与治理模式的关系

G1 审批门绑定具体 Intent，G2 设置影响上限，G3 调整能力长期自治档位，G5 提供确定性执行点。X3 为这些模式提供统一身份与授权基础，也覆盖感知数据访问、记忆读写、子 Agent 委派和反思资产发布。

## 常见失效

- 所有 Agent 共用长期服务账号；
- 把 prompt 中的角色描述当成权限；
- 审批只绑定自然语言摘要，没有绑定工具版本、参数和资源；
- 恢复运行时沿用过期凭证和旧前置条件；
- 记录用户身份，却丢失子 Agent、工作负载和委派链；
- 评测环境可以读取生产密钥或修改发布门。

## 公开路径

[DeerFlow Guardrail](https://adpsagent.com/zh/cases/deerflow-guardrail/)展示面向公开代码的身份传播、Provider、裁决与执行点。[治理模块研讨会](https://adpsagent.com/zh/workshops/governance-2026-08-18/)记录了装配时过滤、运行时复验、短时凭证和 Agent 生命周期中的共性问题。

<div class="document-citation">
<p><strong>引用建议：</strong>ADPS，《X3 · Security &amp; Identity · 安全与身份》，ADPS 横切工程面规范 v0.5，2026-08-20。</p>
<p><a href="https://adpsagent.com/zh/cases/deerflow-guardrail/">DeerFlow Guardrail</a> · <a href="https://adpsagent.com/zh/workshops/governance-2026-08-18/">治理研讨会</a> · <a href="https://creativecommons.org/licenses/by/4.0/" rel="license noopener" target="_blank">CC BY 4.0</a></p>
<p class="publication-disclaimer"><strong>使用边界：</strong>本页定义工程范围与接口，不构成产品认证。具名实践以案例页与公开代码为准。</p>
</div>

<!-- PAGE-CHRONICLE:START -->

<section aria-labelledby="page-chronicle-title" class="page-chronicle">
<h2 id="page-chronicle-title">溯源记录</h2>
<dl>
<div><dt>来源记录</dt><dd>ADPS 模式白皮书；先行工作与参考资料见正文</dd></div>
<div><dt>本页首次公开</dt><dd><time datetime="2026-08-20">2026-08-20</time></dd></div>
</dl>
<p><a href="https://adpsagent.com/zh/chronicle/#patterns-x3-security-and-identity">在 ADPS Chronicle 中查看</a></p>
</section>

<!-- PAGE-CHRONICLE:END -->
