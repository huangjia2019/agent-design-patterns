const state = {
  lectures: [],
  lecture: "36",
  view: "experiment",
  busy: false,
};

const tables = [
  "proposals",
  "control_receipts",
  "authority_credentials",
  "authority_transitions",
  "budget_usage",
  "governance_events",
  "payment_effects",
];

const $ = (selector) => document.querySelector(selector);

const reasonLabels = {
  amount_requires_review: "金额超过自动放行线",
  subject_count_requires_review: "影响人数超过自动放行线",
  risk_requires_review: "风险等级需要复核",
  irreversible_effect: "外部效果不可逆",
};

const decisionLabels = {
  allowed: "允许（allowed）",
  denied: "拒绝（denied）",
};

const presentation = {
  "36": {
    eyebrow: "CONTROL PLANE COMPARISON",
    title: "同一份已验收工件，两条执行桥",
    left: {
      kicker: "无治理桥接",
      title: "把验收通过当成执行授权",
      labels: ["工件验收", "治理回执", "付款结果", "审计结论"],
      tone: "danger",
    },
    right: {
      kicker: "完整治理链",
      title: "每一种权力都要留下回执",
      labels: ["审批门", "爆炸半径", "权限凭证", "轨迹审计"],
      tone: "success",
    },
    evidenceEyebrow: "SEMANTIC TRACE",
    evidenceTitle: "治理事件",
    digestLabel: "哈希",
  },
  "37": {
    eyebrow: "DOUBLE ROUTING",
    title: "先定走哪条路，再定由谁签字",
    left: {
      kicker: "第一次路由",
      title: "自动放行、人审还是硬拒绝",
      labels: ["审批路线", "触发理由", "票据有效期", "提案摘要"],
      tone: "warning",
    },
    right: {
      kicker: "第二次路由",
      title: "金额档位决定谁来签字",
      labels: ["第一位审批人", "第二位审批人", "最终决定", "回执到期"],
      tone: "success",
    },
    evidenceEyebrow: "APPROVAL TIMELINE",
    evidenceTitle: "审批时间线",
    digestLabel: "回执摘要",
  },
  "38": {
    eyebrow: "HIERARCHICAL BUDGET",
    title: "三个部门都合规，为什么第三个仍被拦",
    left: {
      kicker: "叶子作用域",
      title: "每个部门都守住自己的额度",
      labels: ["Engineering", "Finance", "Ops", "部门上限"],
      tone: "success",
    },
    right: {
      kicker: "父级组合",
      title: "共享窗口只剩一份",
      labels: ["窗口总额", "已预留", "剩余额度", "第三批状态"],
      tone: "warning",
    },
    evidenceEyebrow: "RESERVATION TIMELINE",
    evidenceTitle: "预算预留时间线",
    digestLabel: "租约摘要",
  },
  "39": {
    eyebrow: "EVIDENCE-BOUND AUTHORITY",
    title: "权限靠什么逐级挣得，越界后怎样收回",
    left: {
      kicker: "证据窗口",
      title: "每升一级，都重新积累五个业务切片",
      labels: [
        "观察 → 建议",
        "建议 → 影子",
        "影子 → 受限",
        "晋升纪律",
      ],
      tone: "success",
    },
    right: {
      kicker: "权限边界",
      title: "模拟通过，不等于全量执行",
      labels: [
        "影子模拟",
        "影子真实执行",
        "受限小批次",
        "受限全量工资",
      ],
      tone: "warning",
    },
    evidenceEyebrow: "AUTHORITY TIMELINE",
    evidenceTitle: "权限过渡时间线",
    digestLabel: "过渡凭证",
  },
  "40": {
    eyebrow: "TRACE COMPLETENESS",
    title: "付款已经发生，治理过程能否被完整证明",
    left: {
      kicker: "事实与完整性",
      title: "最终状态只能说明结果",
      labels: ["付款事实", "语义事件", "哈希链", "事件完整性"],
      tone: "warning",
    },
    right: {
      kicker: "治理覆盖",
      title: "每一道控制都要在轨迹中留下位置",
      labels: ["审批门", "爆炸半径", "权限凭证", "审计结论"],
      tone: "success",
    },
    evidenceEyebrow: "SEMANTIC GOVERNANCE TRACE",
    evidenceTitle: "语义治理事件",
    digestLabel: "事件哈希",
  },
};

