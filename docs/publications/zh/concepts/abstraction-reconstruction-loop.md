<p style="font-size:0.9rem;color:var(--color-text-faint);margin-bottom:1.75rem;"><a href="https://adpsagent.com/zh/concepts/">概念</a><span style="margin:0 0.45rem;">/</span>概念定义</p>

<header class="publication-head"><p class="publication-series">ADPS Agent 系统 · 工程概念</p><h1>抽象—还原往返</h1><p class="publication-deck">从现场提炼共同结构，再恢复关键差异检验能否施工。</p></header>

## 应用背景：抽象能帮助迁移，也可能把关键差异抹掉

批量筛选简历和批量检查代码都可以抽象成“扇出—处理—聚合”。回到现场以后，简历任务可能需要隐藏敏感字段并由招聘负责人裁决，代码任务则需要隔离 worktree、运行测试并由仓库所有者合并。如果只保留箭头相同，就无法指导权限、状态和验收设计。

## 概念定义

抽象—还原往返包含两个方向。抽象从多个案例提取可复用的问题、约束和结构；还原把结构放回具体角色、对象、状态、权限、证据、失败后果和验收条件，检查它是否仍能工作。还原失败说明抽象过度，或模式尚未写清适用边界。

## 工程机制

每个候选模式至少经过两次还原：一次回到最初案例，确认没有删除决定成败的差异；一次进入独立领域，确认它不依赖原案例的专有名词。凡会改变业务判断、状态迁移、权力边界、证据效力、后续动作、责任归属或验收结果的差异，都需要保留或写入适用条件。

## 使用边界

这个往返用于提炼和审核模式，不要求案例共享相同实现。若一种结构只能在原项目中解释，先保留为案例概念；若在不同领域还原后仍能给出可检查的设计动作，才适合升级为模式。

<section aria-labelledby="concept-provenance-title" class="concept-provenance">
<h2 id="concept-provenance-title">提出与来源</h2>
<dl>
<div><dt>概念分组</dt><dd><a href="https://adpsagent.com/zh/concepts/#group-pattern-method">模式方法与演进</a></dd></div>
<div><dt>ADPS 内初始来源</dt><dd>ADPS 内初始提出：黄佳</dd></div>
<div><dt>首次记录</dt><dd><a href="https://adpsagent.com/zh/workshops/collaboration-2026-08-25/">协作模块第一次研讨会</a>（<time datetime="2026-08-25">2026-08-25</time>）</dd></div>
<div><dt>ADPS 整理</dt><dd>ADPS 将现场到模式、再回到现场的往返整理为模式审校方法。</dd></div>
<div><dt>当前地位</dt><dd>跨模块方法概念</dd></div>
</dl>
</section>

<div class="document-citation"><p><strong>定义来源：</strong>ADPS 白皮书研讨与模式整理。</p><p><a href="https://adpsagent.com/zh/concepts/">概念目录</a> · <a href="https://adpsagent.com/zh/workshops/">研讨会</a> · <a href="https://creativecommons.org/licenses/by/4.0/" rel="license noopener" target="_blank">CC BY 4.0</a></p></div>

<!-- PAGE-CHRONICLE:START -->

<section aria-labelledby="page-chronicle-title" class="page-chronicle">
<h2 id="page-chronicle-title">溯源记录</h2>
<dl>
<div><dt>来源记录</dt><dd><a href="https://adpsagent.com/zh/workshops/collaboration-2026-08-25/">协作模块第一次研讨会</a>（<time datetime="2026-08-25">2026-08-25</time>）</dd></div>
<div><dt>来源日期</dt><dd><time datetime="2026-08-25">2026-08-25</time></dd></div>
<div><dt>本页首次公开</dt><dd><time datetime="2026-08-26">2026-08-26</time></dd></div>
</dl>
<p><a href="https://adpsagent.com/zh/chronicle/#concepts-abstraction-reconstruction-loop">在 ADPS Chronicle 中查看</a></p>
</section>

<!-- PAGE-CHRONICLE:END -->
