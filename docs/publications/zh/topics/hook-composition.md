<p style="font-size:0.9rem;color:var(--color-text-faint);margin-bottom:1.75rem;"><a href="https://adpsagent.com/zh/topics/">专题</a><span style="margin:0 0.45rem;">/</span>Hook 组合</p>

<header class="publication-head"><p class="publication-series">ADPS 专题研究</p><h1>Hook 组合 · 把隐藏回调变成可读的控制结构</h1><p class="publication-deck">在生命周期事件上编排治理、观测、恢复与阶段流转，并显式处理顺序、幂等和失败。</p></header>

Hook 把确定性代码放到 Agent 生命周期的固定事件上。它可以在模型调用前收缩上下文，在工具调用前检查权限，在阶段结束后启动下一位 Agent，也可以记录 trace、保存 checkpoint 或清理资源。

Hook 是机制。具体职责来自它所在的事件、读取的状态、拥有的权限以及失败后的处理方式。

## 四类职责

<table>
<thead>
<tr>
<th style="text-align: left;">类别</th>
<th style="text-align: left;">典型事件</th>
<th style="text-align: left;">主要动作</th>
</tr>
</thead>
<tbody>
<tr>
<td style="text-align: left;">编排</td>
<td style="text-align: left;">artifact accepted、stage completed</td>
<td style="text-align: left;">启动下一阶段、路由任务、聚合结果</td>
</tr>
<tr>
<td style="text-align: left;">治理</td>
<td style="text-align: left;">before tool、before commit</td>
<td style="text-align: left;">鉴权、策略裁决、审批、限额与参数复核</td>
</tr>
<tr>
<td style="text-align: left;">观测</td>
<td style="text-align: left;">model/tool/step completed</td>
<td style="text-align: left;">写入事件、版本、状态差异和外部回执</td>
</tr>
<tr>
<td style="text-align: left;">恢复</td>
<td style="text-align: left;">failure、timeout、cancel</td>
<td style="text-align: left;">保存 checkpoint、补偿、回收租约、升级人工</td>
</tr>
</tbody>
</table>

## 组合图

<pre><code class="language-text">before_model
  → context_policy
  → prompt_trace

before_tool
  → identity_check
  → policy_decision
  → approval_if_needed

after_tool
  → receipt_capture
  → state_diff
  → next_stage_or_recovery
</code></pre>

运行时需要展示最终顺序。两个 Hook 都修改参数时，先后顺序会改变结果；一个审计 Hook 失败时，是阻断业务还是降级记录，也必须提前定义。

以薪酬提交为例：`before_tool` 先验证调用身份，再读取策略并决定是否需要审批；恢复后，`before_commit` 重新检查员工状态和 Intent 摘要；工具成功后，`after_tool` 保存回执与写后读取。若审计写入失败，系统可以把低风险只读调用降级记录，但生产写入通常应阻断。顺序和失败语义属于 Hook 组合本身，不能依赖插件注册的偶然先后。

## HookSpec

<pre><code class="language-yaml">hook_id: payroll.before_commit.policy
event: before_tool
priority: 200
reads: [principal, intent, tool_digest, resource_scope]
writes: [policy_decision]
idempotency_key: run_id + intent_digest
on_failure: deny
emits: [policy.decided]
owner: security-platform
version: 7
</code></pre>

## 与 G5 的关系

G5 保留历史编号，聚焦治理中的确定性执行点。Hook 组合覆盖更大的范围，所以不增加新的协作模式编号。若未来出现无法由现有模式和机制说明的独立问题，再讨论目录调整。

## 常见问题

- Hook 顺序依赖代码注册顺序，运行图不可见。
- 重试时重复发通知、扣配额或提交外部动作。
- 策略来源、裁决、执行和日志写进同一个 handler。
- 一个非关键观测 Hook 故障，意外阻断主任务。
- 子 Agent 与父 Agent 使用不同 Hook 集合，却没有版本记录。

## 评审问题

1. 每个 Hook 由什么事件触发，读写哪些状态？
2. 顺序和冲突规则是否显式？
3. 重试、恢复和重复事件是否幂等？
4. 失败时 fail-open、fail-closed 还是升级人工？
5. 运行记录能否显示最终 Hook 集合和版本？

## 来源

治理研讨会明确了策略来源、裁决、执行与证据的分层；协作研讨会补充了阶段流转、跨 Agent 触发和恢复职责。本专题合并两场讨论，G5 继续作为历史与治理入口。

<div class="document-citation"><p><strong>引用建议：</strong>ADPS，《Hook 组合 · 把隐藏回调变成可读的控制结构》，ADPS 专题研究，2026-08-26。</p><p><a href="https://adpsagent.com/zh/topics/">专题目录</a> · <a href="https://adpsagent.com/zh/workshops/collaboration-2026-08-25/">协作研讨会</a> · <a href="https://creativecommons.org/licenses/by/4.0/" rel="license noopener" target="_blank">CC BY 4.0</a></p></div>

<!-- PAGE-CHRONICLE:START -->

<section aria-labelledby="page-chronicle-title" class="page-chronicle">
<h2 id="page-chronicle-title">溯源记录</h2>
<dl>
<div><dt>来源记录</dt><dd>正文关联的研讨会与案例：<a href="https://adpsagent.com/zh/workshops/collaboration-2026-08-25/">协作研讨会</a>（<time datetime="2026-08-25">2026-08-25</time>）</dd></div>
<div><dt>来源日期</dt><dd><time datetime="2026-08-25">2026-08-25</time></dd></div>
<div><dt>本页首次公开</dt><dd><time datetime="2026-08-26">2026-08-26</time></dd></div>
</dl>
<p><a href="https://adpsagent.com/zh/chronicle/#topics-hook-composition">在 ADPS Chronicle 中查看</a></p>
</section>

<!-- PAGE-CHRONICLE:END -->
