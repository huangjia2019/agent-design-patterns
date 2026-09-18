<p style="font-size:0.9rem;color:var(--color-text-faint);margin-bottom:1.75rem;"><a href="https://adpsagent.com/zh/topics/">专题</a><span style="margin:0 0.45rem;">/</span>抽象—还原</p>

<header class="publication-head"><p class="publication-series">ADPS 专题研究</p><h1>抽象—还原 · 从工程现场到模式，再回到工程现场</h1><p class="publication-deck">控制抽象损失，让模式既能解释共性，也能恢复施工所需的关键差异。</p></header>

模式语言依靠抽象工作。多个项目中反复出现的结构被压缩成名称、问题、机制和边界，团队因此可以比较方案。压缩也会丢信息。若把决定结果的差异一起删掉，模式看起来整洁，回到项目时却无法施工。

![抽象—还原往返](../../assets/images/topics/abstraction-reconstruction-zh.svg)

## 两个方向

**抽象**从实例中寻找重复机制：哪些角色反复出现，状态怎样流转，哪里需要控制，什么证据可以验证。

**还原**把模式重新放入一个具体场景：谁发起任务，操作哪些对象，当前状态在哪里，谁有权改变它，结果由什么事实证明，异常由谁接管。

这两个方向组成往返。抽象结束于模式定义；还原结束于可实现的对象、合同、边界和验收。

## 抽象损失检查

以下差异会改变工程结果，不应在抽象时抹掉：

1. 业务判断会不会变化；
2. 状态迁移是否不同；
3. 权力边界由谁掌握；
4. 证据在流程中是否具有不同效力；
5. 下一动作、责任归属或验收结果是否变化。

例如“人工审批”可以抽象成一个 gate。还原到薪酬、代码发布和内容推荐时，审批对象、前置条件、有效期、回滚能力和责任人完全不同。这些字段决定 gate 是否有效，不能被一个通用按钮代替。

## 在 ADPS 中怎样使用

新模式先从两个以上的独立实例中抽取共同结构，再写清适用边界和失败方式。案例落地时沿角色、对象、状态、权限、证据、异常和验收七个方面还原。若模式只有上行抽象，没有下行还原，它暂时只是一条观点。

这套方法也用于审查术语。名称可以新，机制必须能指向可观察的结构；若只是旧概念换名，不进入目录。

## 与领域建模的关系

领域建模帮助团队发现对象、术语、状态和不变量；模式语言整理跨项目重复出现的协作与控制结构。两者的交点在还原阶段：模式进入领域模型以后，才能得到准确的资源边界、权限语义和验收事实。

## 评审问题

1. 这个抽象省略了哪些现场差异？
2. 被省略的差异会不会改变判断、权限、状态或验收？
3. 模式还原后有哪些明确的数据结构、事件和责任者？
4. 失败时能否从运行证据回到原始设计决定？
5. 第二个场景是否仍然成立，还是只换了术语？

## 来源

该方法在 2026-08-25 ADPS 协作模块研讨会中形成明确表述，并用于审查协作模式的分层、拓扑降阶和人机边界。

<div class="document-citation"><p><strong>引用建议：</strong>ADPS，《抽象—还原 · 从工程现场到模式，再回到工程现场》，ADPS 专题研究，2026-08-26。</p><p><a href="https://adpsagent.com/zh/topics/">专题目录</a> · <a href="https://adpsagent.com/zh/workshops/collaboration-2026-08-25/">协作研讨会</a> · <a href="https://creativecommons.org/licenses/by/4.0/" rel="license noopener" target="_blank">CC BY 4.0</a></p></div>

<!-- PAGE-CHRONICLE:START -->

<section aria-labelledby="page-chronicle-title" class="page-chronicle">
<h2 id="page-chronicle-title">溯源记录</h2>
<dl>
<div><dt>来源记录</dt><dd>正文关联的研讨会与案例：<a href="https://adpsagent.com/zh/workshops/collaboration-2026-08-25/">协作研讨会</a>（<time datetime="2026-08-25">2026-08-25</time>）</dd></div>
<div><dt>来源日期</dt><dd><time datetime="2026-08-25">2026-08-25</time></dd></div>
<div><dt>本页首次公开</dt><dd><time datetime="2026-08-26">2026-08-26</time></dd></div>
</dl>
<p><a href="https://adpsagent.com/zh/chronicle/#topics-abstraction-reconstruction">在 ADPS Chronicle 中查看</a></p>
</section>

<!-- PAGE-CHRONICLE:END -->
