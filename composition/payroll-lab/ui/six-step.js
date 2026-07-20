const state = {
  view: "seams",
  payload: null,
  meta: null,
};

const $ = (selector) => document.querySelector(selector);
const $$ = (selector) => Array.from(document.querySelectorAll(selector));

function text(selector, value) {
  const node = $(selector);
  if (node) node.textContent = value;
}

function renderLectures() {
  $("#lecture-nav").innerHTML = state.meta.lectures
    .map(
      (lecture) => `
        <a href="${lecture.href}" class="lecture-item ${lecture.active ? "active" : "inactive"}">
          <div class="lecture-number">${lecture.number}</div>
          <div>
            <strong>${lecture.title}</strong>
            <span>${lecture.pattern}</span>
          </div>
        </a>
      `,
    )
    .join("");
}

function renderViewButtons() {
  $("#view-control").innerHTML = state.meta.views
    .map(
      (view) => `
        <button
          type="button"
          class="scenario-button ${view.id === state.view ? "active" : ""}"
          data-view="${view.id}"
        >${view.label}</button>
      `,
    )
    .join("");

  $$(".scenario-button").forEach((button) => {
    button.addEventListener("click", () => {
      state.view = button.dataset.view;
      renderViewButtons();
      renderMethod();
    });
  });
}

function renderSteps(run) {
  $("#step-flow").innerHTML = run.steps
    .map(
      (step) => `
        <div>
          <span>${step.number}</span>
          <strong>${step.name}</strong>
          <small>${step.artifact}</small>
        </div>
      `,
    )
    .join("");
}

function candidateState(candidate) {
  if (!candidate.trial_ready) return ["接缝拦下", "blocked"];
  if (candidate.candidate_id === "split-plan-and-settlement") {
    return ["进入消融", "ready"];
  }
  return ["进入对照", "ready"];
}

function renderCandidates(run) {
  $("#candidate-table").innerHTML = run.candidates
    .map((candidate) => {
      const [label, className] = candidateState(candidate);
      const finding = candidate.findings[0];
      const detail =
        finding?.code === "multiple_writers"
          ? "net_amount 同时由规划执行与交接链生产，单一写入权不成立。"
          : finding
            ? `${finding.code}: ${finding.detail}`
            : candidate.rationale;
      return `
        <article class="candidate-row">
          <div>
            <strong>${candidate.patterns.join(" + ")}</strong>
            <span>${candidate.candidate_id}</span>
          </div>
          <p>${detail}</p>
          <span class="candidate-state ${className}">${label}</span>
        </article>
      `;
    })
    .join("");
  text("#framework-conflict", run.framework_conflict);
}

function experimentVerdict(item) {
  const metrics = item.metrics;
  const passes =
    metrics.recovery_success >= 1 &&
    metrics.committed_fact_overwrites <= 0 &&
    metrics.settlement_receipts >= 1;
  if (item.case_id === "baseline") return ["基线缺口", "failed"];
  if (passes) return ["三门通过", "passed"];
  if (item.variant === "完整候选") return ["候选未过门", "failed"];
  return ["暴露贡献", "ablated"];
}

function renderExperiments(run) {
  $("#experiment-rows").innerHTML = run.experiments
    .map((item) => {
      const [label, className] = experimentVerdict(item);
      return `
        <div class="matrix-data-row">
          <div class="matrix-cell matrix-name">
            <strong>${item.name}</strong>
            <span>${item.variant}</span>
          </div>
          <div data-label="恢复" class="matrix-cell metric-value ${item.metrics.recovery_success ? "good" : "bad"}">
            ${item.metrics.recovery_success.toFixed(0)}
          </div>
          <div data-label="提交后覆盖" class="matrix-cell metric-value ${item.metrics.committed_fact_overwrites ? "bad" : "good"}">
            ${item.metrics.committed_fact_overwrites.toFixed(0)}
          </div>
          <div data-label="交接回执" class="matrix-cell metric-value ${item.metrics.settlement_receipts ? "good" : "bad"}">
            ${item.metrics.settlement_receipts.toFixed(0)}
          </div>
          <div class="matrix-cell matrix-verdict">
            <span class="candidate-state ${className}">${label}</span>
          </div>
        </div>
      `;
    })
    .join("");
}

function addDefinition(list, term, detail) {
  const dt = document.createElement("dt");
  const dd = document.createElement("dd");
  dt.textContent = term;
  dd.textContent = detail;
  list.append(dt, dd);
}