function money(value) {
  return `¥${Number(value || 0).toLocaleString("zh-CN", {
    maximumFractionDigits: 0,
  })}`;
}

function setBusy(busy) {
  state.busy = busy;
  ["#run-lecture", "#run-variant", "#run-module", "#reset"].forEach((selector) => {
    $(selector).disabled = busy;
  });
  $("#run-status").textContent = busy ? "运行中" : "运行完成";
}

async function api(path, options = {}) {
  const response = await fetch(path, options);
  const payload = await response.json();
  if (!response.ok) {
    throw new Error(payload.detail || `HTTP ${response.status}`);
  }
  return payload;
}

function renderLectures() {
  $("#lecture-nav").innerHTML = state.lectures.map((lecture) => `
    <button class="lecture-link ${lecture.number === state.lecture ? "active" : ""}"
      data-lecture="${lecture.number}" type="button">
      <span class="lecture-number">${lecture.number}</span>
      <span class="lecture-name">
        <strong>${lecture.title}</strong>
        <span>${lecture.pattern}</span>
      </span>
    </button>
  `).join("");
  document.querySelectorAll(".lecture-link").forEach((button) => {
    button.addEventListener("click", () => selectLecture(button.dataset.lecture));
  });
}

function setLabels(prefix, labels) {
  labels.forEach((label, index) => {
    $(`#${prefix}-label-${index + 1}`).textContent = label;
  });
}

function clearComparison() {
  [
    "#naive-acceptance", "#naive-receipts", "#naive-payment", "#naive-audit",
    "#governed-approval", "#governed-radius", "#governed-authority", "#governed-audit",
  ].forEach((selector) => { $(selector).textContent = "--"; });
  renderEvents([]);
  $("#trace-status").textContent = "尚未运行";
  $("#run-status").textContent = "等待运行";
}

function configurePresentation(number) {
  const config = presentation[number] || presentation["36"];
  $("#comparison-eyebrow").textContent = config.eyebrow;
  $("#comparison-title").textContent = config.title;
  $("#left-kicker").textContent = config.left.kicker;
  $("#left-title").textContent = config.left.title;
  $("#right-kicker").textContent = config.right.kicker;
  $("#right-title").textContent = config.right.title;
  setLabels("left", config.left.labels);
  setLabels("right", config.right.labels);
  $("#comparison-left").className = `comparison-panel ${config.left.tone}`;
  $("#comparison-right").className = `comparison-panel ${config.right.tone}`;
  $("#evidence-eyebrow").textContent = config.evidenceEyebrow;
  $("#evidence-title").textContent = config.evidenceTitle;
  $("#evidence-digest-label").textContent = config.digestLabel;
}

function selectLecture(number) {
  state.lecture = number;
  const lecture = state.lectures.find((item) => item.number === number);
  renderLectures();
  $("#coordinate").textContent = lecture.coordinate.toUpperCase();
  $("#lecture-title").textContent = `${lecture.number} · ${lecture.title}`;
  $("#lecture-question").textContent = lecture.question;
  $("#run-variant").textContent = lecture.variant_label;
  $("#stage-strip").innerHTML = lecture.stages.map((stage, index) => `
    <div class="stage">
      <span class="stage-index">${index + 1}</span>
      <span>${stage}</span>
    </div>
  `).join("");
  configurePresentation(number);
  clearComparison();
}

