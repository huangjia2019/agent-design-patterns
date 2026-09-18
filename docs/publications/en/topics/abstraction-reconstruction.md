<p style="font-size:0.9rem;color:var(--color-text-faint);margin-bottom:1.75rem;"><a href="https://adpsagent.com/topics/">Topics</a><span style="margin:0 0.45rem;">/</span>Abstraction and Reconstruction</p>

<header class="publication-head"><p class="publication-series">ADPS Topic Study</p><h1>Abstraction and Reconstruction · From field evidence to patterns and back</h1><p class="publication-deck">Control abstraction loss so a pattern can explain common structure and still recover what implementation needs.</p></header>

Pattern languages work by abstraction. Repeated structures become names, problems, mechanisms, and boundaries that teams can compare. Compression also loses information. If the distinctions that determine outcomes disappear, the pattern may look clean but cannot guide implementation.

![Abstraction and reconstruction](../../assets/images/topics/abstraction-reconstruction-en.svg)

## Two directions

**Abstraction** finds recurring roles, state transitions, control points, and evidence across cases.

**Reconstruction** places the pattern back into a concrete setting: who starts the work, which objects change, where current state lives, who may alter it, what proves the result, and who takes over on failure.

## Abstraction-loss test

A distinction must survive when it changes business judgement, state transition, power boundary, evidentiary effect, next action, responsibility, or acceptance.

For example, human approval can be abstracted as a gate. In payroll, code deployment, and content recommendation, the approved object, preconditions, expiry, rollback, and accountable role differ. Those fields determine whether the gate works.

## Use in ADPS

A new pattern should extract common structure from independent examples, define boundaries and failure modes, then reconstruct roles, objects, state, authority, evidence, exceptions, and acceptance in a case. A statement that travels upward but cannot come back down remains a proposition, not a finished pattern.

## Relation to domain modelling

Domain modelling finds objects, language, states, and invariants. Pattern language organizes recurring collaboration and control structures across projects. Reconstruction is where they meet: the domain model gives a pattern precise resource boundaries, authority semantics, and acceptance facts.

## Review questions

1. Which field differences did the abstraction remove?
2. Do any of them change judgement, authority, state, or acceptance?
3. Which data structures, events, and responsible roles appear after reconstruction?
4. Can runtime evidence lead back to the design decision?
5. Does the structure survive a second context, or only the vocabulary?

## Source

The method received its explicit ADPS formulation during the Collaboration Module Workshop on 25 August 2026 and is used to review pattern layering, topology lowering, and human-agent boundaries.

<div class="document-citation"><p><strong>Suggested citation:</strong> ADPS, <em>Abstraction and Reconstruction · From field evidence to patterns and back</em>, ADPS Topic Study, 26 August 2026.</p><p><a href="https://adpsagent.com/topics/">Topic index</a> · <a href="https://adpsagent.com/workshops/collaboration-2026-08-25/">Collaboration workshop</a> · <a href="https://creativecommons.org/licenses/by/4.0/" rel="license noopener" target="_blank">CC BY 4.0</a></p></div>

<!-- PAGE-CHRONICLE:START -->

<section aria-labelledby="page-chronicle-title" class="page-chronicle">
<h2 id="page-chronicle-title">Chronicle</h2>
<dl>
<div><dt>Recorded source</dt><dd>Workshop and case records cited in the article: <a href="https://adpsagent.com/workshops/collaboration-2026-08-25/">Collaboration workshop</a> (<time datetime="2026-08-25">2026-08-25</time>)</dd></div>
<div><dt>Source date</dt><dd><time datetime="2026-08-25">2026-08-25</time></dd></div>
<div><dt>First published on ADPS</dt><dd><time datetime="2026-08-26">2026-08-26</time></dd></div>
</dl>
<p><a href="https://adpsagent.com/chronicle/#topics-abstraction-reconstruction">View in the ADPS Chronicle</a></p>
</section>

<!-- PAGE-CHRONICLE:END -->
