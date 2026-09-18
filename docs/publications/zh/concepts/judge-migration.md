<p style="font-size:0.9rem;color:var(--color-text-faint);margin-bottom:1.75rem;"><a href="https://adpsagent.com/zh/concepts/">概念</a><span style="margin:0 0.45rem;">/</span>概念定义</p>

<header class="publication-head"><p class="publication-series">ADPS Agent 系统 · 工程概念</p><h1>裁判迁移</h1><p class="publication-deck">跟踪验收标准怎样从需求阶段移交到测试、评审、部署和业务结果。</p></header>

## 应用背景：同一个“正确”在不同阶段由不同对象证明

需求阶段，产品负责人用验收条件判断方案是否对题；编码阶段，测试用例判断实现是否符合接口；发布阶段，部署检查判断版本能否运行；上线以后，业务结果说明用户是否得到所需结果。若后一阶段没有继承前一阶段的条件，系统可能每一关都通过，最终仍交付错误结果。

## 概念定义

裁判迁移描述一项工作沿生命周期推进时，裁决主体、裁决标准和证据类型的变化及交接。迁移记录至少包括上一阶段确认了什么、下一阶段需要重新证明什么、哪些假设仍未验证，以及最终业务结果如何回链到当时的 Agent 版本和运行轨迹。

## 工程用法

一项“把交通津贴调到 1000”的请求，可以依次形成需求验收条款、参数和权限校验、写后读取、下一薪资周期对账。单元测试证明函数按预期执行，不能替代业务对账；业务对账失败时，也要能追到当时采用的政策版本、批准记录和工具回执。

## 使用边界

裁判迁移关注证据链的连续性，不主张由一个中央评审者包办全部阶段。各阶段可以保留专业裁判，但交接合同需要携带仍有效的约束和尚待验证的结论。

<section aria-labelledby="concept-provenance-title" class="concept-provenance">
<h2 id="concept-provenance-title">提出与来源</h2>
<dl>
<div><dt>概念分组</dt><dd><a href="https://adpsagent.com/zh/concepts/#group-verification-governance">评测、反思与治理</a></dd></div>
<div><dt>ADPS 内初始来源</dt><dd>ADPS 内初始提出：黄佳</dd></div>
<div><dt>首次记录</dt><dd><a href="https://adpsagent.com/zh/workshops/perception-2026-08-13/">感知模块第一次研讨会</a>（<time datetime="2026-08-13">2026-08-13</time>）</dd></div>
<div><dt>ADPS 整理</dt><dd>ADPS 将需求、测试、评审、部署和业务结果中的裁判类型及其交接整理为生命周期问题。</dd></div>
<div><dt>当前地位</dt><dd>候选概念</dd></div>
</dl>
</section>

<div class="document-citation"><p><a href="https://adpsagent.com/zh/concepts/">概念目录</a> · <a href="https://adpsagent.com/zh/workshops/">研讨会</a> · <a href="https://creativecommons.org/licenses/by/4.0/" rel="license noopener" target="_blank">CC BY 4.0</a></p></div>

<!-- PAGE-CHRONICLE:START -->

<section aria-labelledby="page-chronicle-title" class="page-chronicle">
<h2 id="page-chronicle-title">溯源记录</h2>
<dl>
<div><dt>来源记录</dt><dd><a href="https://adpsagent.com/zh/workshops/perception-2026-08-13/">感知模块第一次研讨会</a>（<time datetime="2026-08-13">2026-08-13</time>）</dd></div>
<div><dt>来源日期</dt><dd><time datetime="2026-08-13">2026-08-13</time></dd></div>
<div><dt>本页首次公开</dt><dd><time datetime="2026-08-26">2026-08-26</time></dd></div>
</dl>
<p><a href="https://adpsagent.com/zh/chronicle/#concepts-judge-migration">在 ADPS Chronicle 中查看</a></p>
</section>

<!-- PAGE-CHRONICLE:END -->