function renderState(data) {
  const payroll = data.payroll || {};
  $("#metric-employees").textContent = payroll.employee_count ?? "--";
  $("#metric-amount").textContent = money(payroll.amount);
  $("#metric-receipts").textContent = data.receipt_count ?? 0;
  $("#metric-events").textContent = data.event_count ?? 0;
  $("#db-status").textContent = data.payment_count
    ? `${data.payment_count} 笔付款事实`
    : "基线状态";
}

function renderEvents(events = []) {
  $("#event-count").textContent = `${events.length} 条事件`;
  $("#event-rows").innerHTML = events.length
    ? events.map((event) => `
      <tr>
        <td>${event.sequence}</td>
        <td>${event.event_type}</td>
        <td>${event.control}</td>
        <td>${event.decision || "-"}</td>
        <td>${event.summary}</td>
        <td>${event.event_hash}</td>
      </tr>
    `).join("")
    : '<tr><td colspan="6" class="empty">当前实验没有完整治理事件</td></tr>';
}

function renderApprovalGate(result) {
  $("#metric-events").textContent = result.timeline.length;
  if (result.mode === "approval-gate") {
    $("#naive-acceptance").textContent = "需要人审 (human_review)";
    $("#naive-receipts").textContent = result.route.reason_codes
      .map((code) => reasonLabels[code] || code)
      .join(" / ");
    $("#naive-payment").textContent = result.ticket.expires_at;
    $("#naive-audit").textContent = result.proposal.digest;
    $("#governed-approval").textContent =
      `${result.attestations[0].approver_id} / ${result.attestations[0].role}`;
    $("#governed-radius").textContent =
      `${result.attestations[1].approver_id} / ${result.attestations[1].role}`;
    $("#governed-authority").textContent = result.final_receipt.decision;
    $("#governed-audit").textContent = result.final_receipt.expires_at;
    $("#trace-status").textContent = "审批时间线";
  } else {
    const changed = result.changed;
    $("#left-kicker").textContent = "真实版本漂移";
    $("#left-title").textContent = "审批后补回 E0007 与 E0012";
    setLabels("left", ["补发对象", "金额变化", "工件摘要", "旧审批可用"]);
    $("#naive-acceptance").textContent = changed.restored_ids.join(" + ");
    $("#naive-receipts").textContent =
      `${money(changed.delta_amount)} / ${changed.changed_subject_count} 人`;
    $("#naive-payment").textContent =
      `${changed.original_artifact_digest} → ${changed.changed_artifact_digest}`;
    $("#naive-audit").textContent =
      changed.old_approval_authorizes ? "是" : "否";
    $("#right-kicker").textContent = "执行边界";
    $("#right-title").textContent = "支付适配器重新仲裁";
    setLabels("right", ["原提案摘要", "新提案摘要", "付款结果", "拒绝原因"]);
    $("#governed-approval").textContent = changed.original_digest;
    $("#governed-radius").textContent = changed.changed_digest;
    $("#governed-authority").textContent = "0 笔";
    $("#governed-audit").textContent =
      changed.adapter_result.includes("approval-gate")
        ? "拒绝：审批回执未绑定新提案"
        : changed.adapter_result;
    $("#trace-status").textContent = "审批时间线";
  }
  renderEvents(result.timeline);
}

function renderBlastRadius(result) {
  const candidates = Object.fromEntries(
    result.candidates.map((item) => [item.department, item]),
  );
  const root = result.snapshot[result.policy.root_scope];
  const third = result.batches.find((item) => item.department === "Ops");
  const batchValue = (department) => {
    const item = candidates[department];
    return `${money(item.amount)} / ${item.subject_count} 人`;
  };

  $("#naive-acceptance").textContent = batchValue("Engineering");
  $("#naive-receipts").textContent = batchValue("Finance");
  $("#naive-payment").textContent = batchValue("Ops");
  $("#naive-audit").textContent =
    `${money(result.policy.leaf_amount_limit)} / ${result.policy.leaf_subject_limit} 人`;
  $("#governed-approval").textContent = money(result.policy.root_amount_limit);
  $("#governed-radius").textContent = money(root.reserved_amount);
  $("#governed-authority").textContent =
    money(result.policy.root_amount_limit - root.reserved_amount);
  $("#governed-audit").textContent = third
    ? "父级拒绝：共享窗口金额预算不足"
    : "尚未申请";
  if (third) {
    $("#right-title").textContent = "第三批局部合规，组合超额";
  }
  $("#metric-events").textContent = result.timeline.length;
  $("#trace-status").textContent = "预留时间线";
  renderEvents(result.timeline);
}

