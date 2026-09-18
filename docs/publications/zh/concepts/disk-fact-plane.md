<p style="font-size: 0.9rem; color: var(--color-text-faint); margin-bottom: 1.75rem;"><a href="https://adpsagent.com/zh/concepts/" style="color: var(--color-text-muted);">概念</a><span style="margin:0 0.45rem;">/</span>概念定义</p>

<header class="publication-head">
<p class="publication-series">ADPS Agent 系统蓝皮书 · 工程概念</p>
<h1>磁盘事实平面：用外置合同连接运行阶段</h1>
<p class="publication-deck">以版本化外置合同承载阶段事实、运行状态和验收证据。</p>
</header>

## 从断点恢复开始

一份地图数据跑过识别、处理和发布后，进程意外中断。系统要回答已经完成什么、产物在哪里、下一步从哪里继续。只保留内存对象或终端日志，无法给出稳定答案。

## 定义

磁盘事实平面使用版本化文件合同保存阶段事实、运行状态和验收证据。进程之间传递路径与引用，不依赖不可恢复的共享内存对象。

玄宿案例包含三类核心文件：

- `metadata.json` 保存输入、处理结果和阶段产物引用；
- `run-state.json` 保存阶段状态、时间、退出码和恢复位置；
- `verify_report.json` 保存外部请求、内容检查和验收结论。

每类事实有唯一写入者，下游只读，不重新计算。控制台是这些事实的投影视图。

## 工程边界

该实现适合单机或受控共享磁盘环境。进入多机、多租户并发写后，事实合同应迁移到具备事务、锁与隔离能力的存储。概念的稳定部分是外置、版本化和可恢复的事实合同，磁盘只是案例中的载体。

## 来源与谱系

- 初始案例：玄宿科技 GIS 数据发布 Agent，案例提供熊钰柯（Yuke Xiong）。
- 历史近邻：file-based IPC、single source of truth、append-only state、materialized projection。
- ADPS 整理：区分阶段事实、运行状态和验收证据，并加入单写者约束。
- 定义地位：案例命名。

<section aria-labelledby="concept-provenance-title" class="concept-provenance">
<h2 id="concept-provenance-title">提出与来源</h2>
<dl>
<div><dt>概念分组</dt><dd><a href="https://adpsagent.com/zh/concepts/#group-system-boundaries">系统边界与状态</a></dd></div>
<div><dt>ADPS 内初始来源</dt><dd>初始实践：熊钰柯</dd></div>
<div><dt>首次记录</dt><dd><a href="https://adpsagent.com/zh/cases/xuanxu-gis-agent/">玄宿科技 GIS 数据发布 Agent 案例</a>（<time datetime="2026-07-30">2026-07-30</time>）</dd></div>
<div><dt>ADPS 整理</dt><dd>ADPS 区分阶段事实、运行状态和验收证据，并补入单写者约束。</dd></div>
<div><dt>当前地位</dt><dd>案例命名</dd></div>
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
<p><a href="https://adpsagent.com/zh/chronicle/#concepts-disk-fact-plane">在 ADPS Chronicle 中查看</a></p>
</section>

<!-- PAGE-CHRONICLE:END -->
