const state = {
  mode: "local-only",
  payload: null,
  meta: null,
};

const $ = (selector) => document.querySelector(selector);
const $$ = (selector) => Array.from(document.querySelectorAll(selector));

function text(selector, value) {
  const node = $(selector);
  if (node) node.textContent = value;
}

function short(value) {
  if (!value) return "-";
  return value.length > 18 ? `${value.slice(0, 16)}...` : value;
}

const moduleLabels = {
  composition: "组合",
  perception: "感知",
  collaboration: "协作",
  reasoning: "推理",
  action: "行动",
  reflection: "反思",
  governance: "治理",
  memory: "记忆",
};

const findingDetails = {
  lineage_break: "当前模块只报告本地成功，没有绑定上一模块回执。",
  artifact_handoff_mismatch: "治理读取的仍是旧报告摘要，反思产物没有抵达准入层。",
  endpoint_receipt_mismatch: "业务端点没有绑定这一轮的终态回执。",
  endpoint_artifact_mismatch: "端点发布工件与模块链中的工件版本不同。",
  authorization_not_bound: "端点使用的授权没有出现在治理回执中。",
  business_check_failed: "业务端点事实没有通过独立核验。",
};

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

function renderModes() {
  $("#mode-control").innerHTML = state.meta.modes
    .map(
      (mode) => `
        <button
          type="button"
          class="scenario-button ${mode.id === state.mode ? "active" : ""}"
          data-mode="${mode.id}"
        >${mode.label}</button>
      `,
    )
    .join("");

  $$(".scenario-button").forEach((button) => {
    button.addEventListener("click", async () => {
      state.mode = button.dataset.mode;
      renderModes();
      await runExperiment();
    });
  });
}

function renderSpine(run) {
  $("#receipt-spine").innerHTML = run.receipts
    .map((receipt, index) => {
      const linked = index === 0 || receipt.parent_receipts.length === 1;
      const className = linked ? "linked" : "broken";
      return `
        <div class="spine-node ${className}">
          <span>${String(index + 1).padStart(2, "0")}</span>
          <div>
            <strong>${moduleLabels[receipt.module]}</strong>
            <small>${receipt.pattern}</small>
          </div>
          <code>${short(receipt.output_digest)}</code>
          <b>${linked ? "已绑定" : "断链"}</b>
        </div>
      `;
    })
    .join("");
}

function renderFindings(run) {
  const findings = run.acceptance.findings;
  text(
    "#finding-title",
    findings.length ? `${findings.length} 项系统级缺口` : "端到端检查全部通过",
  );
  $("#finding-list").innerHTML = findings.length
    ? findings
        .map(
          (finding) => `
            <div>
              <code>${finding.code}</code>
              <span>${findingDetails[finding.code] || finding.detail}</span>
            </div>
          `,
        )
        .join("")
    : `
      <div class="finding-clear">
        <strong>版本一致</strong>
        <span>最终报告、治理回执与 SQLite 发布行指向同一摘要。</span>
      </div>
      <div class="finding-clear">
        <strong>事实一致</strong>
        <span>发布端点保留 798 条已支付与 2 条冲正。</span>
      </div>
    `;
}

function renderReceiptTable(run) {
  $("#receipt-table").innerHTML = `
    <div class="receipt-table-head">
      <span>模块 / 模式</span>
      <span>输入摘要</span>
      <span>输出摘要</span>
      <span>父回执</span>
      <span>局部判定</span>
    </div>
    ${run.receipts
      .map(
        (receipt) => `
          <div class="receipt-table-row">
            <div>
              <strong>${moduleLabels[receipt.module]}</strong>
              <small>${receipt.pattern}</small>
            </div>
            <code>${short(receipt.input_digest)}</code>
            <code>${short(receipt.output_digest)}</code>
            <span>${receipt.parent_receipts.length ? "1 张" : "无"}</span>
            <b>${receipt.status.toUpperCase()}</b>
          </div>
        `,
      )
      .join("")}
  `;
}

function renderBoundaries(run) {
  $("#boundary-list").innerHTML = run.boundaries
    .map(
      (item) => `
        <div class="boundary-row">
          <strong>边界</strong>
          <span>${item}</span>
        </div>
      `,
    )
    .join("");
}

function renderAll() {
  const run = state.payload.run;
  const acceptance = run.acceptance;
  const accepted = acceptance.accepted;
  const activeMode = state.meta.modes.find((item) => item.id === state.mode);

  text("#mode-description", activeMode.description);
  text("#system-verdict", accepted ? "ACCEPTED" : "REJECTED");
  text(
    "#local-score",
    `${acceptance.local_acceptance_count}/${acceptance.required_module_count}`,
  );
  const passedChecks = run.endpoint.checks.filter((item) => item.passed).length;
  text("#endpoint-score", `${passedChecks}/${run.endpoint.checks.length}`);
  text("#contract-digest", run.contract_digest);
  text("#spine-state", accepted ? "证据链闭环" : "局部成功，系统拒绝");
  text("#paid-count", run.release_row.paid_count);
  text("#reversed-count", run.release_row.reversed_count);
  text("#report-digest", run.release_row.report_digest);
  text("#approval-ref", short(run.release_row.approval_ref));

  $("#system-verdict").className = accepted ? "accepted" : "rejected";
  $("#spine-state").className = `verdict-label ${accepted ? "accepted" : "rejected"}`;

  renderSpine(run);
  renderFindings(run);
  renderReceiptTable(run);
  renderBoundaries(run);
}

async function runExperiment() {
  const loading = $("#loading");
  const error = $("#error");
  const button = $("#run-button");
  loading.hidden = false;
  error.hidden = true;
  button.disabled = true;

  try {
    const response = await fetch(`/api/43/run/${state.mode}`, {
      method: "POST",
    });
    if (!response.ok) {
      const detail = await response.text();
      throw new Error(detail || `HTTP ${response.status}`);
    }
    state.payload = await response.json();
    renderAll();
  } catch (err) {
    error.textContent = `总装验收失败：${err.message}`;
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
  const response = await fetch("/api/43/meta");
  state.meta = await response.json();
  const requested = new URLSearchParams(window.location.search).get("mode");
  if (requested && state.meta.modes.some((item) => item.id === requested)) {
    state.mode = requested;
  }
  renderLectures();
  renderModes();
  bindPanels();
  $("#run-button").addEventListener("click", runExperiment);
  await runExperiment();
}

boot().catch((err) => {
  const error = $("#error");
  error.textContent = `工作台启动失败：${err.message}`;
  error.hidden = false;
});