function renderProgressiveCommitment(result) {
  const windows = result.evidence_windows;
  const windowValue = (index) => {
    const window = windows[index];
    return (
      `${window.runs} 次 / ${window.evaluation_slices.length} 切片 / `
      + window.evidence_digest
    );
  };
  $("#naive-acceptance").textContent = windowValue(0);
  $("#naive-receipts").textContent = windowValue(1);
  $("#naive-payment").textContent = windowValue(2);
  $("#naive-audit").textContent = "申请绑定窗口摘要，批准后证据清零";

  if (result.incident) {
    const incident = result.incident;
    $("#right-kicker").textContent = "关键越界";
    $("#right-title").textContent = "降级换发新凭证，旧凭证立即失效";
    setLabels("right", ["事故前", "事故后", "旧凭证", "新证据窗口"]);
    $("#governed-approval").textContent =
      `${incident.before.level} v${incident.before.version}`;
    $("#governed-radius").textContent =
      `${incident.after.level} v${incident.after.version}`;
    $("#governed-authority").textContent =
      decisionLabels[incident.old_credential_decision];
    $("#governed-audit").textContent =
      `${incident.fresh_evidence_runs} 次`;
  } else {
    $("#governed-approval").textContent =
      `${decisionLabels[result.shadow.simulation_decision]} / 只模拟`;
    $("#governed-radius").textContent =
      `${decisionLabels[result.shadow.live_decision]} / 禁止真实效果`;
    $("#governed-authority").textContent =
      `${money(result.limited.canary_amount)} / `
      + `${result.limited.canary_subjects} 人 / `
      + decisionLabels[result.limited.canary_decision];
    $("#governed-audit").textContent =
      `${money(result.limited.full_amount)} / `
      + `${result.limited.full_subjects} 人 / `
      + decisionLabels[result.limited.full_decision];
  }
  $("#metric-events").textContent = result.timeline.length;
  $("#trace-status").textContent = "权限过渡时间线";
  renderEvents(result.timeline);
}

function renderObservability(result) {
  const missing = new Set(result.audit.missing_controls);
  const payment = result.payment || {};
  const events = result.events || [];
  $("#naive-acceptance").textContent =
    `${payment.subject_count || 0} 人 / ${money(payment.amount)}`;
  $("#naive-receipts").textContent = `${events.length} 条`;
  $("#naive-payment").textContent =
    result.audit.chain_valid ? "有效" : "断裂";
  $("#naive-audit").textContent =
    result.audit.complete ? "完整" : "不完整";
  $("#governed-approval").textContent =
    missing.has("approval-gate") ? "缺失" : "已记录";
  $("#governed-radius").textContent =
    missing.has("blast-radius") ? "缺失" : "已记录";
  $("#governed-authority").textContent =
    missing.has("progressive-commitment") ? "缺失" : "已记录";
  $("#governed-audit").textContent = result.audit.complete
    ? "完整且哈希链有效"
    : `缺 ${result.audit.missing_controls.join(" / ")}`;
  $("#trace-status").textContent =
    result.audit.complete ? "完整轨迹" : "轨迹不完整";
  renderEvents(events);
}

