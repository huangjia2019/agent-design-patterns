<p style="font-size: 0.9rem; color: var(--color-text-faint); margin-bottom: 1.75rem;">
<a href="https://adpsagent.com/zh/patterns/" style="color: var(--color-text-muted);">模式矩阵</a>
<span style="margin: 0 0.45rem;">/</span>模式白皮书<span style="margin: 0 0.45rem;">/</span>P4
            </p>

<header class="publication-head">
<p class="publication-series">ADPS Agent 设计模式白皮书</p>
<h1>P4 · Multi-Modal Fusion · 多模态融合</h1>
<p class="publication-deck">对图像、文本、表格和日志分别解析，再将结果合并为统一的推理输入。</p>
</header>

<table>
<tbody>
<tr>
<td style="text-align: left;"><strong>坐标</strong></td>
<td style="text-align: left;">感知 Perception × 并行 Parallel（撒）</td>
</tr>
<tr>
<td style="text-align: left;"><strong>成本</strong></td>
<td style="text-align: left;">高（成本随 specialist 处理路径和 vision 调用增加）</td>
</tr>
<tr>
<td style="text-align: left;"><strong>模式组</strong></td>
<td style="text-align: left;">感知模式</td>
</tr>
<tr>
<td style="text-align: left;"><strong>模式简介</strong></td>
<td style="text-align: left;">对图像、文本、表格和日志分别解析，再将结果合并为统一的推理输入。</td>
</tr>
</tbody>
</table>

---

## 问题

企业输入通常混合 PDF、图表、表格、扫描件和日志。将整份研报直接提交给 vision 模型，可能看错图表中的数量级；全部 OCR 为纯文本，又会丢失柱状图和饼图中的空间关系，只留下“图表显示市场份额”一类低信息量描述。

多模态融合在数据进入 context 前选择处理路径：空间关系明显的内容进入 vision，结构化数据转换为文本或表格，装饰性内容直接丢弃。处理结果随后作为分诊、压缩和检索的输入。

## 坐标说明：感知 × 并行

- **纵轴 · 感知**：融合处理的是多通道输入（PDF、图、音、结构化数据）合成统一表示，是感知最原始的"融合"问题，发生在推理之前。
- **横轴 · 并行**：每一路数据同时交给各自的 specialist 处理器（PDF parser、OCR、table extractor、日志 sub-agent）**并行转换**，各路互不依赖、可同时跑，再由一个 fuser 把多路结果**聚合（gather）**成统一的 prompt content。这是典型的扇出—聚合（fan-out / gather）：N 路并行处理 + 一次合并，不是单链顺序，也不是单点路由。

## 解决方案与机制

融合先为每类数据选择表示形式，再执行合并。空间关系承载信息时保留图像，行列结构承载信息时转换为 markdown。

<table>
<thead>
<tr>
<th style="text-align: left;">输入类型</th>
<th style="text-align: left;">默认处理</th>
<th style="text-align: left;">成本对比</th>
</tr>
</thead>
<tbody>
<tr>
<td style="text-align: left;">架构图、流程图</td>
<td style="text-align: left;">视用途保留原图，或转换为 Mermaid 等结构化表示</td>
<td style="text-align: left;">结构化表示便于检索和修改，原图用于保留布局细节</td>
</tr>
<tr>
<td style="text-align: left;">表格、结构化数据</td>
<td style="text-align: left;">转 GitHub Flavored Markdown 或结构化记录</td>
<td style="text-align: left;">便于精确读取单元格并减少视觉解析歧义</td>
</tr>
<tr>
<td style="text-align: left;">chart、heatmap</td>
<td style="text-align: left;">保留图但只做检索 anchor，要数字走 chart→CSV 二次提取</td>
<td style="text-align: left;">vision 直读 chart 准确率低，不能当推理引擎用</td>
</tr>
<tr>
<td style="text-align: left;">长日志（&gt;&gt; 窗口）</td>
<td style="text-align: left;">三层流水线</td>
<td style="text-align: left;">见下</td>
</tr>
</tbody>
</table>

vision 成本取决于模型、分辨率和 detail 设置，不能用一组固定数字跨模型比较。上线前应使用自己的文档样本记录每条路径的 token、延迟、解析质量和缓存命中。长日志可采用三级流水线：先用 grep、awk、jq 过滤无关内容，再由 sub-agent 生成结构化摘要，最后只把 JSON 和原始日志指针写入主 context。

## 适用场景

- **金融研报分析**：PDF 表格 + 分析师文字 + 市场规模图表，每一路单独看都不完整，必须拼起来才能下判断。
- **保险理赔**：事故照片 + 报案文本 + 结构化保单数据合一。
- **运维事故响应**：监控截图 + 长日志片段 + 配置文件，长日志必走三层流水线。
- **任何输入混着结构化和非结构化的场景**：判断标准是各路信息是否互补——如果只是同一信息的重复表达，跳过融合直接进推理，融合是有成本的。

## 已知失效方式

