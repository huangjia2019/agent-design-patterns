<p style="font-size: 0.9rem; color: var(--color-text-faint); margin-bottom: 1.75rem;"><a href="https://adpsagent.com/workshops/">Workshops</a><span style="margin: 0 0.45rem;">/</span>Cross-cutting engineering · Evaluation and validation</p>

<header class="publication-head">
<p class="publication-series">ADPS Design Pattern Workshop Series</p>
<h1>Agent Evaluation and Validation Workshop</h1>
<p class="publication-deck">Task design, scoring, and regression tests for vehicle interfaces, product classification, AI-assisted development, and engineering drawing review.</p>
</header>

<p class="publication-date">29 September 2026</p>

<table class="workshop-roster"><thead><tr><th>Role</th><th>Name</th><th>Public role</th></tr></thead><tbody>
<tr><td>Host</td><td>Jia Huang</td><td>ADPS co-founder; author of Manning's <em>Designing AI Agents</em></td></tr>
<tr><td>Host</td><td>Fei Gao</td><td>Technical lead of software-testing agent AUUO.ai; formerly an architect at Kuaishou and iQIYI</td></tr>
<tr><td>Speaker</td><td>Likun Zhao</td><td>Quality expert, Ant Group's Alipay technology division</td></tr>
<tr><td>Speaker</td><td>Dong Zhang</td><td>Expert engineer at Tencent; head of Wukong R&amp;D security</td></tr>
<tr><td>Speaker</td><td>Xianglong Huang</td><td>Founder of Beijing Weinian Intelligent; author of OpenLogos and RunLogos</td></tr>
<tr><td>Speaker</td><td>Haili Zhang</td><td>Author of <em>LangGraph in Practice</em> and <em>LangChain in Practice</em>; LangChain Ambassador</td></tr>
<tr><td>Speaker</td><td>Bo Li</td><td>Senior engineer and chief engineer at a planning and design institute</td></tr>
<tr><td>Organizer</td><td>Pingping Bai</td><td>ADPS secretary; organizer of AI R&amp;D conferences</td></tr>
</tbody></table>

## 1. Evaluating software, agent products, and research workflows

Jia Huang introduced three examples with different evaluation targets: software rewritten with AI must still meet its requirements; a map-publishing agent must produce usable maps; an agent arranging drug-research calculations must help researchers choose the next experiment.

The software-migration example concerns response order. Suppose an application must return results in request order, but a new implementation scrambles them. A coding agent could fix the implementation or relax the test to check only that the same items are present. Both changes could make the test pass. If callers still require ordered results, the implementation needs fixing. If the requirement changes, the requirement owner must confirm that decision and reviewers must check affected callers before changing the test. This is a teaching example, not a reported incident in a particular migration.

<figure class="workshop-diagram"><a href="../../assets/images/workshops/evaluation-opening-software-zh.png"><img alt="Chinese diagram comparing a response-order fix with a relaxed test assertion" loading="lazy" src="../../assets/images/workshops/evaluation-opening-software-zh.png"/></a><figcaption>If response order is still required, fix the code and rerun the original assertion. Changing that requirement needs a check with affected callers.</figcaption></figure>

The GIS example uses a failure documented in an existing case: the server returns HTTP 200, but the response body is an XML <code>LayerNotDefined</code> error. The checker must inspect the response and verify that it can decode a map image. The opening material extends this into a position check: compare known harbor or coastline control points and inspect layer order for hidden features. These position and overlap checks are teaching extensions; the recorded incident was a failed layer request.

<figure class="workshop-diagram"><a href="../../assets/images/workshops/evaluation-opening-gis-zh.png"><img alt="Chinese diagram of response inspection, image decoding, and map-position checks" loading="lazy" src="../../assets/images/workshops/evaluation-opening-gis-zh.png"/></a><figcaption>Map-publishing checks: inspect the response, decode the image, then compare map positions with control points.</figcaption></figure>

Drug research is another teaching example. An experiment needs a candidate molecule in solution at a specified concentration. Solubility model A predicts that the concentration is achievable; model B predicts that it is not. The agent first checks molecular representations, units, temperature, pH, and each model's applicable range. If the conditions match and the predictions still disagree, a domain specialist can select another calculation method or request a targeted solubility experiment. A third model's vote would not resolve differences in assumptions or input conditions.

To test whether the extra check helps, compare both workflows on molecules with reliable experimental results that were not used to tune either workflow. Under the same budget, count usable candidates wrongly rejected, unsuitable candidates wrongly recommended, and cases requiring a researcher to resolve the disagreement.

