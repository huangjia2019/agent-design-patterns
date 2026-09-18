<p style="font-size: 0.9rem; color: var(--color-text-faint); margin-bottom: 1.75rem;"><a href="https://adpsagent.com/zh/concepts/" style="color: var(--color-text-muted);">概念</a><span style="margin:0 0.45rem;">/</span>概念定义</p>

<header class="publication-head">
<p class="publication-series">ADPS Agent 系统蓝皮书 · 工程概念</p>
<h1>外部验收探针：从用户一侧裁决成功</h1>
<p class="publication-deck">从用户一侧发出真实请求，以状态、内容和可见结果裁决成功。</p>
</header>

## 从 HTTP 200 的假成功开始

GeoServer 可能在 HTTP 200 响应中返回 `ServiceException`。发布接口报告成功，用户打开地图仍然看到空白。只看进程退出码或状态码，会把业务失败记成成功。

## 定义

外部验收探针从系统边界外执行与用户交付物一致的动作，并同时检查返回状态、内容和可见结果。系统内部回执属于过程证据；探针结果决定任务提交、重试或失败。

玄宿案例的探针发送真实 WMS / WMTS 请求，检查内容类型与异常正文，并验证截图包含非透明地图内容。结论写入 `verify_report.json`。

## 工程边界

探针应覆盖用户真正依赖的路径，避免调用内部捷径。视觉检查可能受底图、阈值和数据类型影响，需要已知良好样本与回归校准。复杂制图语义仍可能需要人工抽检。

## 来源与谱系

- 初始案例：玄宿科技 GIS 数据发布 Agent，案例提供熊钰柯（Yuke Xiong）。
- 历史近邻：end-to-end test、synthetic probe、health endpoint monitoring。
- ADPS 整理：把外部探针回执接入任务状态机，直接裁决副作用是否提交。
- 定义地位：ADPS 重述。

<section aria-labelledby="concept-provenance-title" class="concept-provenance">
<h2 id="concept-provenance-title">提出与来源</h2>
<dl>
<div><dt>概念分组</dt><dd><a href="https://adpsagent.com/zh/concepts/#group-verification-governance">评测、反思与治理</a></dd></div>
<div><dt>ADPS 内初始来源</dt><dd>初始实践：熊钰柯</dd></div>
<div><dt>首次记录</dt><dd><a href="https://adpsagent.com/zh/cases/xuanxu-gis-agent/">玄宿科技 GIS 数据发布 Agent 案例</a>（<time datetime="2026-07-30">2026-07-30</time>）</dd></div>
<div><dt>ADPS 整理</dt><dd>ADPS 将用户侧探针回执接入任务状态机，用真实结果裁决成功。</dd></div>
<div><dt>当前地位</dt><dd>ADPS 重述</dd></div>
</dl>
</section>

<div class="document-citation">
<p><strong>初始来源：</strong><a href="https://adpsagent.com/zh/cases/xuanxu-gis-agent/">玄宿科技 GIS 数据发布 Agent 案例报告</a>；案例提供：熊钰柯（Yuke Xiong）。</p>
<p><a href="https://adpsagent.com/zh/cases/">案例报告目录</a> · <a href="https://adpsagent.com/zh/patterns/">模式目录</a> · <a href="https://creativecommons.org/licenses/by/4.0/" rel="license noopener" target="_blank">CC BY 4.0</a></p>
</div>

<!-- PAGE-CHRONICLE:START -->

<section aria-labelledby="page-chronicle-title" class="page-chronicle">
<h2 id="page-chronicle-title">溯源记录</h2>
<dl>
<div><dt>来源记录</dt><dd><a href="https://adpsagent.com/zh/cases/xuanxu-gis-agent/">玄宿科技 GIS 数据发布 Agent 案例</a>（<time datetime="2026-07-30">2026-07-30</time>）</dd></div>
<div><dt>来源日期</dt><dd><time datetime="2026-07-30">2026-07-30</time></dd></div>
<div><dt>本页首次公开</dt><dd><time datetime="2026-08-02">2026-08-02</time></dd></div>
</dl>
<p><a href="https://adpsagent.com/zh/chronicle/#concepts-external-acceptance-probe">在 ADPS Chronicle 中查看</a></p>
</section>

<!-- PAGE-CHRONICLE:END -->
