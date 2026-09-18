<p style="font-size:0.9rem;color:var(--color-text-faint);margin-bottom:1.75rem;"><a href="https://adpsagent.com/topics/">Topics</a><span style="margin:0 0.45rem;">/</span>Agent Evaluation and Validation: From Output Scores to System Acceptance</p>

<header class="publication-head">
<p class="publication-series">ADPS Topic Research</p>
<h1>Agent Evaluation and Validation: From Output Scores to System Acceptance</h1>
<p class="publication-deck">Deterministic tests, trajectory evaluation, external acceptance, and production feedback combined into agent release evidence.</p>
</header>

Traditional software tests remain essential for agents. Data structures, permissions, tool contracts, idempotency, and business ledgers still need deterministic assertions. The new difficulty comes from probabilistic outputs, multiple valid paths, external tools, and delayed outcomes. A run may follow a different trajectory and still succeed, or produce fluent text after writing the wrong external state.

Agent evals address this uncertain layer. They work alongside unit tests, integration tests, sandbox acceptance, production monitoring, and human review.

## Why validation is the dividing line

For most of the past decade, practice in artificial intelligence has run ahead of theory. The rapid spread of agents since late 2025 is a clear case: it did not follow from a body of theory, but accumulated as one concrete problem after another was solved. The first question any theory now owes an answer to is why agents sit at the centre of a "large model plus agent" system.

One account that fits the history is that the dividing line runs through verifiability. Without a validation step, a large model can reason on indefinitely and with complete confidence, because nothing in the loop forces it to stop and concede an error. During that period the applications that worked commercially were largely those where truth did not have to be adjudicated. Companionship and emotional value do not depend on external facts to be judged correct, so they escaped the constraint, and they are also not productivity tools.

Tool calls and agents changed this. For the first time, model output could be checked against the external world: calls return, actions have consequences, and results can be compared with a target state. That shift is what moved AI from emotional value toward productivity. The first productivity domain to commercialise at scale was AI-assisted programming, and one reason is that programming carries several layers of native adjudication. Compilers, type checks, test cases, and run results all return a definite verdict within a short interval.

