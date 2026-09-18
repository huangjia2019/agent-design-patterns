<p style="font-size: 0.9rem; color: var(--color-text-faint); margin-bottom: 1.75rem;"><a href="https://adpsagent.com/zh/concepts/" style="color: var(--color-text-muted);">概念</a><span style="margin:0 0.45rem;">/</span>概念定义</p>

<header class="publication-head">
<p class="publication-series">ADPS Agent 系统蓝皮书 · 工程概念</p>
<h1>可续跑澄清作业：缺信息时暂停同一任务</h1>
<p class="publication-deck">缺少信息时冻结同一作业，保存已确认字段、候选项和恢复游标。</p>
</header>

## 从范围未命中开始

用户要求在“闸机中控”包下建图，工程索引里没有唯一匹配。系统已经识别出创建动作和用例图类型，只缺挂载位置。重新开启一轮对话会丢失已确认字段，也可能重新解释出另一份意图。

## 定义

可续跑澄清作业把一次提问建模为持久化运行状态。系统保存作业 ID、已确认字段、待确认字段、候选项、当前阶段、恢复游标和宿主工程版本。用户补充信息后恢复原作业。

<pre><code class="language-text">PendingOperation = {
  job_id,
  confirmed_fields,
  missing_fields,
  candidates,
  stage,
  resume_cursor,
  host_revision
}
</code></pre>

恢复前重新校验候选范围和宿主版本。工程已变化时，系统回到范围解析，避免沿失效坐标继续写入。

## 工程边界

弹窗只负责采集信息。正确性来自作业冻结、持久化和断点恢复。仅在内存中保存状态，无法覆盖进程重启、延迟回复和多人协作。

## 来源与谱系

- 初始研究来源：AI4MBSE 建模 Agent 项目，作者袁良锭（Liangding Yuan）；名称由 ADPS 归纳。
- 历史近邻：durable execution、continuation、checkpointed interrupt、workflow wait state。
- ADPS 整理：将澄清字段、候选工程对象、恢复游标和宿主版本放进同一作业合同。
- 定义地位：ADPS 重述。

<section aria-labelledby="concept-provenance-title" class="concept-provenance">
<h2 id="concept-provenance-title">提出与来源</h2>
<dl>
<div><dt>概念分组</dt><dd><a href="https://adpsagent.com/zh/concepts/#group-planning-execution">规划、执行与写回</a></dd></div>
<div><dt>ADPS 内初始来源</dt><dd>初始研究实践：袁良锭</dd></div>
<div><dt>首次记录</dt><dd><a href="https://adpsagent.com/zh/cases/ark-mbse-agent/">AI4MBSE 建模 Agent 项目</a>（<time datetime="2026-08-02">2026-08-02</time>）</dd></div>
<div><dt>ADPS 整理</dt><dd>ADPS 将澄清字段、候选对象、恢复游标和宿主版本放进同一作业合同。</dd></div>
<div><dt>当前地位</dt><dd>ADPS 重述</dd></div>
</dl>
</section>

<div class="document-citation">
<p><strong>初始来源：</strong><a href="https://adpsagent.com/zh/cases/ark-mbse-agent/">AI4MBSE 建模 Agent 项目</a>；作者：袁良锭（Liangding Yuan）。</p>
<p><a href="https://adpsagent.com/zh/cases/">案例报告目录</a> · <a href="https://adpsagent.com/zh/patterns/">模式目录</a> · <a href="https://creativecommons.org/licenses/by/4.0/" rel="license noopener" target="_blank">CC BY 4.0</a></p>
</div>

<!-- PAGE-CHRONICLE:START -->

<section aria-labelledby="page-chronicle-title" class="page-chronicle">
<h2 id="page-chronicle-title">溯源记录</h2>
<dl>
<div><dt>来源记录</dt><dd><a href="https://adpsagent.com/zh/cases/ark-mbse-agent/">AI4MBSE 建模 Agent 项目</a>（<time datetime="2026-08-02">2026-08-02</time>）</dd></div>
<div><dt>来源日期</dt><dd><time datetime="2026-08-02">2026-08-02</time></dd></div>
<div><dt>本页首次公开</dt><dd><time datetime="2026-08-02">2026-08-02</time></dd></div>
</dl>
<p><a href="https://adpsagent.com/zh/chronicle/#concepts-resumable-clarification-job">在 ADPS Chronicle 中查看</a></p>
</section>

<!-- PAGE-CHRONICLE:END -->
