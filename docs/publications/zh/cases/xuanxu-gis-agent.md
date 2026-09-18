<p style="font-size: 0.9rem; color: var(--color-text-faint); margin-bottom: 1.75rem;"><a href="https://adpsagent.com/zh/cases/" style="color: var(--color-text-muted);">案例库</a><span style="margin:0 0.45rem;">/</span>完整蓝皮书</p>

<header class="publication-head">
<p class="publication-series">ADPS 企业 Agent 系统蓝皮书 · 案例报告 02</p>
<h1>玄宿科技 GIS 数据发布 Agent：把运行经验固化成可验收管线</h1>
<p class="publication-deck">模型参与新管线设计，已认证管线按规则运行，真实地图请求负责最终验收。</p>
</header>

<!-- CASE-V06-ROUTE-xuanxu-gis-agent-True:START -->

<section aria-labelledby="case-route-gis" class="case-route">
<p class="case-route-kicker">贯穿任务</p>
<h2 id="case-route-gis">一份 S-57 海图，怎样取得自动发布资格</h2>
<ol class="case-route-list">
<li><span class="case-step-no">01</span><strong>任务</strong><p>识别海图、处理坐标、生成样式、发布服务、生成浏览页并完成验收。</p></li>
<li><span class="case-step-no">02</span><strong>第一处分叉</strong><p>GeoServer 接受发布配置后，任务过早写成 completed，用户端仍可能看到异常 XML 或空图。</p></li>
<li><span class="case-step-no">03</span><strong>架构修改</strong><p>六阶段管线逐项提交事实文件；运行主链只执行已经认证的 active 能力。</p></li>
<li><span class="case-step-no">04</span><strong>重新验收</strong><p>外部探针发出真实地图请求，检查正文、画面和报告，再提交本次运行。</p></li>
</ol>
</section>

<!-- CASE-V06-ROUTE-xuanxu-gis-agent-True:END -->

## 案例速览

<table>
<thead>
<tr>
<th style="text-align: left;">项目</th>
<th style="text-align: left;">现场信息</th>
</tr>
</thead>
<tbody>
<tr>
<td style="text-align: left;">业务任务</td>
<td style="text-align: left;">将不同格式的 GIS 数据处理后发布到 GeoServer，并生成可供业务使用的地图服务</td>
</tr>
<tr>
<td style="text-align: left;">最难发现的失败</td>
<td style="text-align: left;">发布接口返回成功，真实 GetMap/GetTile 请求仍可能失败；部分 ServiceException 的 HTTP 状态也是 200</td>
</tr>
<tr>
<td style="text-align: left;">核心做法</td>
<td style="text-align: left;">模型参与新管线设计，已认证管线在运行期按规则执行；发布后必须用真实请求和截图验收</td>
</tr>
<tr>
<td style="text-align: left;">关键运行结构</td>
<td style="text-align: left;">六阶段管线、磁盘事实文件、错误规则、失败卡、draft/candidate/active 生命周期</td>
</tr>
<tr>
<td style="text-align: left;">当前证据</td>
<td style="text-align: left;">运行控制台、知识卡、实际地图结果和案例方失败复盘</td>
</tr>
<tr>
<td style="text-align: left;">适用范围</td>
<td style="text-align: left;">输入类型可枚举、处理链重复、错误代价高、外部结果可以自动探测的数据发布任务</td>
</tr>
</tbody>
</table>

## 1. GIS 发布链

GIS 数据发布不等于上传一个文件。系统需要识别格式，确定坐标系，处理数据，生成样式，把数据注册到 GeoServer，配置缓存，最后验证地图服务。

几个常见字段的业务含义如下。

<table>
<thead>
<tr>
<th style="text-align: left;">字段</th>
<th style="text-align: left;">在流程中的含义</th>
</tr>
</thead>
<tbody>
<tr>
<td style="text-align: left;"><code>workspace</code></td>
<td style="text-align: left;">GeoServer 中隔离一组资源的命名空间</td>
</tr>
<tr>
<td style="text-align: left;"><code>store</code></td>
<td style="text-align: left;">指向 PostGIS、栅格文件等真实数据源的连接</td>
</tr>
<tr>
<td style="text-align: left;"><code>layer</code></td>
<td style="text-align: left;">对外发布和请求的地图图层</td>
</tr>
<tr>
<td style="text-align: left;"><code>SRS</code></td>
<td style="text-align: left;">数据使用的空间参考或坐标系</td>
</tr>
<tr>
<td style="text-align: left;"><code>bbox</code></td>
<td style="text-align: left;">数据覆盖的地理边界，浏览器据此定位和缩放</td>
</tr>
</tbody>
</table>

