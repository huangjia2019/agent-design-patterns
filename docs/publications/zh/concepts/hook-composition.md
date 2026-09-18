<p style="font-size:0.9rem;color:var(--color-text-faint);margin-bottom:1.75rem;"><a href="https://adpsagent.com/zh/concepts/">概念</a><span style="margin:0 0.45rem;">/</span>概念定义</p>

<header class="publication-head"><p class="publication-series">ADPS Agent 系统 · 工程概念</p><h1>Hook 组合</h1><p class="publication-deck">在生命周期事件上组合编排、治理、观测和恢复动作。</p></header>

## 应用背景：同一个 Hook 名称可能隐藏四种职责

团队在“需求完成后”触发编码 Agent，在高危工具调用前暂停审批，在调用后记录 trace，并在失败时保存 checkpoint。实现上都可以叫 Hook，设计责任却分别属于流程编排、治理、观测和恢复。若回调散落在配置和插件中，真实控制流很难从主图中看见。

## 概念定义

Hook 组合把多个确定性触发点当作一条有顺序、有状态的控制链来设计。每个 Hook 声明触发事件、执行条件、读写对象、优先级、幂等键、失败语义和后续事件；组合层负责冲突检测和执行顺序。

## 工程机制

<table><thead><tr><th>职责</th><th>示例</th><th>失败时</th></tr></thead><tbody><tr><td>编排</td><td>规格确认后启动编码</td><td>不应重复创建同一任务</td></tr><tr><td>治理</td><td>写入生产前等待审批</td><td>阻断调用并保留恢复点</td></tr><tr><td>观测</td><td>记录请求、裁决和回执</td><td>按风险决定阻断或降级</td></tr><tr><td>恢复</td><td>保存 checkpoint、释放租约</td><td>必须可重试且保持幂等</td></tr></tbody></table>

组合清单应能生成可读的控制图，并进入版本管理和回归测试。

## 使用边界

Hook 是机制，不自动成为一种协作拓扑。若多个参与者只是由同一 Hook 管理器按完整计划调用，仍属于编排；只有控制分散到事件参与者的本地规则时，才接近编舞。

<section aria-labelledby="concept-provenance-title" class="concept-provenance">
<h2 id="concept-provenance-title">提出与来源</h2>
<dl>
<div><dt>概念分组</dt><dd><a href="https://adpsagent.com/zh/concepts/#group-collaboration-runtime">协作与运行时控制</a></dd></div>
<div><dt>ADPS 内初始来源</dt><dd>初始问题与实践：王伟；分类整理：ADPS</dd></div>
<div><dt>首次记录</dt><dd><a href="https://adpsagent.com/zh/workshops/collaboration-2026-08-25/">协作模块第一次研讨会</a>（<time datetime="2026-08-25">2026-08-25</time>）</dd></div>
<div><dt>ADPS 整理</dt><dd>ADPS 区分编排、治理、观测和恢复四类职责，并补充顺序、幂等和失败语义。</dd></div>
<div><dt>当前地位</dt><dd>跨模块概念</dd></div>
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
<p><a href="https://adpsagent.com/zh/chronicle/#concepts-hook-composition">在 ADPS Chronicle 中查看</a></p>
</section>

<!-- PAGE-CHRONICLE:END -->
