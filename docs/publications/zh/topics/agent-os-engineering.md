<p style="font-size:0.9rem;color:var(--color-text-faint);margin-bottom:1.75rem;"><a href="https://adpsagent.com/zh/topics/">专题</a><span style="margin:0 0.45rem;">/</span>Agent OS</p>

<header class="publication-head"><p class="publication-series">ADPS 专题研究</p><h1>Agent OS · 从类比到工程清单</h1><p class="publication-deck">用操作系统的责任划分检查多 Agent runtime，同时保留类比的边界。</p></header>

多 Agent runtime 越来越像一个小型操作系统：它要安排执行单元、隔离资源、传递消息、保存状态、处理失败，还要让人随时暂停、接管和恢复。这个类比适合用来检查工程缺项。

## 八项责任

<table>
<thead>
<tr>
<th style="text-align: left;">OS 视角</th>
<th style="text-align: left;">Agent runtime 中的问题</th>
</tr>
</thead>
<tbody>
<tr>
<td style="text-align: left;">调度</td>
<td style="text-align: left;">哪个 Agent 何时运行，优先级、预算和取消怎样处理</td>
</tr>
<tr>
<td style="text-align: left;">隔离</td>
<td style="text-align: left;">context、工具、凭证、工作区和故障是否彼此隔离</td>
</tr>
<tr>
<td style="text-align: left;">通信</td>
<td style="text-align: left;">消息、事件、artifact 和 handoff 是否有 schema 与版本</td>
</tr>
<tr>
<td style="text-align: left;">存储</td>
<td style="text-align: left;">checkpoint、memory、workspace 和外部事实如何分层</td>
</tr>
<tr>
<td style="text-align: left;">身份</td>
<td style="text-align: left;">用户委托怎样传给 Agent、run、工具和资源</td>
</tr>
<tr>
<td style="text-align: left;">观测</td>
<td style="text-align: left;">因果 trace、组件版本、状态差异与外部结果怎样连接</td>
</tr>
<tr>
<td style="text-align: left;">回收</td>
<td style="text-align: left;">临时凭证、锁、队列、子任务和沙箱何时释放</td>
</tr>
<tr>
<td style="text-align: left;">故障处理</td>
<td style="text-align: left;">超时、重试、补偿、熔断、降级和人工接管怎样协作</td>
</tr>
</tbody>
</table>

## 类比在哪里有用

操作系统把“能运行”与“能长期管理”分开。一个模型能够调用多个工具，并不代表 runtime 已经处理调度、公平性、隔离、资源泄漏和故障传播。类比迫使架构师给这些责任安排明确位置。

例如两个 Coding Agent 分别修改客户端和服务端。调度器需要知道它们是否争用同一个 API 合同；隔离层给出独立 worktree 和短时凭证；通信层使用带版本的 Handoff Contract；存储层保存 checkpoint；取消其中一个任务时，回收层还要释放沙箱、租约和排队中的回调。只实现“同时启动两个 Agent”，这些责任都还没有答案。

## 类比在哪里失真

Agent 的执行意图和结果具有概率性，传统进程通常没有这种语义。Agent 的记忆也不等同于内存：它还涉及内容选择、可信度、遗忘和版本。Human-in-the-loop 更接近业务控制与组织责任，不能简单映射为中断处理。

因此，Agent OS 目前适合作为工程清单和研究议程，不作为统一产品定义。

## 最小运行时接口

<pre><code class="language-text">submit(task, principal, constraints)
spawn(role, task_packet, authority_scope)
handoff(contract)
observe(run_id)
checkpoint(run_id)
cancel(run_id, reason)
reclaim(run_id)
</code></pre>

接口名称可以变化，责任不能消失。实现采用中心 Orchestrator、分布式事件总线或混合架构，都要回答这些问题。

## 研究问题

1. Agent、workload、run 和 tool invocation 的身份模型怎样分层？
2. 跨 Session 的资源冲突能否在调度前声明和检测？
3. Handoff Contract 与 Agent Protocol 怎样对接？
4. 长程任务的 checkpoint 应冻结哪些版本与外部前置条件？
5. 资源回收怎样覆盖试点结束、责任人离岗和系统退役？

## 来源

该专题来自协作与治理模块研讨中的跨层讨论，并连接 C5 子 Agent 隔离、C6 编舞、X1 可观测性和 X3 安全与身份。

<div class="document-citation"><p><strong>引用建议：</strong>ADPS，《Agent OS · 从类比到工程清单》，ADPS 专题研究，2026-08-26。</p><p><a href="https://adpsagent.com/zh/topics/">专题目录</a> · <a href="https://adpsagent.com/zh/workshops/collaboration-2026-08-25/">协作研讨会</a> · <a href="https://creativecommons.org/licenses/by/4.0/" rel="license noopener" target="_blank">CC BY 4.0</a></p></div>

<!-- PAGE-CHRONICLE:START -->

<section aria-labelledby="page-chronicle-title" class="page-chronicle">
<h2 id="page-chronicle-title">溯源记录</h2>
<dl>
<div><dt>来源记录</dt><dd>正文关联的研讨会与案例：<a href="https://adpsagent.com/zh/workshops/collaboration-2026-08-25/">协作研讨会</a>（<time datetime="2026-08-25">2026-08-25</time>）</dd></div>
<div><dt>来源日期</dt><dd><time datetime="2026-08-25">2026-08-25</time></dd></div>
<div><dt>本页首次公开</dt><dd><time datetime="2026-08-26">2026-08-26</time></dd></div>
</dl>
<p><a href="https://adpsagent.com/zh/chronicle/#topics-agent-os-engineering">在 ADPS Chronicle 中查看</a></p>
</section>

<!-- PAGE-CHRONICLE:END -->