这些值在前一步产生，后一步逐值引用。名称或坐标错一位，接口可能直接失败，也可能发布出位置错误的地图。

玄宿科技的流程还跨越桌面 GIS、GDAL、PostGIS、GeoServer 和 GWC。操作顺序长期依赖工程师记忆，重复发布后很难回答“哪一次运行的哪一步出了问题”。

## 2. 两个现场失败改变了设计

第一个失败来自 S-57 电子海图。一组海图导入 PostGIS 后会按物标类生成上百张表，随后逐表建立 store、发布图层并组成图层组。图层组配置为 `OPAQUE_CONTAINER` 后，成员图层可能从 WMS 列表消失。直接请求 GetMap 返回 `LayerNotDefined`，HTTP 状态仍是 200。只看状态码，系统会把错误结果登记成成功。

第二个失败出现在 WMTS 瓦片请求。GetTile 返回 400，响应含有 `/ by zero`。排查后发现 metatile 尺寸被配置为 `0×0`。官方文档没有说明这个取值的后果，结论来自平台实测。

两个问题分别给出了明确要求。

1. 发布接口自报成功不能作为最终验收。
2. 平台实测经验必须进入下一次运行能读取的规则，不能只留在操作人员记忆里。

## 3. 为什么运行期没有调用模型

团队评估过将 GeoServer REST API 封装为工具，再让模型运行时选择接口和参数。这个方案没有进入主链。GIS 发布的 `workspace`、`store`、`layer`、`SRS` 和 `bbox` 都有严格来源，模型重新生成会增加参数漂移风险。

与此同时，输入意图可以从数据签名确定。目录中包含 `.000` 文件时进入 S-57 管线，包含 `.tif` 时进入栅格管线。未匹配签名就返回明确错误。这里不需要模型猜测用户意图。

团队把开放判断放到设计期：Coding Agent 起草新管线，工程师审阅并完成首次运行，系统验证通过后再认证为 active。运行期只使用已认证规则。

案例方把这项取舍称为**推理资产化**。这个名称指一件具体的事：一次开放推理的结论写成管线声明和错误规则，后续高频运行直接复用。

<table>
<thead>
<tr>
<th style="text-align: left;">决策</th>
<th style="text-align: left;">发生位置</th>
<th style="text-align: left;">运行期动作</th>
</tr>
</thead>
<tbody>
<tr>
<td style="text-align: left;">输入应进入哪条已有管线</td>
<td style="text-align: left;">设计期定义签名</td>
<td style="text-align: left;">查 <code>accepts</code> 表</td>
</tr>
<tr>
<td style="text-align: left;">某个已知错误如何处理</td>
<td style="text-align: left;">失败复盘后写规则</td>
<td style="text-align: left;">按 signature 选择 retry、abort 或 skip</td>
</tr>
<tr>
<td style="text-align: left;">新格式如何处理</td>
<td style="text-align: left;">设计期由模型和人员共同完成</td>
<td style="text-align: left;">未认证前拒绝自动运行</td>
</tr>
</tbody>
</table>

“运行期零 LLM”是当前输入空间下的结果，不是系统目标，也不适合被推广为通用准则。

## 4. 六个阶段怎样完成一次发布

主链固定为六个阶段。每个阶段在独立子进程中运行，编排器只读取返回码、结构化输出和错误签名。