function renderPolicyDrift(result) {
  $("#comparison-eyebrow").textContent = "POLICY DRIFT COMPARISON";
  $("#comparison-title").textContent = "同一份已验收工件，两版策略尺度";
  $("#stage-strip").innerHTML = [
    "策略盘点",
    "原策略判断",
    "策略变更",
    "新策略判断",
  ].map((stage, index) => `
    <div class="stage">
      <span class="stage-index">${index + 1}</span>
      <span>${stage}</span>
    </div>
  `).join("");
  $("#left-kicker").textContent = "原策略 v1";
  $("#left-title").textContent = "1300 万现金线把组合转入人工处理";
  setLabels("left", ["策略盘点", "组合现金线", "判断结果", "原始回执策略痕迹"]);
  $("#comparison-left").className = "comparison-panel warning";
  $("#naive-acceptance").textContent =
    `${result.inventory.verified}/${result.inventory.count} 条已核对`;
  $("#naive-receipts").textContent = money(result.before.limit);
  $("#naive-payment").textContent = result.before.decision;
  $("#naive-audit").textContent =
    `${result.before.raw_policy_marks.length} 处 / 拒绝时可见`;

  $("#right-kicker").textContent = "放宽后的策略 v2";
  $("#right-title").textContent = "3000 万现金线让同一组合直接通过";
  setLabels("right", ["组合现金线", "判断结果", "原始回执策略痕迹", "治理策略摘要"]);
  $("#comparison-right").className = "comparison-panel danger";
  $("#governed-approval").textContent = money(result.after.limit);
  $("#governed-radius").textContent = result.after.decision;
  $("#governed-authority").textContent =
    `${result.after.raw_policy_marks.length} 处 / 放行时消失`;
  $("#governed-audit").textContent =
    `v${result.after.policy_version} / ${result.after.policy_digest}`;
  $("#metric-events").textContent = result.timeline.length;
  $("#trace-status").textContent = "策略变更证据";
  $("#evidence-eyebrow").textContent = "POLICY DRIFT TRACE";
  $("#evidence-title").textContent = "策略漂移时间线";
  $("#evidence-digest-label").textContent = "策略摘要";
  renderEvents(result.timeline);
}

function renderComparison(payload) {
  const result = payload.result;
  if (result.mode === "policy-drift") {
    renderPolicyDrift(result);
    return;
  }
  if (result.mode === "approval-gate" || result.mode === "approval-changed") {
    renderApprovalGate(result);
    return;
  }
  if (result.mode === "blast-radius" || result.mode === "blast-radius-overflow") {
    renderBlastRadius(result);
    return;
  }
  if (
    result.mode === "progressive-commitment"
    || result.mode === "progressive-incident"
  ) {
    renderProgressiveCommitment(result);
    return;
  }
  if (
    state.lecture === "40"
    && (result.mode === "governed" || result.mode === "incomplete-trace")
  ) {
    renderObservability(result);
    return;
  }
  const naive = result.naive || (result.mode === "naive" ? result : null);
  const governed = result.governed || (result.mode === "governed" ? result : null);

  if (naive) {
    $("#naive-acceptance").textContent = naive.artifact_acceptance;
    $("#naive-receipts").textContent = String(naive.governance_receipts);
    $("#naive-payment").textContent =
      `${naive.payment.subject_count} 人 / ${money(naive.payment.amount)}`;
    $("#naive-audit").textContent = "不可证明";
  }

  if (governed) {
    $("#governed-approval").textContent =
      `${governed.approval.final} / ${governed.approval.roles.join(" + ")}`;
    $("#governed-radius").textContent =
      `${governed.containment.reservation} / 预算已占用`;
    $("#governed-authority").textContent =
      `${governed.authority.level} v${governed.authority.version}`;
    $("#governed-audit").textContent =
      governed.audit.complete ? "完整且哈希链有效" : "不完整";
    $("#trace-status").textContent =
      governed.audit.complete ? "完整轨迹" : "轨迹缺口";
    renderEvents(governed.events);
  } else {
    renderEvents([]);
  }

  if (result.mode === "changed-after-approval") {
    $("#naive-acceptance").textContent = "old approval";
    $("#naive-receipts").textContent = "digest mismatch";
    $("#naive-payment").textContent = "0 笔";
    $("#naive-audit").textContent = "执行适配器拒绝";
  }
  if (result.mode === "containment-overflow") {
    $("#naive-acceptance").textContent = "提案存在";
    $("#naive-receipts").textContent = "预算拒绝";
    $("#naive-payment").textContent = "0 笔";
    $("#naive-audit").textContent = result.blocked;
  }
  if (result.mode === "critical-incident") {
    $("#governed-authority").textContent =
      `${result.before.level} → ${result.after.level}`;
    $("#governed-audit").textContent =
      `证据窗口 ${result.fresh_evidence_runs} 条`;
  }
}