function renderArtifacts(run) {
  const baseline = $("#baseline-artifact");
  const decision = $("#decision-artifact");
  baseline.innerHTML = "";
  decision.innerHTML = "";
  addDefinition(baseline, "目标", run.problem.objective);
  addDefinition(baseline, "排除范围", run.problem.excluded_scope.join(" / "));
  addDefinition(
    baseline,
    "基线事实",
    `${run.baseline.before.net_amount} → ${run.baseline.after.net_amount}`,
  );
  addDefinition(
    baseline,
    "实测缺口",
    run.baseline.observed_failures.join(" / "),
  );

  $("#diagnosis-artifact").innerHTML = run.diagnoses
    .map(
      (item) => `
        <div>
          <strong>${item.code}</strong>
          <span>${item.claim}</span>
          <code>${item.evidence_refs[0]}</code>
        </div>
      `,
    )
    .join("");

  const split = run.candidates.find(
    (item) => item.candidate_id === "split-plan-and-settlement",
  );
  const seam = split.seams[0];
  addDefinition(
    decision,
    "工件所有者",
    `${seam.artifact} → ${seam.owner}`,
  );
  addDefinition(
    decision,
    "改写规则",
    `${seam.mutation_policy} / ${seam.version_field}`,
  );
  addDefinition(
    decision,
    "重开触发器",
    run.receipt.reopen_triggers.join(" / "),
  );
}

function renderMethod() {
  if (!state.payload) return;
  const run = state.payload.run;
  const activeView = state.meta.views.find((item) => item.id === state.view);

  text("#objective", run.problem.objective);
  text("#view-description", activeView.description);
  text("#workload", run.workload_ref.replace("fixture://payroll/", ""));
  text("#version", `v${run.version}`);
  const decisionLabels = {
    keep_baseline: "保留基线",
    adopt_candidate: "采用候选",
    reject_all: "全部拒绝",
    needs_review: "等待评审",
  };
  text("#decision-status", decisionLabels[run.receipt.status]);
  text("#receipt-digest", `receipt ${run.receipt_digest}`);
  text(
    "#selected-candidate",
    "采用：职责拆分组合（split-plan-and-settlement）",
  );
  text("#decision-reason", run.receipt_reason_zh);
  text("#current-receipt", run.receipt_digest);
  text("#reopened-version", `v${run.reopened_version}`);

  $("#seam-section").classList.toggle("focus-section", state.view === "seams");
  $("#experiment-section").classList.toggle(
    "focus-section",
    state.view === "decision",
  );
  renderCandidates(run);
  renderExperiments(run);
  renderArtifacts(run);
}

async function runExperiment() {
  const loading = $("#loading");
  const error = $("#error");
  const button = $("#run-button");
  loading.hidden = false;
  error.hidden = true;
  button.disabled = true;

  try {
    const response = await fetch(`/api/42/run/${state.view}`, {
      method: "POST",
    });
    if (!response.ok) {
      const detail = await response.text();
      throw new Error(detail || `HTTP ${response.status}`);
    }
    state.payload = await response.json();
    renderSteps(state.payload.run);
    renderMethod();
  } catch (err) {
    error.textContent = `实验运行失败：${err.message}`;
    error.hidden = false;
  } finally {
    loading.hidden = true;
    button.disabled = false;
  }
}

function bindPanels() {
  $$(".view-tab").forEach((tab) => {
    tab.addEventListener("click", () => {
      $$(".view-tab").forEach((item) => item.classList.remove("active"));
      tab.classList.add("active");
      $$(".view-panel").forEach((panel) => {
        panel.hidden = panel.id !== `${tab.dataset.panel}-view`;
      });
    });
  });
}

async function boot() {
  const response = await fetch("/api/42/meta");
  state.meta = await response.json();
  const requestedView = new URLSearchParams(window.location.search).get("view");
  if (
    requestedView &&
    state.meta.views.some((item) => item.id === requestedView)
  ) {
    state.view = requestedView;
  }
  renderLectures();
  renderViewButtons();
  bindPanels();
  $("#run-button").addEventListener("click", runExperiment);
  await runExperiment();
  if (window.location.hash) {
    document.querySelector(window.location.hash)?.scrollIntoView();
  }
}

boot().catch((err) => {
  const error = $("#error");
  error.textContent = `工作台启动失败：${err.message}`;
  error.hidden = false;
});