<figure class="workshop-diagram"><a href="../../assets/images/workshops/evaluation-opening-science-zh.png"><img alt="Chinese diagram of input checks and follow-up calculations or experiments for conflicting solubility predictions" loading="lazy" src="../../assets/images/workshops/evaluation-opening-science-zh.png"/></a><figcaption>When solubility predictions disagree, compare input conditions before choosing another calculation or an experiment.</figcaption></figure>

## 2. Tasks and environments for vehicle GUI testing

Fei distinguished public leaderboards from product-specific tests. He discussed <a href="https://github.com/open-compass/AgentCompass">AgentCompass</a>, which separates benchmarks, harnesses, models, and environments, and <a href="https://github.com/harbor-framework/harbor">Harbor</a>, which structures task execution and verification. These tools make repeated runs practical, but they do not decide what a particular product ought to do. He used <a href="https://github.com/swe-bench/SWE-bench">SWE-bench</a> to illustrate a task with a repository issue, a patch, and executable tests. A research report or GUI task also needs checks on citations, interface state, and intermediate actions.

In Fei's vehicle-display work, some devices cannot be controlled through a debugging interface. A testing agent reads a camera image and operates the screen through a robotic arm. When the vehicle interface changes, the team collects images of the new icons and screens, labels samples, and tests recognition and action again. An early version observed the screen after every character typed. It could enter text, but took too long to be useful; batching part of the keyboard sequence reduced the time spent observing the screen.

Jia asked how to compare outputs such as reports and websites, where there is no single reference answer. Fei recommended defining the product task, then checking executable behavior, required content, citation validity, and style separately. Failed runs should record the incomplete step. For example, a nonexistent citation and an omitted analysis topic require different corrections and follow-up checks.

## 3. Business datasets and judge calibration

Likun described agents used in consumer, merchant, and internal operations settings. Functionality, latency, and time to first token remain conventional software tests. Whether an answer serves the business calls for a domain-specific dataset and scoring rules. Her examples of dataset inputs included manually constructed questions, real user requests, production failures, and synthetic questions. The right sample count depends on the task rather than a universal target.

For product classification, people label a reference set, while another model scores a larger batch. Cases where the model judge and people disagree become calibration material: the team checks the sample, classification rules, and judge prompt. Shared platform teams can provide checks such as safety and multi-turn behavior, while product teams maintain their own cases and metrics.

Jia also asked how a company manages many separately built agents. Likun described a shared platform with team-level management. She said consumer-facing applications needed further observation, while some business-facing customer-service, strategy, and creative tasks were already saving processing time.

## 4. End-to-end evaluation and repeated-run stability

Dong began with a business scenario. In security testing, a team can first cover the common, high-impact categories, set a release threshold, and add new failure cases from production. Recall asks how many genuine problems were found; precision asks how many reported findings were real. Other domains need different measures. A generic benchmark cannot replace local acceptance criteria.

His use of “black box” did not mean deleting traces. Evaluate the full task first. If it meets the agreed outcome, there may be little value in scoring every internal step. If it fails, split the work into stages and locate the loss of evidence or incorrect decision. Fei pressed him on metrics tied to real tasks. Dong added **stability across repeated runs**: with the same task, model, prompt, and harness, a vulnerability may appear in one run and disappear in another. A single accuracy number hides that variance. A new model version also requires rerunning old cases; newer is not automatically better in every business scenario.

For changes to security-enforcement rules or customer-facing behavior, Dong recommends human review and release approval. Agents can draft tests, analyze failures, propose updates, and cross-check them with other models in development. The responsible person reviews the test results and scope of the change before release.

## 5. Test ledgers and code review in AI-assisted development

Xianglong described the OpenLogos and RunLogos workflow. A requirement becomes scenarios and test cases; code and test results retain the case IDs. Each run writes a structured ledger so acceptance can check every ID. A long task is delivered in smaller slices, each tested before the next one, followed by a complete regression. A failed test or broken ledger stops the flow for human attention.

He uses one model to implement and another to review. A review finding needs a code location, severity, and evidence. The implementer must answer whether it fixed, rejected, or deferred each finding. Without a limit, the reviewers can keep producing smaller objections indefinitely, so the process distinguishes discovery from convergence and escalates unresolved high-risk issues to a person.

The failure mode he emphasized was overdesign. An agent may write plausible new code without reading existing mechanisms closely enough, creating another cache, event source, or rate limiter. Review therefore asks whether the behavior already exists and points to the code that can be reused. Even the original mechanism should be reconsidered when a fix adds another one. Xianglong also warned that test code, ledgers, and evaluation rules are software and can be wrong themselves. As the suite grows, a full run after every small edit becomes expensive; selective and parallel regression require their own design.

## 6. Required documents for engineering drawing review

Bo approached the question from a planning and design institute. He first built assistance for one discipline, then worked toward cross-discipline review in which engineers inspect the same project facts and reconcile conflicting comments. He does not apply a single automation rate to every task. Higher-risk decisions remain with people; lower-risk document checks and rule prompts can be automated more readily.