async function runLecture(variant = false) {
  if (state.busy) return;
  setBusy(true);
  try {
    const payload = await api(
      `/api/run/${state.lecture}?variant=${variant}`,
      { method: "POST" },
    );
    renderState(payload.state);
    renderComparison(payload);
  } catch (error) {
    $("#run-status").textContent = error.message;
  } finally {
    setBusy(false);
  }
}

function switchView(view) {
  state.view = view;
  document.querySelectorAll(".tab").forEach((tab) => {
    tab.classList.toggle("active", tab.dataset.view === view);
  });
  document.querySelectorAll(".view").forEach((panel) => {
    panel.classList.toggle("active", panel.id === `view-${view}`);
  });
}

function renderTableTabs() {
  $("#table-tabs").innerHTML = tables.map((table, index) => `
    <button class="table-tab ${index === 0 ? "active" : ""}"
      data-table="${table}" type="button">${table}</button>
  `).join("");
  document.querySelectorAll(".table-tab").forEach((button) => {
    button.addEventListener("click", () => loadTable(button.dataset.table));
  });
}

async function loadTable(table) {
  document.querySelectorAll(".table-tab").forEach((button) => {
    button.classList.toggle("active", button.dataset.table === table);
  });
  const payload = await api(`/api/tables/${table}`);
  const rows = payload.rows;
  const columns = rows.length ? Object.keys(rows[0]) : [];
  $("#db-head").innerHTML = columns.length
    ? `<tr>${columns.map((column) => `<th>${column}</th>`).join("")}</tr>`
    : "";
  $("#db-body").innerHTML = rows.length
    ? rows.map((row) => `
      <tr>${columns.map((column) => `<td>${row[column] ?? ""}</td>`).join("")}</tr>
    `).join("")
    : '<tr><td class="empty">当前表为空</td></tr>';
}

async function resetLab() {
  if (state.busy) return;
  setBusy(true);
  try {
    const payload = await api("/api/reset", { method: "POST" });
    renderState(payload);
    configurePresentation(state.lecture);
    clearComparison();
    $("#run-status").textContent = "已重置";
  } finally {
    setBusy(false);
  }
}

async function init() {
  const query = new URLSearchParams(window.location.search);
  const meta = await api("/api/meta");
  state.lectures = meta.lectures;
  renderLectures();
  const requestedLecture = query.get("lecture");
  const initialLecture = state.lectures.some(
    (lecture) => lecture.number === requestedLecture,
  ) ? requestedLecture : "36";
  selectLecture(initialLecture);
  renderTableTabs();
  renderState(await api("/api/state"));
  await loadTable("proposals");

  $("#run-lecture").addEventListener("click", () => runLecture(false));
  $("#run-variant").addEventListener("click", () => runLecture(true));
  $("#run-module").addEventListener("click", () => {
    selectLecture("36");
    switchView("experiment");
    runLecture(false);
  });
  $("#reset").addEventListener("click", resetLab);
  document.querySelectorAll(".tab").forEach((tab) => {
    tab.addEventListener("click", () => switchView(tab.dataset.view));
  });
  if (query.get("autorun") === "1") {
    await runLecture(query.get("variant") === "1");
  }
}

init().catch((error) => {
  $("#run-status").textContent = error.message;
});
