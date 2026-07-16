const appState = {
  meta: null,
  database: null,
  selectedLecture: "21",
  selectedTable: "employees",
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
    button.disabled = active;
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
        <button class="lecture-link ${lecture.number === appState.selectedLecture ? "active" : ""}"
                data-lecture="${escapeHtml(lecture.number)}" type="button">
          <span class="lecture-number">${escapeHtml(lecture.number)}</span>
          <span>
            <strong>${escapeHtml(lecture.title)}</strong>
            <small>${escapeHtml(lecture.pattern)}</small>
          </span>
        </button>
      `,
    )
    .join("");

  document.querySelectorAll(".lecture-link").forEach((button) => {
    button.addEventListener("click", () => {
      appState.selectedLecture = button.dataset.lecture;
      renderLectureNav();
      renderLesson();
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
  renderStressControls();
}

function renderStressControls() {
  const stress = appState.meta.stress;
  if (!stress) return;
  const lecture = appState.selectedLecture;
  const primary = byId("stress-primary");
  const resultNode = byId("stress-ladder");
  resultNode.classList.add("hidden");
  resultNode.innerHTML = "";
  let actions = "";

  if (lecture === "21") {
    byId("stress-title").textContent = "一个例子走透：L0 裸循环";
    byId("stress-subtitle").textContent = "同一份北极星目标与外部备注，只看动作流水和数据库终态";
    actions = stress.worked_levels
      .filter((level) => level.id === "L0")
      .map(levelButton)
      .join("");
    primary.textContent = "运行 L0";
    primary.onclick = () => runStress("L0");
  } else if (lecture === "22") {
    byId("stress-title").textContent = "工具边界消融：L0 → L2";
    byId("stress-subtitle").textContent = "状态账与动作账同时核对，再把教学版放进四种生产压力";
    actions = stress.worked_levels.map(levelButton).join("") + `
      <button class="scenario-button pressure-button" id="stress-gaps-button" type="button">
        四种生产压力
      </button>`;
    primary.textContent = "运行三层对照";
    primary.onclick = runStressLadder;
  } else {
    const vector = stress.vectors.find((item) => item.lecture === lecture);
    byId("stress-title").textContent = `${vector.id}-${vector.title}`;
    byId("stress-subtitle").textContent = `同一刺激运行两种配置，以业务证据判断${vector.pattern}守住了什么`;
    actions = `
      <button class="scenario-button stress-vector-button" data-vector="${escapeHtml(vector.id)}" type="button">
        运行${escapeHtml(vector.pattern)}前后对照
      </button>
      ${lecture === "25" ? '<button class="scenario-button" id="stress-matrix-button" type="button">运行全模块矩阵</button>' : ""}`;
    primary.textContent = "运行本讲对照";
    primary.onclick = () => runStressVector(vector.id);
  }

  byId("stress-actions").innerHTML = actions;
  document.querySelectorAll(".stress-level-button").forEach((button) => {
    button.addEventListener("click", () => runStress(button.dataset.level));
  });
  document.querySelectorAll(".stress-vector-button").forEach((button) => {
    button.addEventListener("click", () => runStressVector(button.dataset.vector));
  });
  byId("stress-gaps-button")?.addEventListener("click", runStressGaps);
  byId("stress-matrix-button")?.addEventListener("click", runStressMatrix);
}

function levelButton(level) {
  return `
    <button class="scenario-button stress-level-button" data-level="${escapeHtml(level.id)}"
            type="button" title="${escapeHtml(level.note)}">
      <strong>${escapeHtml(level.id)}</strong> ${escapeHtml(level.title)}
    </button>`;
}

async function runStress(level) {
  setBusy(true, `正在跑消融 ${level}`);
  try {
    const result = await api(`/api/stress/${level}`, { method: "POST" });
    renderRunResult(result);
    appState.database = result.after;
    renderDatabaseState();
    renderStressLevelResult(result);
    toast(`消融 ${level} 运行完成 · ${result.verdict}`);
  } catch (error) {
    toast(error.message, true);
  } finally {
    setBusy(false);
  }
}

async function runStressLadder() {
  const levels = appState.meta.stress.worked_levels;
  setBusy(true, "正在跑全阶梯对照");
  const rows = [];
  let lastResult = null;
  try {
    for (const level of levels) {
      const result = await api(`/api/stress/${level.id}`, { method: "POST" });
      lastResult = result;
      rows.push({
        id: level.id,
        title: level.title,
        changes: result.after.change_count,
        payments: result.evidence.payment_count,
        disciplined: result.evidence.payments.every((payment) => payment.disciplined),
        verdict: result.verdict,
      });
    }
    if (lastResult) {
      appState.database = lastResult.after;
      renderDatabaseState();
    }
    const node = byId("stress-ladder");
    node.classList.remove("hidden");
    node.innerHTML = `
      <table class="ladder-table">
        <tr><th>层级</th><th>装上的控制</th><th>状态差异</th><th>出账流水</th><th>纪律</th><th>判定</th></tr>
        ${rows
          .map(
            (row) => `
          <tr class="ladder-${row.verdict === "守住" ? "clean" : "bad"}">
            <td><strong>${escapeHtml(row.id)}</strong></td>
            <td>${escapeHtml(row.title)}</td>
            <td>${number.format(row.changes)} 行</td>
            <td>${number.format(row.payments)} 笔</td>
            <td>${row.disciplined ? "有" : "无"}</td>
            <td><span class="verdict ${row.verdict === "守住" ? "safe" : "exposed"}">${escapeHtml(row.verdict)}</span></td>
          </tr>`,
          )
          .join("")}
      </table>
      <p class="ladder-note">状态差异看数据库，双付看动作流水。L1 和 L2 都只改一条工资单状态，纪律却完全不同。</p>
    `;
    toast("全阶梯对照完成");
  } catch (error) {
    toast(error.message, true);
  } finally {
    setBusy(false);
  }
}

function renderStressLevelResult(result) {
  const payments = result.evidence.payments;
  const node = byId("stress-ladder");
  node.classList.remove("hidden");
  node.innerHTML = `
    <div class="stress-metric-grid">
      <div class="stress-metric"><span>本级判定</span><strong class="${result.verdict === "守住" ? "safe-text" : "exposed-text"}">${escapeHtml(result.verdict)}</strong></div>
      <div class="stress-metric"><span>状态差异</span><strong>${number.format(result.after.change_count)} 行</strong></div>
      <div class="stress-metric"><span>实际出账</span><strong>${number.format(result.evidence.payment_count)} 笔</strong></div>
      <div class="stress-metric"><span>受保护字段</span><strong>${result.protected_fields_safe ? "保留" : "被改"}</strong></div>
    </div>
    <table class="ladder-table payment-table">
      <tr><th>流水</th><th>员工</th><th>金额</th><th>先读后写</th><th>来源</th></tr>
      ${payments.map((payment) => `
        <tr><td>${payment.id}</td><td>${escapeHtml(payment.emp_id)}</td><td>¥${number.format(payment.amount)}</td>
        <td>${payment.disciplined ? "是" : "否"}</td><td>${escapeHtml(payment.source)}</td></tr>`).join("")}
    </table>`;
}

async function runStressVector(vectorId) {
  setBusy(true, `正在运行 ${vectorId} 前后对照`);
  try {
    const result = await api(`/api/stress/vector/${vectorId}`, { method: "POST" });
    if (result.after) {
      appState.database = result.after;   // reset baseline, never a prior lecture's L0 damage
      renderDatabaseState();
    }
    const comparison = result.comparison;
    const rows = [comparison.without_pattern, comparison.with_pattern];
    const node = byId("stress-ladder");
    node.classList.remove("hidden");
    node.innerHTML = `
      <div class="stress-stimulus"><span>受控刺激</span><strong>${escapeHtml(comparison.vector.stimulus)}</strong></div>
      <table class="ladder-table">
        <tr><th>配置</th><th>判定</th><th>业务证据</th></tr>
        ${rows.map((row) => `
          <tr class="ladder-${row.safe ? "clean" : "bad"}">
            <td>${escapeHtml(row.configuration || (row.defended ? `装上${row.pattern}` : "未装该模式"))}</td>
            <td><span class="verdict ${row.safe ? "safe" : "exposed"}">${row.safe ? "守住" : "暴露"}</span></td>
            <td>${escapeHtml(row.evidence)}</td>
          </tr>`).join("")}
      </table>`;
    toast(`${vectorId} 前后对照完成`);
  } catch (error) {
    toast(error.message, true);
  } finally {
    setBusy(false);
  }
}

async function runStressGaps() {
  setBusy(true, "正在运行生产压力台");
  try {
    const result = await api("/api/stress/gaps", { method: "POST" });
    const node = byId("stress-ladder");
    node.classList.remove("hidden");
    node.innerHTML = `
      <table class="ladder-table gap-table">
        <tr><th>压力</th><th>缺口</th><th>结果</th><th>结构化证据</th></tr>
        ${result.gaps.map((gap) => `
          <tr class="ladder-${gap.leaked ? "bad" : "clean"}">
            <td><strong>${escapeHtml(gap.id)}-${escapeHtml(gap.name)}</strong></td>
            <td>${escapeHtml(gap.gap)}</td>
            <td><span class="verdict ${gap.leaked ? "exposed" : "safe"}">${gap.leaked ? "暴露" : "守住"}</span></td>
            <td><code>${escapeHtml(JSON.stringify(gap.evidence))}</code></td>
          </tr>`).join("")}
      </table>`;
    toast("生产压力台运行完成");
  } catch (error) {
    toast(error.message, true);
  } finally {
    setBusy(false);
  }
}

async function runStressMatrix() {
  setBusy(true, "正在逐格运行全模块矩阵");
  try {
    const result = await api("/api/stress/matrix", { method: "POST" });
    const matrix = result.matrix;
    const vectorIds = Object.keys(matrix.vectors);
    const node = byId("stress-ladder");
    node.classList.remove("hidden");
    node.innerHTML = `
      <div class="matrix-wrap"><table class="ladder-table matrix-table">
        <tr><th>配置</th>${vectorIds.map((id) => `<th>${escapeHtml(id)}-${escapeHtml(matrix.vectors[id])}</th>`).join("")}<th>终态</th></tr>
        ${matrix.levels.map((level) => `
          <tr>
            <td><strong>${escapeHtml(level.id)}</strong> ${escapeHtml(level.title)}</td>
            ${vectorIds.map((id) => `<td><span class="verdict ${level.cells[id].safe ? "safe" : "exposed"}">${level.cells[id].safe ? "守住" : "暴露"}</span></td>`).join("")}
            <td>${level.safe ? "全守住" : `${level.exposed.length} 类暴露`}</td>
          </tr>`).join("")}
      </table></div>
      <p class="ladder-note">V1/V2 共用薪酬备注注入；V3-中途超时后整批重跑、V4-污染工件向后传递和 V5-高风险输入输出是边界不同的独立刺激。矩阵表示评测套件，不把它们伪装成一条万能提示词。</p>`;
    toast("全模块矩阵运行完成");
  } catch (error) {
    toast(error.message, true);
  } finally {
    setBusy(false);
  }
}

function renderDatabaseState() {
  const state = appState.database;
  if (!state) return;

  byId("metric-employees").textContent = number.format(state.employees);
  byId("metric-total").textContent = `¥${number.format(state.payroll_total)}`;
  const approvalCount = Object.values(state.approval_status).reduce(
    (sum, count) => sum + count,
    0,
  );
  byId("metric-approvals").textContent = number.format(approvalCount);
  byId("metric-changes").textContent = number.format(state.change_count);
  byId("database-path").textContent = state.database;
  byId("updated-at").textContent = new Date().toLocaleTimeString("zh-CN", {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  });
  byId("sidebar-db-status").textContent =
    state.change_count === 0 ? "基线状态" : `${state.change_count} 行已变化`;

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

  const evidence = state.e0099;
  const panel = byId("e0099-panel");
  panel.classList.toggle("present", Boolean(evidence));
  if (evidence) {
    byId("e0099-title").textContent = "错误审批已进入实验库";
    byId("e0099-details").innerHTML = Object.entries(evidence)
      .map(
        ([key, value]) => `
          <div><dt>${escapeHtml(key)}</dt><dd>${escapeHtml(value)}</dd></div>
        `,
      )
      .join("");
  } else {
    byId("e0099-title").textContent = "尚未注入错误审批";
    byId("e0099-details").innerHTML =
      "<div><dt>status</dt><dd>baseline</dd></div>";
  }
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
    : '<div class="no-changes">数据库与基线一致</div>';
}

function renderRunResult(result) {
  byId("run-empty").classList.add("hidden");
  byId("run-result").classList.remove("hidden");
  byId("result-title").textContent = result.meta.title;
  byId("result-command").textContent = result.command;
  byId("run-meta").textContent = `${result.duration_ms} ms · exit ${result.return_code}`;
  byId("raw-output").textContent = result.output;
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
  byId("reset-db").addEventListener("click", () => {
    if (window.confirm("恢复数据库基线？当前实验产生的状态会被清除。")) {
      mutateDatabase("/api/database/reset", "正在恢复数据库基线");
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
  setBusy(true, "正在读取实验状态");
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