Bo's example was a large project's drawing review. If a prerequisite geotechnical report is missing, the system should pause formal review, list the missing documents, and wait for them. The evaluation must check whether it detects the omission and stops the review steps that depend on that report.

At the Skill, single-discipline agent, and multi-agent stages, the team evaluates assistance with engineering work, completion of discipline-specific tasks, and consistency across disciplines respectively. Bo recommends keeping real project cases in the test set. For some drawing tasks, he finds images and PDFs more workable model inputs than direct CAD/BIM files, so input format also needs testing.

## 7. Checks to carry into an evaluation plan

<figure class="workshop-diagram"><a href="../../assets/images/workshops/evaluation-evidence-loop-en.svg"><img alt="Evaluation workflow showing tasks, run conditions, verification, and failure cases added to subsequent tests" loading="lazy" src="../../assets/images/workshops/evaluation-evidence-loop-en.svg"/></a><figcaption>Evaluation workflow: check results against business requirements and add failed cases to subsequent tests.</figcaption></figure>

<table class="evaluation-checklist"><thead><tr><th>Decision</th><th>Question to answer</th></tr></thead><tbody>
<tr><td>Task and outcome</td><td>Whose task is it? What counts as a correct result, a justified stop, or an unacceptable risk?</td></tr>
<tr><td>Run conditions</td><td>Can the data, environment, model, harness, tools, and budget be recorded and replayed?</td></tr>
<tr><td>Judge</td><td>Which checks belong to code, domain rules, model judges, and people? How is a judge calibrated?</td></tr>
<tr><td>Version comparison</td><td>When one main variable changes, what happens to quality, repeatability, cost, and latency?</td></tr>
<tr><td>Release and regression</td><td>Which failures become test cases? Which production changes need human approval?</td></tr>
</tbody></table>

Haili Zhang described two development approaches: organizing existing coding agents to perform development tasks, and building an agent product with a framework such as LangGraph. They expose different ways to collect runtime traces. A detailed framework comparison was deferred to a later discussion.

## 8. Related specifications and cases

- [X2 Evaluation and Validation](https://adpsagent.com/patterns/x2-evals-and-testing/) contains the cross-cutting engineering requirements. This workshop adds business ground truth, judge calibration, repeated-run stability, tests of the evaluation machinery, and human release gates.
- The [Agent Evals and Testing topic](https://adpsagent.com/topics/agent-evals-and-testing/) can hold deeper, domain-specific tasks and verifier designs; this record preserves the exchange that motivated them.
- The [GIS publishing case](https://adpsagent.com/cases/xuanxu-gis-agent/) gives the project context for an API that succeeds while the visible map is wrong. The [Reflection module](https://adpsagent.com/patterns/reflection/) covers what happens to failures after a run.

The workshop did not settle how to reset a long-running interrupted task, how to measure the quality of multiple model reviewers, or who approves changes to a business test set. Those questions need further case work.

The opening material illustrates regression with map publishing. Suppose the old version accepts an HTTP 200 XML error as a map. After adding response-content checks, rerun that failure and test a separate set of similar errors and valid maps. If the new check rejects valid maps as well, it needs further correction. Test records identify the code version, tool configuration, and applicable map types so the responsible person can decide whether to approve the new version.

<figure class="workshop-diagram"><a href="../../assets/images/workshops/evaluation-opening-regression-zh.png"><img alt="Chinese diagram of error cases and valid-map regression tests after a map-publishing fix" loading="lazy" src="../../assets/images/workshops/evaluation-opening-regression-zh.png"/></a><figcaption>Map-publishing regression: check that XML errors are detected and valid maps can still be published.</figcaption></figure>

<p class="publication-note publication-note-end">Based on the 29 September 2026 meeting transcript. Internal implementation details have been anonymized. The original Chinese opening slides are from Jia Huang's v0.4 deck; the additional diagram was prepared after the workshop.</p>

<!-- PAGE-CHRONICLE:START -->
<section aria-labelledby="page-chronicle-title" class="page-chronicle">
<h2 id="page-chronicle-title">Source record</h2>
<dl>
<div><dt>Source</dt><dd>Agent Evaluation and Validation workshop, <time datetime="2026-09-29">29 September 2026</time></dd></div>
<div><dt>Source date</dt><dd><time datetime="2026-09-29">29 September 2026</time></dd></div>
<div><dt>First published</dt><dd><time datetime="2026-10-01">1 October 2026</time></dd></div>
</dl>
<p><a href="https://adpsagent.com/chronicle/">ADPS source timeline</a></p>
</section>
<!-- PAGE-CHRONICLE:END -->