<table>
<thead>
<tr>
<th style="text-align: left;">阶段</th>
<th style="text-align: left;">主要动作</th>
<th style="text-align: left;">必须落下的结果</th>
<th style="text-align: left;">失败时</th>
</tr>
</thead>
<tbody>
<tr>
<td style="text-align: left;"><code>validate</code></td>
<td style="text-align: left;">识别格式并选择 active 管线</td>
<td style="text-align: left;">输入签名、管线 ID、原始文件清单</td>
<td style="text-align: left;">无匹配管线则拒绝</td>
</tr>
<tr>
<td style="text-align: left;"><code>process</code></td>
<td style="text-align: left;">重投影、入库或归一数据</td>
<td style="text-align: left;"><code>processed_crs</code>、<code>processed_bbox</code>、处理后路径</td>
<td style="text-align: left;">不猜缺失坐标系</td>
</tr>
<tr>
<td style="text-align: left;"><code>generate_sld</code></td>
<td style="text-align: left;">生成或选择样式</td>
<td style="text-align: left;">可追溯的样式文件</td>
<td style="text-align: left;">样式契约失败则停止发布</td>
</tr>
<tr>
<td style="text-align: left;"><code>publish</code></td>
<td style="text-align: left;">调用 GeoServer REST 并配置资源</td>
<td style="text-align: left;">workspace、store、layer 等发布回执</td>
<td style="text-align: left;">过最小事实检查后才调用</td>
</tr>
<tr>
<td style="text-align: left;"><code>viewer</code></td>
<td style="text-align: left;">生成浏览页和访问配置</td>
<td style="text-align: left;">可复现的服务地址和视图配置</td>
<td style="text-align: left;">不把页面生成当作验收</td>
</tr>
<tr>
<td style="text-align: left;"><code>verify</code></td>
<td style="text-align: left;">发送真实请求并截图</td>
<td style="text-align: left;"><code>verify_report.json</code>、截图、请求统计</td>
<td style="text-align: left;">失败签名进入规则或人工复盘</td>
</tr>
</tbody>
</table>

<figure>
<img alt="GIS Agent 控制台总览，展示管线目录、数据集和六阶段进度" src="../../assets/zh/cases/xuanxu-gis-agent/assets/console-overview.jpg"/>
<figcaption>控制台把六个阶段映射到真实状态文件。用户可以看到当前数据集停在哪一步，也能打开相应的 metadata、viewer 和验收报告。</figcaption>
</figure>

这条链刻意没有并行。案例方记录过两个数据集并发发布时，其中一个 verify 短暂出现零个瓦片请求成功。当前规模下，团队选择排队执行，换取可复现性。吞吐要求超过排队能力时，这项取舍需要重新评估。

## 5. 状态为什么落在磁盘上

阶段之间不共享进程内对象，状态通过文件传递。

<pre><code class="language-text">run/
  metadata.json       # 输入签名、管线、处理结果和发布坐标
  run-state.json      # 当前阶段、重试次数和状态迁移
  verify_report.json  # 真实请求、截图和验收结论
</code></pre>

`validate` 写识别结果，`process` 追加坐标系和 bbox，下游阶段读取这些值，不重新计算。案例方称这套结构为磁盘事实平面。它遵守“一个事实一个写入者”：同一个 bbox 只有一个权威生产阶段。

文件方式带来四个直接收益：进程退出后仍可审计；重跑时可以跳过已完成阶段；前端、命令行和执行代理共享文件契约；新子进程会加载磁盘上的最新实现。

代价也很具体。状态文件需要 schema 版本，前端轮询与命令行时间精度必须一致，错误前缀若被规则表使用就不能随意改名。部署进入多机、多租户和高并发写入后，文件真源需要迁移到支持事务和隔离的存储。

## 6. 发布后怎样证明地图真的能用

`verify` 不读取 publish 阶段的“成功”字段来替代验收。它请求真实的 GetMap 或 GetTile 地址，至少核对下面三项。

1. HTTP 状态符合预期。
2. `content-type` 是 `image/*`，响应体不是 XML ServiceException。
3. 截图或图像分析能观察到有效地图内容。

<figure>
<img alt="S-57 电子海图 WMTS 服务在三维地球中的实际渲染" src="../../assets/zh/cases/xuanxu-gis-agent/assets/cesium-s57-viewer.jpg"/>
<figcaption>S-57 服务的最终验收对象是业务可以使用的地图结果。发布接口成功、图层已注册和地图可用是三个不同事实。</figcaption>
</figure>