- **看错图**：chart 直读可能看错数量级，而且错误会沿多轮推理传播。对策是 cross-field consistency check：图中提取的数字要与正文、表格或原始数据核对，对不上就进入人工评审；后续轮次继续引用时应保留图源和提取方法。
- **图像输入成本失控**：Agent loop 的每一步都重新提交完整图像，会迅速放大调用成本。应设置金额、token、运行时长和递归深度预算，按任务需要选择缩略图、裁剪区域和 prompt cache。
- **sub-agent 循环与 finding 丢失**：handoff 截断长文本后，下游可能拿到残缺指令并反复询问上游。完整 finding 应写入 state store，context 只传 pointer ID；每个 sub-agent 启动前声明预算和终止条件，超限时由运行时中止并保留已有产物。该场景用于说明风险机制，不对应已核验的企业事故数字。
- **截断阈值一刀切**：不同工具要按信息分布制定保留策略。bash 输出通常需要同时保留开头命令信息和结尾错误栈，read\_file 则要结合文件类型决定保留头部、尾部或相关片段。统一比例容易丢掉关键证据。

## 验证指标

- **按形态的 token 占比**：分别观察 image、table、text 和 log 的占用趋势。某一形态相对本地基线突然增长时，检查转换路径、重复提交和缓存是否失效。
- **agent loop 的预算触发情况**：记录金额、token、运行时长和递归深度限制的触发与拦截。预算没有生效或只能在调用后发现超限，都属于运行时缺陷。
- **chart 路径的二次提取率**：走 vision 的 chart 中有多少做了 chart→CSV 提取再计算。直接拿 vision 输出的数字做推理是高风险信号。

## 最小实现

```
fuse(inputs):                       # inputs 是多路异构输入
    对每一路按形态分发：
        TEXT   → 直接进 content
        IMAGE  → base64 走 vision（空间信息是信号才走这条）
        TABLE  → 转 markdown（结构是主要信号）
        PDF    → 抽目录 + 定位关键页 + 关键图走 vision + 表转 md + 装饰图丢
        LOG    → bash 预过滤 → sub-agent 摘要 → 结构化 JSON 回主 context
        AUDIO  → STT 转文本
    合并成统一 content blocks，返回 + 一份 trace（每路 modality / tokens_out / method）
health_check：按形态盯 token 占比，异常形态早报警
```

specialist 工具（ocr / stt / pdf\_extract / log\_subagent / bash\_filter）通过依赖注入接入。迁移环境时只需替换具体实现，例如将 OCR 从 Textract 切换到本地引擎。cv2、pyaudio、pdfplumber 等多模态依赖应在函数内延迟导入，并处理 ImportError，避免 headless 环境在启动阶段失败。

## 场景化示例

设想一个研报分析 Agent 经历三版实现。第一版把整份 PDF 提交给 vision，图表中的数量级被误读；第二版把全文 OCR 为纯文本，又丢失了图表的空间关系。第三版先提取目录并定位关键页，关键图保留原图，表格转换为 markdown，装饰图不进入 context，图中数字再与正文和表格交叉核对。这个演进说明，多模态融合的关键是为每种信息形态选择合适的表示，并保留来源与核验路径。

## 相邻模式

- **上下文分诊（P1）、语义压缩（P2）、渐进发现（P3）**：融合先统一输入形态，随后再进行筛选、压缩和主动检索。
- **扇出聚合（C2，协作模块）**：长日志流水线可由多个 specialist 处理器并行解析，再由中央 fuser 合并结果。
- **分层记忆（Memory 模块）**：Memory Pointer Pattern 将完整产物存入外部 store，在 context 中仅传递 pointer。

## 工程判断

多模态融合需要为不同数据形态选择解析、压缩和对齐方法，并控制进入上下文的信息量。目标是在保留结构信号的前提下降低无关内容。

## 企业证据

<p class="evidence-empty">当前没有与本模式绑定的公开评审案例。模式定义不因此视为已经获得企业验证。</p>

<p style="font-size: 0.88rem; color: var(--color-text-muted);">案例收录要求说明业务约束、实现结构、已知失败和迁移边界。参见 <a href="https://adpsagent.com/zh/join/">贡献与评审规则</a>。</p>

<div class="document-citation">
<p><strong>引用建议：</strong>ADPS，《P4 多模态融合》，Agent 设计模式白皮书 v0.3，2026-07-30。</p>
<p><a href="https://adpsagent.com/zh/patterns/">模式目录</a> · <a href="https://github.com/huangjia2019/agent-design-patterns" rel="noopener" target="_blank">参考实现</a> · <a href="https://creativecommons.org/licenses/by/4.0/" rel="license noopener" target="_blank">CC BY 4.0</a></p>
<p class="publication-disclaimer"><strong>文档状态：</strong>本页为公开评审稿。模式定义与分类可供讨论和引用；场景化示例用于说明机制，不代表已经核验的企业案例。具名实践另见<a href="https://adpsagent.com/zh/cases/">案例库</a>。ADPS 欢迎业界提交带来源、测量口径和发布授权的案例。</p>
</div>

<!-- PAGE-CHRONICLE:START -->

<section aria-labelledby="page-chronicle-title" class="page-chronicle">
<h2 id="page-chronicle-title">溯源记录</h2>
<dl>
<div><dt>来源记录</dt><dd>ADPS 模式白皮书；先行工作与参考资料见正文</dd></div>
<div><dt>本页首次公开</dt><dd><time datetime="2026-06-07">2026-06-07</time></dd></div>
</dl>
<p><a href="https://adpsagent.com/zh/chronicle/#patterns-p4-multi-modal-fusion">在 ADPS Chronicle 中查看</a></p>
</section>

<!-- PAGE-CHRONICLE:END -->
