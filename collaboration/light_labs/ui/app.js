const LESSONS = {
  32: {
    pattern: "层级委派",
    question: "三位研究员怎样覆盖完整任务，而不是重复同一方向？",
    benefit: "扩大覆盖面，同时让主管保留总目标与验收责任。",
  },
  33: {
    pattern: "扇出聚合",
    question: "三句都正确的话，为什么会被多数票合成一句错话？",
    benefit: "缩短墙钟时间，并保留多路证据里的差异、冲突和来源。",
  },
  34: {
    pattern: "对抗评审",
    question: "两条阻断意见已经写下，为什么文章仍然发布？",
    benefit: "用独立异议发现盲区，并让高风险问题真实影响放行。",
  },
  35: {
    pattern: "交接链",
    question: "上游已经纠正事实，旧说法为什么还能在下一棒复活？",
    benefit: "让专业角色顺序接力，同时保住状态、版本、证据和责任。",
  },
  B1: {
    pattern: "并发与业务聚合",
    question: "三路 Agent 都成功返回，为什么薪酬结算仍然不能放行？",
    benefit: "把运行成功与业务结论分账，避免用调用状态冒充证据结论。",
  },
};

const state = {
  lesson: new URLSearchParams(window.location.search).get("lesson") || "32",
  running: false,
};

const title = document.querySelector("#lesson-title");
const question = document.querySelector("#lesson-question");
const benefit = document.querySelector("#lesson-benefit");
const runButton = document.querySelector("#run-button");
const resetButton = document.querySelector("#reset-button");
const runState = document.querySelector("#run-state");
const emptyState = document.querySelector("#empty-state");
const results = document.querySelector("#results");
const traceSection = document.querySelector("#trace-section");
const traceGrid = document.querySelector("#trace-grid");

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function selectLesson(lessonId, updateUrl = true) {
  state.lesson = lessonId;
  const lesson = LESSONS[lessonId];
  title.textContent = `${lessonId} · ${lesson.pattern}`;
  question.textContent = lesson.question;
  benefit.textContent = lesson.benefit;
  document.querySelectorAll(".lesson-link").forEach((button) => {
    button.classList.toggle("active", button.dataset.lesson === lessonId);
  });
  if (updateUrl) {
    const url = new URL(window.location.href);
    url.searchParams.set("lesson", lessonId);
    history.replaceState({}, "", url);
  }
  resetView();
}

function resetView() {
  state.running = false;
  emptyState.hidden = false;
  results.hidden = true;
  traceSection.hidden = true;
  runState.textContent = "等待运行";
  runState.className = "run-state";
  runButton.disabled = false;
  runButton.textContent = "运行对照实验";
}

function resultPanel(data, side) {
  const metrics = data.metrics
    .map(
      (metric) => `
        <div class="metric">
          <span>${escapeHtml(metric.label)}</span>
          <strong>${escapeHtml(metric.value)}</strong>
        </div>`,
    )
    .join("");
  const evidence = data.evidence
    .map(
      (item) => `
        <li>
          <span>${escapeHtml(item.label)}</span>
          <strong>${escapeHtml(item.value)}</strong>
        </li>`,
    )
    .join("");
  return `
    <div class="panel-header ${escapeHtml(data.tone)}">
      <div>
        <span>${side}</span>
        <h3>${escapeHtml(data.label)}</h3>
      </div>
      <span class="verdict">${data.tone === "success" ? "守住" : "暴露"}</span>
    </div>
    <div class="panel-body">
      <h4>${escapeHtml(data.headline)}</h4>
      <p>${escapeHtml(data.summary)}</p>
      <div class="metrics">${metrics}</div>
      <div class="evidence-title">结构化证据</div>
      <ul class="evidence-list">${evidence}</ul>
    </div>`;
}

function traceColumn(titleText, data, tone) {
  const rows = data.trace
    .map(
      (item) => `
        <div class="trace-row">
          <span class="trace-step">${escapeHtml(item.step)}</span>
          <div>
            <strong>${escapeHtml(item.state)}</strong>
            <p>${escapeHtml(item.detail)}</p>
          </div>
        </div>`,
    )
    .join("");
  return `
    <div class="trace-column ${tone}">
      <h3>${titleText}</h3>
      ${rows}
    </div>`;
}

async function runComparison() {
  if (state.running) return;
  state.running = true;
  runButton.disabled = true;
  runButton.textContent = "运行中";
  runState.textContent = "正在执行真实 Lab";
  runState.className = "run-state running";

  try {
    const response = await fetch(`/api/compare/${state.lesson}`, { method: "POST" });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const payload = await response.json();
    document.querySelector("#baseline-panel").innerHTML = resultPanel(
      payload.baseline,
      "原始做法",
    );
    document.querySelector("#pattern-panel").innerHTML = resultPanel(
      payload.pattern,
      "加入模式",
    );
    traceGrid.innerHTML =
      traceColumn("原始轨迹", payload.baseline, "danger") +
      traceColumn("模式轨迹", payload.pattern, "success");
    emptyState.hidden = true;
    results.hidden = false;
    traceSection.hidden = false;
    runState.textContent = "运行完成";
    runState.className = "run-state complete";
  } catch (error) {
    runState.textContent = `运行失败：${error.message}`;
    runState.className = "run-state failed";
  } finally {
    state.running = false;
    runButton.disabled = false;
    runButton.textContent = "再次运行";
  }
}

document.querySelectorAll(".lesson-link").forEach((button) => {
  button.addEventListener("click", () => selectLesson(button.dataset.lesson));
});
runButton.addEventListener("click", runComparison);
resetButton.addEventListener("click", resetView);

if (!LESSONS[state.lesson]) state.lesson = "32";
selectLesson(state.lesson, false);
if (new URLSearchParams(window.location.search).get("autorun") === "1") {
  runComparison();
}
