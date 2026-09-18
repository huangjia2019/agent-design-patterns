<p style="font-size: 0.9rem; color: var(--color-text-faint); margin-bottom: 1.75rem;"><a href="https://adpsagent.com/zh/concepts/" style="color: var(--color-text-muted);">概念</a><span style="margin:0 0.45rem;">/</span>概念定义</p>

<header class="publication-head">
<p class="publication-series">ADPS Agent 系统蓝皮书 · 工程概念</p>
<h1>机械状态平面与 Provenance 来源坐标</h1>
<p class="publication-deck">业务参数由程序按来源坐标传递，不经模型重新生成。</p>
</header>

![机械状态平面与 Provenance 来源坐标](../../assets/images/concepts/mechanical-state-plane.png)

## 应用背景：下一步需要的是原值

创建薪资组后，API 返回 `pay_group_id=pg_84721`。下一步关联员工必须使用这个精确 ID，而且要能证明它来自哪次调用、属于哪个租户。如果先让模型摘要“已创建新加坡薪资组”，再让它回忆 ID，工具返回的事实就变成了一次概率生成。

凡是后续 API 会直接消费的值，包括实体 ID、币种、时间范围和幂等键，都应由程序保留原值与来源。

## 概念定义

机械状态平面保存业务 API 调用所需的严格参数。参数由程序从工具回执中解析、存储和传递，不经过模型重新生成。每个值都附带 Provenance，用于记录生产工具、调用实例、作用域和原始回执。

一个状态 Cell 可以表示为：

<pre><code class="language-text">Cell = scope + key + value + producer + provenance
</code></pre>

消费者按坐标读取 Cell，并在调用前校验来源。找不到唯一坐标、来源不符合契约或值已过期时，调用立即终止。

## 工程机制

工具注册时声明输入和输出坐标：

- 输入需要哪个 `key`；
- 从哪个 `scope` 读取；
- 预期由哪个工具和步骤生产；
- 输出写入哪个坐标；
- 值的有效期和覆盖规则。

系统级状态在登录等关键事件写入，API 级状态由工具回执写入。机械状态平面维护最新值和事件历史，工具负责声明自己生产和消费的坐标。

## 案例用法

薪资组模板匹配接口返回 `template_id`，模板导入接口必须使用同一值。此类 ID 可达 64 位或 128 位。模型从对话上下文重新输出时可能误写字符；格式正确也不能证明来源正确。

东方屹腾把 `template_id` 写入 SessionState，并保存产生它的工具回执。导入工具按坐标读取，RunPipeline 在调用前检查 Provenance。叙事上下文只记录“已匹配模板”，不承担 ID 传递。

该实现基于企业管理的封闭工具体系。所有工具由团队注册，因此系统可以在启动时建立状态键字典。开放工具接入场景还需要动态命名空间、来源信任和冲突处理。

## 适用条件

当步骤之间传递 ID、流水号、状态码等不可重新生成的参数，且错误值可能造成数据损坏或错误交易时，应使用机械状态平面。三个运行状态的职责见[会话统一状态](https://adpsagent.com/zh/concepts/unified-session-state/)，任务依赖见[任务 DAG 与状态机](https://adpsagent.com/zh/concepts/task-dag-state-machine/)。

<section aria-labelledby="concept-provenance-title" class="concept-provenance">
<h2 id="concept-provenance-title">提出与来源</h2>
<dl>
<div><dt>概念分组</dt><dd><a href="https://adpsagent.com/zh/concepts/#group-system-boundaries">系统边界与状态</a></dd></div>
<div><dt>ADPS 内初始来源</dt><dd>初始实践：梁博</dd></div>
<div><dt>首次记录</dt><dd><a href="https://adpsagent.com/zh/cases/liangbo-execution-agent/">东方屹腾执行型 Agent 案例</a>（<time datetime="2026-06-19">2026-06-19</time>）</dd></div>
<div><dt>ADPS 整理</dt><dd>ADPS 补入 Provenance 来源坐标和调用前 fail-fast 约束。</dd></div>
<div><dt>当前地位</dt><dd>候选概念</dd></div>
</dl>
</section>

<div class="document-citation">
<p><strong>初始来源：</strong><a href="https://adpsagent.com/zh/cases/liangbo-execution-agent/">东方屹腾执行型 Agent 案例报告</a>；案例提供：梁博（Bo Liang）。</p>
<p><a href="https://adpsagent.com/zh/cases/">案例报告目录</a> · <a href="https://adpsagent.com/zh/patterns/">模式目录</a> · <a href="https://creativecommons.org/licenses/by/4.0/" rel="license noopener" target="_blank">CC BY 4.0</a></p>
</div>

<!-- PAGE-CHRONICLE:START -->

<section aria-labelledby="page-chronicle-title" class="page-chronicle">
<h2 id="page-chronicle-title">溯源记录</h2>
<dl>
<div><dt>来源记录</dt><dd><a href="https://adpsagent.com/zh/cases/liangbo-execution-agent/">东方屹腾执行型 Agent 案例</a>（<time datetime="2026-06-19">2026-06-19</time>）</dd></div>
<div><dt>来源日期</dt><dd><time datetime="2026-06-19">2026-06-19</time></dd></div>
<div><dt>本页首次公开</dt><dd><time datetime="2026-06-21">2026-06-21</time></dd></div>
</dl>
<p><a href="https://adpsagent.com/zh/chronicle/#concepts-mechanical-state-plane">在 ADPS Chronicle 中查看</a></p>
</section>

<!-- PAGE-CHRONICLE:END -->