这项机制在 ADPS 中对应[外部验收探针](https://adpsagent.com/zh/concepts/external-acceptance-probe/)：系统离开自身状态，到真实消费端检查结果。它适用于数据库写入、文件交付、支付回执和网页发布等无法只靠内部调用结果判定的任务。

## 7. 一次失败怎样进入下一次运行

运行期只处理已经认识的错误签名，动作限定为 retry、abort 和 skip。缺少空间参考、海图更新链断号等问题不允许自动补猜，系统直接停止。

新的失败由人复盘，并写成五段式失败卡。

<pre><code class="language-yaml">signature: "GetTile=400 and body contains '/ by zero'"
root_cause: "metatile size was configured as 0x0"
fallback: "disable the invalid metatile setting and rerun verify"
fixed_by: "set a safe SDK default"
related_rules: ["wmts-metatile-zero"]
</code></pre>

这张卡同时保存现象、原因、当前处置、永久修复和运行规则。后续运行不需要重新阅读整篇复盘，只读取压缩后的错误签名与动作。原始事实仍可沿 source 字段回查。

<figure>
<img alt="知识卡图谱视图，卡片按管线分组并关联到来源" src="../../assets/zh/cases/xuanxu-gis-agent/assets/knowledge-card2.jpg"/>
<figcaption>知识卡按管线关联。运行规则消费压缩结论，工程师仍能打开卡片核对故障经过和出处。</figcaption>
</figure>

## 8. 新能力怎样取得自动运行资格

新管线经过三个状态。

<table>
<thead>
<tr>
<th style="text-align: left;">状态</th>
<th style="text-align: left;">可以做什么</th>
<th style="text-align: left;">进入下一状态的条件</th>
</tr>
</thead>
<tbody>
<tr>
<td style="text-align: left;"><code>draft</code></td>
<td style="text-align: left;">生成、修改和人工检查</td>
<td style="text-align: left;">人员显式触发首次完整运行</td>
</tr>
<tr>
<td style="text-align: left;"><code>candidate</code></td>
<td style="text-align: left;">保存首跑证据，等待认证</td>
<td style="text-align: left;">六阶段通过，真实请求和截图验收成功</td>
</tr>
<tr>
<td style="text-align: left;"><code>active</code></td>
<td style="text-align: left;">自动匹配输入并运行</td>
<td style="text-align: left;">人员确认认证</td>
</tr>
</tbody>
</table>

活跃管线的当前版本与认证版本不一致时，系统自动退回 candidate。一次代码修改不会沿用旧认证继续自动运行。

模型在生长期生成脚手架，人员决定是否认证，运行时只接受 active 管线。这个生命周期比“生成后直接上线”多了首跑证据和明确责任人，也比每次运行都请人批准更适合重复任务。

<!-- CASE-V06-REPLAY-xuanxu-gis-agent-True:START -->

<section aria-labelledby="replay-gis" class="case-replay">
<h2 id="replay-gis">同一份 S-57 数据重新发布一遍</h2>
<p>运行器不临场猜测。它逐阶段读取上一阶段已经提交的事实。</p>
<ol class="case-replay-list">
<li><span class="case-step-no">01</span><strong>validate</strong><p>文件签名唯一命中一条 active 管线，并保存输入清单。</p></li>
<li><span class="case-step-no">02</span><strong>process</strong><p>GDAL 与 PostGIS 产出处理路径、SRS 和 bbox；下游不重复计算。</p></li>
<li><span class="case-step-no">03</span><strong>generate_sld</strong><p>按版本生成样式；合同不完整就停止，不依赖平台默认值。</p></li>
<li><span class="case-step-no">04</span><strong>publish</strong><p>保存 workspace、store、layer 与服务回执，任务仍保持 running。</p></li>
<li><span class="case-step-no">05</span><strong>viewer</strong><p>生成真实访问入口，供探针和人员从消费侧打开。</p></li>
<li><span class="case-step-no">06</span><strong>verify</strong><p>检查响应类型、异常正文、像素内容和截图，生成 acceptance 报告。</p></li>
</ol>
<p class="case-outcome"><strong>提交条件</strong><code>verify</code> 通过后才提交成功；HTTP 2xx 或 publish 回执单独都不够。</p>
</section>

<!-- CASE-V06-REPLAY-xuanxu-gis-agent-True:END -->

## 9. 没有运行期模型，为什么仍把它作为 Agent 案例

名称并不由是否每次调用 LLM 决定。这个系统会感知输入签名，选择能力，修改外部环境，主动验收，按错误签名回退，并通过失败卡和管线生命周期扩展能力。

它的自主范围很窄。签名空间封闭，未知输入拒绝；已接受任务必须留下可验收结果和可查询状态。若只剩一条固定脚本，没有输入识别、能力选择、外部验收和生命周期管理，把它称为 Agent 就没有额外解释价值。

## 10. 复制这套做法时从哪里开始

1. 选一条每周重复发生、输入类型有限、失败可以观察的发布流程。
2. 把完整流程拆成阶段，为每个阶段定义唯一输出和错误签名。
3. 标出必须由程序传递的机械参数，禁止下游重新计算或由模型生成。
4. 设计一项离开系统内部的验收，例如真实请求、回读数据库或打开交付文件。
5. 先记录三次真实失败，再决定哪些可以进入自动 retry，哪些必须 abort。
6. 为能力设置 draft、candidate、active，代码变更后取消旧认证。
7. 连续运行后再评估是否需要并行、动态规划或运行期模型。

这七步不依赖 GIS。数据导入、媒体转码、模型部署、报表发布和静态网站发布都可以使用同样的骨架。

## 11. 失效信号与迁移边界

<table>
<thead>
<tr>
<th style="text-align: left;">当前取舍</th>
<th style="text-align: left;">成立条件</th>
<th style="text-align: left;">出现这些信号时重新设计</th>
</tr>
</thead>
<tbody>
<tr>
<td style="text-align: left;">运行期查表</td>
<td style="text-align: left;">输入签名可枚举</td>
<td style="text-align: left;">用户意图转为开放语言，规则表持续膨胀</td>
</tr>
<tr>
<td style="text-align: left;">顺序执行</td>
<td style="text-align: left;">排队时间可接受</td>
<td style="text-align: left;">批量规模导致 SLA 无法满足</td>
</tr>
<tr>
<td style="text-align: left;">磁盘事实</td>
<td style="text-align: left;">单主机、低并发写</td>
<td style="text-align: left;">多机、多租户或多个写入者竞争同一状态</td>
</tr>
<tr>
<td style="text-align: left;">错误签名回退</td>
<td style="text-align: left;">失败模式可稳定识别</td>
<td style="text-align: left;">未知错误占比持续上升，规则误匹配增加</td>
</tr>
<tr>
<td style="text-align: left;">人工认证能力</td>
<td style="text-align: left;">新管线增长速度可控</td>
<td style="text-align: left;">认证队列成为主要交付瓶颈</td>
</tr>
</tbody>
</table>

错误规则和失败卡来自 GeoServer 与 GIS 领域，不能原样迁移。可复用的是阶段契约、单一事实生产者、外部验收、失败到规则的路径和能力认证过程。

<!-- CASE-V06-EVIDENCE-xuanxu-gis-agent-True:START -->

<section aria-labelledby="evidence-gis" class="case-evidence-section">
<p class="case-evidence-label">原始运行画面</p>
<h2 id="evidence-gis">控制台怎样把数据识别和失败知识交给下一次运行</h2>
<div class="case-evidence-grid">
<figure class="case-evidence"><img alt="玄宿 GIS Agent 数据集识别页面" loading="lazy" src="../../assets/zh/cases/xuanxu-gis-agent/assets/console-datasets.jpg"/><figcaption><strong>数据集与处理事实</strong>输入文件、识别结果和处理产物在同一视图中可查。<span class="case-evidence-proof">截图支持一次运行界面；不推出所有格式均已覆盖。</span></figcaption></figure>
<figure class="case-evidence"><img alt="玄宿 GIS Agent 失败知识卡" loading="lazy" src="../../assets/zh/cases/xuanxu-gis-agent/assets/knowledge-card.jpg"/><figcaption><strong>失败知识卡</strong>现场错误被整理为现象、根因、修复和防复发规则。<span class="case-evidence-proof">截图支持知识卡机制；规则有效性仍需回归测试。</span></figcaption></figure>
</div>
</section>

<!-- CASE-V06-EVIDENCE-xuanxu-gis-agent-True:END -->

## 12. 当前证据与下一步数据

<table>
<thead>
<tr>
<th style="text-align: left;">主张</th>
<th style="text-align: left;">当前依据</th>
<th style="text-align: left;">状态</th>
</tr>
</thead>
<tbody>
<tr>
<td style="text-align: left;">S-57 与栅格输入可按文件签名路由</td>
<td style="text-align: left;">管线 accepts 机制</td>
<td style="text-align: left;">架构与运行说明</td>
</tr>
<tr>
<td style="text-align: left;">HTTP 200 不能证明 WMS 结果可用</td>
<td style="text-align: left;"><code>LayerNotDefined</code> 实测</td>
<td style="text-align: left;">案例方运行证据</td>
</tr>
<tr>
<td style="text-align: left;"><code>/ by zero</code> 来自 0×0 metatile</td>
<td style="text-align: left;">失败复盘与知识卡</td>
<td style="text-align: left;">案例方运行证据</td>
</tr>
<tr>
<td style="text-align: left;">版本漂移会使 active 管线退回 candidate</td>
<td style="text-align: left;">生命周期机制</td>
<td style="text-align: left;">架构说明</td>
</tr>
<tr>
<td style="text-align: left;">该设计在大规模并发下仍优于动态系统</td>
<td style="text-align: left;">尚无对照数据</td>
<td style="text-align: left;">本版不作此结论</td>
</tr>
</tbody>
</table>

下一版应记录每条管线的运行次数、成功率、人工接管率、verify 发现的假成功数、规则命中率和代码变更后的重新认证耗时。

## 13. ADPS 对照

<table>
<thead>
<tr>
<th style="text-align: left;">模式或概念</th>
<th style="text-align: left;">本案例中的实现</th>
</tr>
</thead>
<tbody>
<tr>
<td style="text-align: left;"><a href="https://adpsagent.com/zh/patterns/m4-failure-journals/">M4 失败日记</a></td>
<td style="text-align: left;">五段式失败卡回链错误规则</td>
</tr>
<tr>
<td style="text-align: left;"><a href="https://adpsagent.com/zh/patterns/f2-skill-package/">F2 技能包</a></td>
<td style="text-align: left;">一条带声明、代码、证据和生命周期的管线</td>
</tr>
<tr>
<td style="text-align: left;"><a href="https://adpsagent.com/zh/patterns/a2-plan-and-execute/">A2 规划执行</a></td>
<td style="text-align: left;">六阶段静态计划，依赖在设计期固定</td>
</tr>
<tr>
<td style="text-align: left;"><a href="https://adpsagent.com/zh/patterns/a4-guardrail-sandwich/">A4 护栏三明治</a></td>
<td style="text-align: left;">发布前事实检查，发布后真实请求验收</td>
</tr>
<tr>
<td style="text-align: left;"><a href="https://adpsagent.com/zh/patterns/g3-progressive-commitment/">G3 渐进承诺</a></td>
<td style="text-align: left;">draft、candidate、active 逐级开放权限</td>
</tr>
<tr>
<td style="text-align: left;"><a href="https://adpsagent.com/zh/patterns/x1-observability/">X1 可观测性</a></td>
<td style="text-align: left;">文件状态、控制台、请求记录和截图</td>
</tr>
<tr>
<td style="text-align: left;"><a href="https://adpsagent.com/zh/concepts/reasoning-assetization/">推理资产化</a></td>
<td style="text-align: left;">设计期结论进入管线和规则，运行期复用</td>
</tr>
<tr>
<td style="text-align: left;"><a href="https://adpsagent.com/zh/concepts/disk-fact-plane/">磁盘事实平面</a></td>
<td style="text-align: left;">阶段通过版本化 JSON 交换权威状态</td>
</tr>
</tbody>
</table>

## 案例提供与引用

**案例提供：**熊钰柯（Yuke Xiong），玄宿科技。

**建议引用：**ADPS、熊钰柯，《玄宿科技 GIS 数据发布 Agent：把运行经验固化成可验收管线》，ADPS 企业 Agent 系统蓝皮书·案例报告 02，v0.4，2026。

<div class="document-citation">
<p><a href="https://adpsagent.com/zh/cases/">案例报告目录</a> · <a href="https://adpsagent.com/zh/patterns/">模式目录</a> · <a href="https://creativecommons.org/licenses/by/4.0/" rel="license noopener" target="_blank">CC BY 4.0</a></p>
<p class="publication-disclaimer"><strong>证据边界：</strong>本文记录玄宿科技 GIS 数据发布系统的项目实践。流程、失败案例和架构取舍由案例方熊钰柯提供，尚未经过独立审计。页面截图来自案例运行环境；示例契约由 ADPS 根据公开机制整理，不代表案例方实际字段名。</p>
</div>

<!-- PAGE-CHRONICLE:START -->

<section aria-labelledby="page-chronicle-title" class="page-chronicle">
<h2 id="page-chronicle-title">溯源记录</h2>
<dl>
<div><dt>来源记录</dt><dd><a href="https://adpsagent.com/zh/cases/xuanxu-gis-agent/">玄宿科技 GIS 发布 Agent 案例</a>；案例提供：熊钰柯</dd></div>
<div><dt>来源日期</dt><dd><time datetime="2026-07-30">2026-07-30</time></dd></div>
<div><dt>本页首次公开</dt><dd><time datetime="2026-07-30">2026-07-30</time></dd></div>
</dl>
<p><a href="https://adpsagent.com/zh/chronicle/#cases-xuanxu-gis-agent">在 ADPS Chronicle 中查看</a></p>
</section>

<!-- PAGE-CHRONICLE:END -->
