const appState = {
  meta: null,
  database: null,
  selectedLecture: "26",
  selectedTable: "payroll",
  tablePage: 1,
  tablePageSize: 25,
  tableSearch: "",
  tableResult: null,
};

const byId = (id) => document.getElementById(id);
const number = new Intl.NumberFormat("zh-CN");

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

async function api(path, options = {}) {
  const response = await fetch(path, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  const payload = await response.json();
  if (!response.ok) throw new Error(payload.detail || "请求失败");
  return payload;
}

function setBusy(active, label = "正在运行实验") {
  byId("busy-label").textContent = label;
  byId("busy-overlay").classList.toggle("hidden", !active);
  document.querySelectorAll("button").forEach((button) => {
    button.disabled = active || button.dataset.permanentDisabled === "true";
  });
}

let toastTimer;
function toast(message, error = false) {
  clearTimeout(toastTimer);
  const node = byId("toast");
  node.textContent = message;
  node.classList.toggle("error", error);
  node.classList.remove("hidden");
  toastTimer = setTimeout(() => node.classList.add("hidden"), 3200);
}

function selectedLecture() {
  return appState.meta.lectures.find(
    (lecture) => lecture.number === appState.selectedLecture,
  );
}

function renderLectureNav() {
  byId("lecture-list").innerHTML = appState.meta.lectures
    .map(
      (lecture) => `
        <button class="lecture-link ${lecture.number === appState.selectedLecture ? "active" : ""} ${lecture.available ? "" : "unavailable"}"
                data-lecture="${escapeHtml(lecture.number)}"
                data-permanent-disabled="${lecture.available ? "false" : "true"}"
                ${lecture.available ? "" : "disabled"} type="button">
          <span class="lecture-number">${escapeHtml(lecture.number)}</span>
          <span>
            <strong>${escapeHtml(lecture.title)}</strong>
            <small>${escapeHtml(lecture.pattern)}</small>
          </span>
        </button>
      `,
    )
    .join("");

  document.querySelectorAll(".lecture-link:not(.unavailable)").forEach((button) => {
    button.addEventListener("click", () => {
      appState.selectedLecture = button.dataset.lecture;
      renderLectureNav();
      renderLesson();
      clearRunResult();
      switchView("experiment");
    });
  });
}

function renderLesson() {
  const lecture = selectedLecture();
  byId("lesson-coordinate").textContent = lecture.coordinate;
  byId("lesson-title").textContent = `${lecture.number} · ${lecture.title}`;
  byId("lesson-question").textContent = lecture.question;
  byId("empty-pattern").textContent = lecture.pattern;
  byId("empty-summary").textContent = lecture.summary;
  byId("variant-label").textContent = lecture.variant_label;
  byId("variant-mode").checked = false;
  byId("stage-strip").innerHTML = lecture.stages
    .map(
      (stage, index) => `
        <div class="stage">
          <span>${index + 1}</span>
          <strong>${escapeHtml(stage)}</strong>
        </div>
      `,
    )
    .join("");
}

function clearRunResult() {
  byId("run-empty").classList.remove("hidden");
  byId("run-result").classList.add("hidden");
  byId("reflection-verdict").classList.add("hidden");
  byId("run-meta").textContent = "等待运行";
}

function renderDatabaseState() {
  const state = appState.database;
  if (!state) return;

  const paid = state.ledger_truth.paid;
  const reversed = state.ledger_truth.reversed;
  byId("metric-employees").textContent = number.format(state.employees);
  byId("metric-paid").textContent = number.format(paid);
  byId("metric-reversed").textContent = number.format(reversed);
  byId("metric-findings").textContent = number.format(state.mismatch_findings);
  byId("database-path").textContent = state.database;
  byId("updated-at").textContent = new Date().toLocaleTimeString("zh-CN", {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  });
  byId("sidebar-db-status").textContent =
    paid === 798 && reversed === 2 ? "月末反思场景" : "行动模块基线";

  const payrollTotal = Object.values(state.payroll_status).reduce(
    (sum, count) => sum + count,
    0,
  );
  byId("payroll-status-label").textContent = `${payrollTotal} rows`;
  byId("payroll-status-bar").innerHTML = Object.entries(state.payroll_status)
    .map(
      ([status, count]) => `
        <span class="status-segment status-${escapeHtml(status)}"
              style="width:${(count / payrollTotal) * 100}%"
              title="${escapeHtml(status)} ${count}"></span>
      `,
    )
    .join("");
  byId("payroll-legend").innerHTML = Object.entries(state.payroll_status)
    .map(
      ([status, count]) => `
        <span class="legend-item">
          <span class="legend-swatch status-${escapeHtml(status)}"></span>
          ${escapeHtml(status)} ${number.format(count)}
        </span>
      `,
    )
    .join("");

  byId("report-claim").textContent =
    `PAID ${state.report_claim.paid} · REVERSED ${state.report_claim.reversed}`;
  byId("ledger-truth").textContent = `PAID ${paid} · REVERSED ${reversed}`;
  byId("mirror-panel").classList.toggle("matched", state.mismatch_findings === 0);

  renderChanges(state.changes);
  renderTableTabs();
}

function renderChanges(changes) {
  byId("change-list").innerHTML = changes.length
    ? changes
        .map(
          (change) => `
            <div class="change-row">
              <strong>${escapeHtml(change.table)}</strong>
              <span>${escapeHtml(change.key)}</span>
              <span>${escapeHtml(change.fields)}</span>
            </div>
          `,
        )
        .join("")
    : '<div class="no-changes">数据库与行动基线一致</div>';
}

function renderRunResult(result) {
  byId("run-empty").classList.add("hidden");
  byId("run-result").classList.remove("hidden");
  byId("result-title").textContent = result.meta.title;
  byId("result-command").textContent = result.command;
  byId("run-meta").textContent = `${result.duration_ms} ms · exit ${result.return_code}`;
  byId("raw-output").textContent = result.output;

  const analysis = result.analysis || {};
  const verdict = byId("reflection-verdict");
  if (analysis.metrics?.length === 3) {
    verdict.classList.remove("hidden");
    analysis.metrics.forEach((metric, index) => {
      const number = index + 1;
      byId(`verdict-label-${number}`).textContent = metric.label;
      byId(`verdict-value-${number}`).textContent = metric.value;
      byId(`verdict-note-${number}`).textContent = metric.note;
    });
  } else {
    verdict.classList.add("hidden");
  }

  const keyEvents = result.events.filter(
    (event) => !["detail", "system"].includes(event.kind),
  );
  byId("event-list").innerHTML = keyEvents
    .map(
      (event) => `
        <div class="event ${escapeHtml(event.kind)}">
          <span class="event-kind">${escapeHtml(event.kind)}</span>
          <span class="event-text">${escapeHtml(event.text)}</span>
        </div>
      `,
    )
    .join("");
}

function renderTableTabs() {
  if (!appState.database) return;
  byId("table-tabs").innerHTML = appState.database.tables
    .map(
      (table) => `
        <button class="table-tab ${table.name === appState.selectedTable ? "active" : ""}"
                data-table="${escapeHtml(table.name)}" type="button">
          ${escapeHtml(table.name)} · ${number.format(table.count)}
        </button>
      `,
    )
    .join("");
  document.querySelectorAll(".table-tab").forEach((button) => {
    button.addEventListener("click", () => {
      appState.selectedTable = button.dataset.table;
      appState.tablePage = 1;
      renderTableTabs();
      loadTable();
    });
  });
}

function renderTable() {
  const result = appState.tableResult;
  if (!result) return;
  const schema = appState.database.tables.find(
    (table) => table.name === result.table,
  );
  byId("schema-line").innerHTML = schema.columns
    .map(
      (column) => `
        <span class="column-chip ${column.primary_key ? "primary" : ""}">
          ${escapeHtml(column.name)} : ${escapeHtml(column.type)}
        </span>
      `,
    )
    .join("");
  byId("data-head").innerHTML = `
    <tr>${result.columns.map((column) => `<th>${escapeHtml(column)}</th>`).join("")}</tr>
  `;
  byId("data-body").innerHTML = result.rows.length
    ? result.rows
        .map(
          (row) => `
            <tr>
              ${result.columns
                .map((column) => {
                  const value = row[column];
                  const formatted =
                    column === "status"
                      ? `<span class="cell-status">${escapeHtml(value)}</span>`
                      : escapeHtml(value);
                  return `<td>${formatted}</td>`;
                })
                .join("")}
            </tr>
          `,
        )
        .join("")
    : `<tr><td colspan="${result.columns.length}">没有匹配记录</td></tr>`;

  const pages = Math.max(1, Math.ceil(result.total / result.page_size));
  byId("table-count").textContent = `${number.format(result.total)} rows`;
  byId("page-label").textContent = `${result.page} / ${pages}`;
  byId("page-prev").disabled = result.page <= 1;
  byId("page-next").disabled = result.page >= pages;
}

async function loadTable() {
  const params = new URLSearchParams({
    page: appState.tablePage,
    page_size: appState.tablePageSize,
    search: appState.tableSearch,
  });
  appState.tableResult = await api(
    `/api/tables/${appState.selectedTable}?${params}`,
  );
  renderTable();
}

async function runLecture(lecture) {
  const variant = lecture === "all" ? false : byId("variant-mode").checked;
  const label = lecture === "all" ? "正在串行运行五讲" : `正在运行第 ${lecture} 讲`;
  setBusy(true, label);
  try {
    const result = await api(`/api/run/${lecture}?variant=${variant}`, {
      method: "POST",
    });
    renderRunResult(result);
    appState.database = result.after;
    renderDatabaseState();
    toast(`${result.meta.title}运行完成`);
  } catch (error) {
    toast(error.message, true);
  } finally {
    setBusy(false);
  }
}

function switchView(view) {
  document.querySelectorAll(".view").forEach((node) => {
    node.classList.toggle("active", node.id === `view-${view}`);
  });
  document.querySelectorAll(".view-tab").forEach((button) => {
    button.classList.toggle("active", button.dataset.view === view);
  });
  if (view === "database") {
    loadTable().catch((error) => toast(error.message, true));
  }
}

async function mutateDatabase(path, label) {
  setBusy(true, label);
  try {
    const result = await api(path, { method: "POST" });
    appState.database = result.state;
    renderDatabaseState();
    clearRunResult();
    if (document.querySelector("#view-database.active")) await loadTable();
    toast(result.operation.output);
  } catch (error) {
    toast(error.message, true);
  } finally {
    setBusy(false);
  }
}

function bindEvents() {
  document.querySelectorAll(".view-tab").forEach((button) => {
    button.addEventListener("click", () => switchView(button.dataset.view));
  });
  byId("run-lecture").addEventListener("click", () =>
    runLecture(appState.selectedLecture),
  );
  byId("run-all").addEventListener("click", () => runLecture("all"));
  byId("month-end-db").addEventListener("click", () =>
    mutateDatabase("/api/database/month-end", "正在重建月末反思场景"),
  );
  byId("reset-db").addEventListener("click", () => {
    if (window.confirm("恢复行动模块基线？月末反思状态会被清除。")) {
      mutateDatabase("/api/database/reset", "正在恢复行动模块基线");
    }
  });
  byId("page-prev").addEventListener("click", () => {
    appState.tablePage -= 1;
    loadTable().catch((error) => toast(error.message, true));
  });
  byId("page-next").addEventListener("click", () => {
    appState.tablePage += 1;
    loadTable().catch((error) => toast(error.message, true));
  });
  let searchTimer;
  byId("table-search").addEventListener("input", (event) => {
    clearTimeout(searchTimer);
    searchTimer = setTimeout(() => {
      appState.tableSearch = event.target.value.trim();
      appState.tablePage = 1;
      loadTable().catch((error) => toast(error.message, true));
    }, 220);
  });
}

async function init() {
  setBusy(true, "正在读取反思场景");
  try {
    const [meta, database] = await Promise.all([
      api("/api/meta"),
      api("/api/state"),
    ]);
    appState.meta = meta;
    appState.database = database;
    renderLectureNav();
    renderLesson();
    renderDatabaseState();
    bindEvents();
  } catch (error) {
    toast(error.message, true);
  } finally {
    setBusy(false);
  }
}

init();
