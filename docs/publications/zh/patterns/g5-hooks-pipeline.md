<p style="font-size: 0.9rem; color: var(--color-text-faint); margin-bottom: 1.75rem;"><a href="https://adpsagent.com/zh/patterns/">模式矩阵</a><span style="margin: 0 0.45rem;">/</span>模式白皮书<span style="margin: 0 0.45rem;">/</span>G5</p>

<header class="publication-head">
<p class="publication-series">ADPS Agent 设计模式白皮书</p>
<h1>G5 · Hooks Pipeline · 钩子流水线</h1>
<p class="publication-deck">在不可绕过的生命周期节点执行有序、可测试的确定性控制。</p>
</header>

钩子流水线把权限、参数、配额、格式和审计等确定性规则放到少数不可绕过的执行节点。它避免把可执行边界写进 prompt，也避免在多个 handler 中散落互不一致的 if。

## v0.4 分类

**扩展模式 · 确定性执行机制。**流水线内部有链式顺序，但它横跨 Agent 生命周期，不占核心矩阵单格。

## 四层分工

<table><thead><tr><th>层</th><th>职责</th><th>例子</th></tr></thead><tbody>
<tr><td>Policy Source</td><td>保存业务规则与配置</td><td>RBAC Provider、策略库、租户配置</td></tr>
<tr><td>Decision</td><td>结合身份、参数、资源和环境形成裁决</td><td>allow、deny、ask、reason、obligation</td></tr>
<tr><td>Enforcement</td><td>在不可绕过的节点执行裁决</td><td>middleware、hook、gateway、sandbox</td></tr>
<tr><td>Evidence</td><td>记录输入、版本、命中规则和结果</td><td>audit event、trace、RunJournal</td></tr>
</tbody></table>

Hook 是 Enforcement Point。把所有策略硬编码进 hook 会妨碍业务演化；让 hook 临时调用模型决定权限，又会丢掉确定性边界。

## 生命周期节点

<table><thead><tr><th>节点</th><th>控制</th></tr></thead><tbody>
<tr><td>装配</td><td>工具过滤、Skill 准入、凭证绑定与版本固定</td></tr>
<tr><td>输入</td><td>schema、来源、租户、敏感等级与注入标记</td></tr>
<tr><td>工具前</td><td>身份、参数、资源、配额、审批与前置条件</td></tr>
<tr><td>提交前</td><td>新鲜状态、幂等、单次消费与事务条件</td></tr>
<tr><td>工具后</td><td>schema、状态差异、敏感输出与外部回执</td></tr>
<tr><td>结束、恢复与退役</td><td>验收、checkpoint、意图复验、资源和凭证回收</td></tr>
</tbody></table>

## 装配时与运行时

```
task needs
  ∩ tool groups
  ∩ agent/subagent allow-deny
  ∩ active skill policy
  ∩ principal authorization
  = model-visible tools

visible tool + arguments + resource + environment + quota + approval
  → runtime verdict
```

装配时过滤缩小模型选择面；运行时复核处理参数、资源和状态变化。两层不能互相替代。

## DeerFlow 公开演进

[DeerFlow Guardrail](https://adpsagent.com/zh/cases/deerflow-guardrail/)的五个公开 PR 依次加入工具前 middleware、可信 Principal、RunJournal、独立 RBAC Provider 和双层授权。同步与异步路径、Lead Agent、Subagent 与 Embedded Client 都纳入测试。

现有公开实现覆盖 allow/deny 型 PRE guard；人工 ask、持久化意图和通用 POST 业务验收仍需接入方补齐。

## 故障语义

流水线必须声明顺序、裁决冲突、超时和异常默认行为、同步异步一致性、审计故障与重试语义。高风险授权通常 fail closed，低风险 telemetry 可以缓冲后继续。默认行为按 hook 类型配置并测试。

## 常见失效与验证

重点排查 prompt 中的安全规则、旁路入口、静默扩大权限的 payload 改写、POST 替代 PRE、策略与执行混在一个函数、依赖故障默认放行，以及非幂等 hook 重试。

验证主 Agent、子 Agent、同步、异步、恢复和嵌入式入口覆盖；deny 后 handler 调用必须为零；同一配置的顺序稳定；每个 reason code、冲突与故障分支都有合同测试。

## 2026-08-25 研讨会修订：Hook 组合的边界

Hook 可以承担编排、治理、观测和恢复职责。G5 保留历史编号并聚焦治理中的确定性执行点；跨模块组合另见 Hook 组合专题，不新增 C7。

[协作模块研讨记录](https://adpsagent.com/zh/workshops/collaboration-2026-08-25/)

<div class="document-citation">
<p><strong>引用建议：</strong>ADPS，《G5 · Hooks Pipeline · 钩子流水线》，Agent 设计模式白皮书 v0.4，2026-08-19。</p>
<p><a href="https://adpsagent.com/zh/patterns/">模式目录</a> · <a href="https://adpsagent.com/zh/workshops/governance-2026-08-18/">治理研讨会</a> · <a href="https://creativecommons.org/licenses/by/4.0/" rel="license noopener" target="_blank">CC BY 4.0</a></p>
<p class="publication-disclaimer"><strong>使用边界：</strong>本页为公开评审稿。模式定义与分类可供讨论和引用；运行实例用于说明机制，具名实践另见案例库。</p>
</div>

<!-- PAGE-CHRONICLE:START -->

<section aria-labelledby="page-chronicle-title" class="page-chronicle">
<h2 id="page-chronicle-title">溯源记录</h2>
<dl>
<div><dt>来源记录</dt><dd>ADPS 模式白皮书；先行工作与参考资料见正文</dd></div>
<div><dt>本页首次公开</dt><dd><time datetime="2026-07-18">2026-07-18</time></dd></div>
</dl>
<p><a href="https://adpsagent.com/zh/chronicle/#patterns-g5-hooks-pipeline">在 ADPS Chronicle 中查看</a></p>
</section>

<!-- PAGE-CHRONICLE:END -->