This yields a judgement that runs through the rest of this article. Whether a domain can be turned into productive work by an agent depends substantially on whether its validation can be made to work. Different stages will place the bottleneck on different technologies, but validation remains the variable that sets the ceiling. The [first ADPS Reflection workshop](https://adpsagent.com/workshops/reflection-2026-08-12/) recorded a related conclusion from another direction: when ground truth arrives determines which layer a correction should close in.

## Four terms with different jobs

| Term | Primary job | Typical artefact |
| --- | --- | --- |
| Test | Assert a deterministic contract | Pass/fail, diff, and fault location |
| Eval | Measure capability and regression across uncertain behaviour and repeated trials | Sample evidence, scores, pass rates, and failure clusters |
| Monitoring | Observe behaviour on real production traffic | Runtime events, metrics, alerts, and sampled runs |
| Acceptance | Let users or business rules decide whether delivery is valid | External receipt, visible result, approval, or sign-off |

The boundary between a test and an eval can overlap, and a deterministic grader can appear in either suite. Classify the check by its evidence source, owner, and the release decision it can support.

## Define the system under test

“Test the agent” is too broad. The system under test may be:

- one model or prompt;
- a skill or tool adapter;
- a routing, planning, or workflow component;
- an agent harness with state, authority, and recovery;
- a complete agent product;
- a multi-agent system with hand-offs, aggregation, and termination conditions.

The dataset, execution environment, graders, and release gate change with the system under test. A tool adapter focuses on schema, authority, and idempotency. A long-running agent also requires goal retention, checkpoints, budgets, and recovery tests.

## Six evaluation surfaces

| Surface | Question | Example evidence |
| --- | --- | --- |
| Final outcome | Did the external world reach the target state? | Database fact, business receipt, real request result |
| Trajectory | Were tools, order, and parameters acceptable? | Trace, ActionEvent, task-graph node |
| Single-step decision | Was routing, retrieval, compaction, or approval correct? | Decision label, candidate set, rationale checked against facts |
| Safety and authority | Did the agent cross a boundary, and did refusal or escalation work? | Negative case, sandbox event, approval and rejection record |
| Recovery and long-running progress | Can interruption, retry, and hand-off return to the right task? | Checkpoint, idempotency key, goal version, progress ledger |
| Resource and latency | Does quality fit the latency and cost envelope? | Trial distribution, tokens, latency, tool-call count |

Final outcome is the primary verdict. Trajectory evaluation exposes latent risk and locates failures. Where multiple correct paths exist, strict matching to one golden trajectory rejects valid solutions. Preserve route freedom when outcomes, authority, and mandatory constraints are satisfied.

## An agent test pyramid

<pre><code class="language-text">               Production shadow / canary / business outcomes
                     Human and calibrated model grading
                  Trajectory replay, sandbox, fault injection
               Workflow, external acceptance, system integration
            Tool contracts, permissions, state machines, idempotency
         Schema, parsing, functions, rules, deterministic component tests
</code></pre>

Lower layers are fast, stable, and easy to diagnose. Upper layers approach real value but run more slowly, cost more, and carry more variance. A usable release gate combines evidence across layers instead of treating one aggregate score as complete truth.

## Grader priority

1. External facts and deterministic assertions.
2. Code, rules, schemas, and state-machine checks.
3. Business acceptors or independent simulations.
4. Calibrated model graders.
5. Experts or real users for ambiguous criteria.

Model graders are useful for semantic relevance, style, completeness, and complex trajectories that resist hard rules. They need calibration against human judgements and periodic bias review. Using one uncalibrated model to generate, grade, and rewrite the criteria weakens independence.

## Eval Contract

<pre><code class="language-yaml">eval_id: gis-publish-regression-v7
system_under_test: gis-agent@v5
task: publish_and_verify_layer
input_fixture: fixtures/s57-small-03
environment: geoserver-sandbox@2.25
allowed_tools: [inspect, publish, verify_get_map]
authority: no_production_write
expected_outcomes:
  - layer_is_queryable
  - get_map_contains_visible_content
forbidden_outcomes:
  - modify_unrelated_workspace
graders:
  - schema_contract
  - external_get_map_probe
trials: 5
release_gate:
  capability: all_required_cases_pass
  regression: no_blocking_case_regresses
evidence: artifacts/evals/gis-v7/
owner: geo-platform
</code></pre>

This contract joins the task, environment, authority, positive and negative outcomes, graders, trials, and release gate. Stochastic tasks require repeated trials with each trajectory retained; an average alone can hide a rare but severe failure.

## Dataset lifecycle

1. Derive an initial capability set from specifications and business acceptance criteria.
2. Compress real failures, bad cases, and incidents into replayable regression samples.
3. Add boundary, authority, adversarial, empty-input, and unknown-input cases; keep both positive and negative examples.
4. Version data, environments, graders, and expected outcomes separately.
5. Read failed trajectories, retire stale samples, and split graders whose criteria have become too broad.

Capability evals ask whether the system can complete its target tasks now. Regression evals protect established behaviour from new changes. Their selection logic differs, and releases need both.

## Three engineering cases

### External acceptance replaces internal “success”

The Xuanxu Technology GIS publishing agent encountered a typical false success. A publish API could return success while a real GetMap request still returned `LayerNotDefined`; some error responses also carried HTTP 200. The final acceptor issues real GetMap or GetTile requests from the consumer side and checks protocol results, content type, and visible map content.

### The task graph carries execution and acceptance

The Dongfang Yiteng execution agent uses a task DAG and node state machines for strict dependencies. Node completion passes through a validator, while business-ID provenance, tool receipts, and approval events enter one timeline. The same evidence judges the outcome and locates skipped, missing, or duplicate steps.

### One capability across three environments

The Reflection workshop proposed a practical split. A baseline environment runs stable samples, a daily environment carries real work, and a test environment admits candidate skills and prompts. Candidate and current capabilities coexist until evaluation supports promotion, so one local lesson does not immediately change global behaviour.

## Release evidence flow

<pre><code class="language-text">Production failure or new specification
        ↓
Reproduce and freeze it as a sample
        ↓
Add it to regression; define grader and environment
        ↓
Change a candidate component
        ↓
Run capability + regression + negative cases
        ↓
Read failed trajectories and review graders
        ↓
Release, shadow, canary, or roll back
</code></pre>

New failures should enter regression, but not every production sample deserves permanent retention. Teams need deduplication, retirement, and a way to distinguish model variance, environment faults, grader defects, and actual capability gaps.

## Common failure modes

- Testing only the final text while ignoring external state and side effects.
- Running one trial and treating a lucky success as stable capability.
- Keeping positive cases only, with no refusal, authority, unknown-input, or recovery cases.
- Requiring one golden trajectory for every valid execution path.
- Using model graders without calibration against human labels.
- Changing the agent and grader together, which destroys the comparison baseline.
- Publishing only an aggregate score without sample-level failures, trajectories, or business acceptance evidence.

## Questions for further discussion

A useful session should bring four artefacts: one real bad case, one Eval Contract, one failed trajectory, and the release record that the sample influenced. This makes systems under test, grading rules, and authority boundaries comparable across teams.

## Sources

- [Anthropic: Demystifying evals for AI agents](https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents)
- [LangSmith: Trajectory evaluations](https://docs.langchain.com/langsmith/trajectory-evals)
- [LangSmith: Evaluate a complex agent](https://docs.langchain.com/langsmith/evaluate-complex-agent)
- [OpenAI Evals API](https://platform.openai.com/docs/api-reference/evals/)
- [Xuanxu Technology GIS publishing agent](https://adpsagent.com/cases/xuanxu-gis-agent/)
- [Dongfang Yiteng execution agent](https://adpsagent.com/cases/liangbo-execution-agent/)
- [First ADPS Action Module Workshop](https://adpsagent.com/workshops/action-2026-08-06/)
- [First ADPS Reflection Module Workshop](https://adpsagent.com/workshops/reflection-2026-08-12/)
- [First ADPS Governance Module Workshop](https://adpsagent.com/workshops/governance-2026-08-18/)
- [Governance overview and agent lifecycle](https://adpsagent.com/patterns/governance/)

<div class="document-citation"><p><strong>Suggested citation:</strong> ADPS, <em>Agent Evaluation and Validation: From Output Scores to System Acceptance</em>, ADPS Topic Research, 2026-08-14.</p><p><a href="https://adpsagent.com/topics/">Topic index</a> · <a href="https://creativecommons.org/licenses/by/4.0/" rel="license noopener" target="_blank">CC BY 4.0</a></p><p class="publication-disclaimer">Topics synthesize engineering questions that cross several modules. Pattern definitions, attributed cases, and workshop records remain authoritative on their own pages.</p></div>

<!-- PAGE-CHRONICLE:START -->

<section aria-labelledby="page-chronicle-title" class="page-chronicle">
<h2 id="page-chronicle-title">Chronicle</h2>
<dl>
<div><dt>Recorded source</dt><dd>Workshop and case records cited in the article: <a href="https://adpsagent.com/cases/liangbo-execution-agent/">Dongfang Yiteng execution agent</a> (<time datetime="2026-06-19">2026-06-19</time>); <a href="https://adpsagent.com/cases/xuanxu-gis-agent/">Xuanxu Technology GIS publishing agent</a> (<time datetime="2026-07-30">2026-07-30</time>); <a href="https://adpsagent.com/workshops/action-2026-08-06/">First ADPS Action Module Workshop</a> (<time datetime="2026-08-06">2026-08-06</time>); <a href="https://adpsagent.com/workshops/reflection-2026-08-12/">First ADPS Reflection Module Workshop</a> (<time datetime="2026-08-12">2026-08-12</time>)</dd></div>
<div><dt>Community contribution</dt><dd>The section “Why validation is the dividing line” was proposed by <a href="https://github.com/wikimatt" rel="noopener" target="_blank">@wikimatt</a> through <a href="https://adpsagent.com/contribute/">passage discussion</a> and edited by ADPS (<time datetime="2026-09-11">2026-09-11</time>). Revisions are recorded in the <a href="https://adpsagent.com/changes/">change log</a>.</dd></div>
<div><dt>Source date</dt><dd><time datetime="2026-06-19">2026-06-19</time></dd></div>
<div><dt>First published on ADPS</dt><dd><time datetime="2026-08-14">2026-08-14</time></dd></div>
</dl>
<p><a href="https://adpsagent.com/chronicle/#topics-agent-evals-and-testing">View in the ADPS Chronicle</a></p>
</section>

<!-- PAGE-CHRONICLE:END -->
