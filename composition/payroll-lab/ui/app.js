const state = {
  scenario: "independent",
  payload: null,
  meta: null,
};

const $ = (selector) => document.querySelector(selector);
const $$ = (selector) => Array.from(document.querySelectorAll(selector));

function text(selector, value) {
  const node = $(selector);
  if (node) node.textContent = value;
}

function metric(value) {
  if (value === undefined || value === null) return "-";
  return Number(value).toFixed(0);
}

function formatDependency(value) {
  const labels = {
    independent: "独立来源",
    ordered: "顺序依赖",
    shared_state: "共享状态",
  };
  return labels[value] || value;
}

function renderLectures() {
  const nav = $("#lecture-nav");
  nav.innerHTML = state.meta.lectures
    .map(
      (lecture) => `
        <div class="lecture-item ${lecture.active ? "active" : "inactive"}">
          <div class="lecture-number">${lecture.number}</div>
          <div>
            <strong>${lecture.title}</strong>
            <span>${lecture.pattern}</span>
          </div>
        </div>
      `,
    )
    .join("");
}

function renderScenarioButtons() {
  const control = $("#scenario-control");
  control.innerHTML = state.meta.scenarios
    .map(
      (scenario) => `
        <button
          type="button"
          class="scenario-button ${scenario.id === state.scenario ? "active" : ""}"
          data-scenario="${scenario.id}"
        >${scenario.label}</button>
      `,
    )
    .join("");

  $$(".scenario-button").forEach((button) => {
    button.addEventListener("click", async () => {
      state.scenario = button.dataset.scenario;
      renderScenarioButtons();
      await runExperiment();
    });
  });
}

function evidenceSummary(run) {
  if (run.scenario === "independent") {
    const divergence = run.proposal.divergences[0];
    return `差异 ${metric(divergence.gap)} 元，低值来源：${divergence.low_sources.join(", ")}`;
  }
  return `确认根因：${run.proposal.confirmed}`;
}

function baselineSummary(run) {
  if (run.scenario === "independent") {
    return "只读一份薪酬库，看不到来源之间的差异。";
  }
  return "四个来源共同读取错的结转值，聚合器把错误判成一致。";
}

function renderExperiment() {
  const run = state.payload.run;
  const card = run.card;
  const outcome = run.outcome;
  const scenarioMeta = state.meta.scenarios.find(
    (item) => item.id === run.scenario,
  );

  text("#question", run.question);
  text("#scenario-description", scenarioMeta.description);
  text("#dependency-shape", formatDependency(card.problem.dependency_shape));
  text("#outcome-state", outcome.state.toUpperCase());
  text("#card-digest", run.card_digest);

  const stateNode = $("#outcome-state");
  stateNode.className = `state-${outcome.state}`;

  text("#baseline-name", run.baseline.pattern);
  text("#baseline-finding", baselineSummary(run));
  text("#baseline-recall", metric(run.baseline.metrics.defect_recall));
  text("#baseline-consensus", metric(run.baseline.metrics.false_consensus));
  text("#baseline-reads", metric(run.baseline.metrics.source_reads));

  text("#proposal-name", run.proposal.pattern);
  text("#proposal-finding", evidenceSummary(run));
  text("#proposal-recall", metric(run.proposal.metrics.defect_recall));
  text("#proposal-consensus", metric(run.proposal.metrics.false_consensus));
  text("#proposal-reads", metric(run.proposal.metrics.source_reads));

  const verdict = $("#verdict-label");
  verdict.textContent =
    outcome.state === "accepted" ? "候选获得采用资格" : outcome.state.toUpperCase();
  verdict.className = `verdict-label ${outcome.state}`;

  const evidence = $("#evidence-list");
  const preflight = run.preflight_findings.map(
    (finding) =>
      `预检拦下手工猜测：${finding.code}。模式前提没有来源证据。`,
  );
  const refs = outcome.evidence_refs.map((ref) => `运行证据：${ref}`);
  evidence.innerHTML = [...preflight, ...refs]
    .map(
      (item, index) => `
        <div class="evidence-item">
          <span class="evidence-index">${String(index + 1).padStart(2, "0")}</span>
          <code>${item}</code>
        </div>
      `,
    )
    .join("");
}

function addDefinition(list, term, detail) {
  const dt = document.createElement("dt");
  const dd = document.createElement("dd");
  dt.textContent = term;
  dd.textContent = detail;
  list.append(dt, dd);
}

function renderCard() {
  const card = state.payload.run.card;
  const assess = $("#assess-panel");
  const route = $("#route-panel");
  const select = $("#select-panel");
  assess.innerHTML = "";
  route.innerHTML = "";
  select.innerHTML = "";

  addDefinition(assess, "目标", card.problem.objective);
  addDefinition(assess, "最小基线的失败", card.problem.observed_baseline_failure);
  addDefinition(assess, "约束", card.problem.constraints.join(" / "));
  addDefinition(assess, "验收输出", card.problem.output_contract);

  addDefinition(route, "数据依赖", formatDependency(card.problem.dependency_shape));
  addDefinition(
    route,
    "候选拓扑",
    card.proposal.patterns.map((item) => item.topology).join(" + "),
  );
  addDefinition(route, "选择理由", card.proposal.rationale);
  addDefinition(
    route,
    "前提证据",
    card.proposal.assumptions
      .map((item) => `${item.claim} [${item.evidence_ref}]`)
      .join(" / "),
  );

  addDefinition(
    select,
    "候选模式",
    card.proposal.patterns.map((item) => item.name).join(" + "),
  );
  addDefinition(
    select,
    "明确排除",
    card.rejected_alternatives
      .map((item) => `${item.candidate_id}: ${item.reason}`)
      .join(" / "),
  );
  addDefinition(
    select,
    "验收门",
    card.experiment.gates
      .map((item) => `${item.metric} ${item.comparison} ${item.target}`)
      .join(" / "),
  );
  addDefinition(select, "回退", card.experiment.rollback_plan);
}

function renderAll() {
  renderExperiment();
  renderCard();
}

async function runExperiment() {
  const loading = $("#loading");
  const error = $("#error");
  const button = $("#run-button");
  loading.hidden = false;
  error.hidden = true;
  button.disabled = true;

  try {
    const response = await fetch(`/api/run/${state.scenario}`, {
      method: "POST",
    });
    if (!response.ok) {
      const detail = await response.text();
      throw new Error(detail || `HTTP ${response.status}`);
    }
    state.payload = await response.json();
    renderAll();
  } catch (err) {
    error.textContent = `实验运行失败：${err.message}`;
    error.hidden = false;
  } finally {
    loading.hidden = true;
    button.disabled = false;
  }
}

function bindViews() {
  $$(".view-tab").forEach((tab) => {
    tab.addEventListener("click", () => {
      $$(".view-tab").forEach((item) => item.classList.remove("active"));
      tab.classList.add("active");
      $$(".view-panel").forEach((panel) => {
        panel.hidden = panel.id !== `${tab.dataset.view}-view`;
      });
    });
  });
}

async function boot() {
  const response = await fetch("/api/meta");
  state.meta = await response.json();
  const requestedScenario = new URLSearchParams(window.location.search).get(
    "scenario",
  );
  if (
    requestedScenario &&
    state.meta.scenarios.some((item) => item.id === requestedScenario)
  ) {
    state.scenario = requestedScenario;
  }
  renderLectures();
  renderScenarioButtons();
  bindViews();
  $("#run-button").addEventListener("click", runExperiment);
  await runExperiment();
}

boot().catch((err) => {
  const error = $("#error");
  error.textContent = `工作台启动失败：${err.message}`;
  error.hidden = false;
});
