"""Experience Replay pattern.

Reference implementation from column lecture 06-04 (29). The claim:
**a lesson stays in the replay pool only as long as reuse keeps proving
it useful.** The store recalls past trajectories for a new task and
injects them as an upper context layer that constrains the current
decision. But "the agent finds this lesson useful" and "downstream
tasks succeed after this lesson is injected" are two different things,
and only the second is a signal. Effectiveness tracking closes that
loop: every reuse writes back whether the downstream task succeeded,
and a lesson whose track record falls below the health line is
archived out of the pool.

Hierarchy topology: the experience layers sit above the task. L0 keeps
raw traces (ground truth for audit), L1 keeps one distilled reflection
per task, L2 keeps cross-task heuristics distilled from enough similar
L1 entries. Retrieval hands the current run a bundle from the upper
layers; the run happens inside that bundle's constraints. Nothing here
is a loop — no signal re-triggers execution — and nothing is a chain:
the layers persist across tasks.

Three roles:

* `Experience` — one L1 entry: task kind, outcome, the distilled
  lesson, a pointer to its L0 steps, plus the lifecycle numbers
  (retrievals, effectiveness).
* `ExperienceStore.retrieve` — keyword-scored recall over active
  entries, ranked by score then effectiveness. `render` turns the
  hits into the context block the task runs under.
* `ExperienceStore.feedback` — the external signal. EMA-updates each
  injected lesson with the downstream outcome; entries that were
  reused enough and still sit below the health line are archived.

Named failure modes:

* **Superstitious lesson** — a mis-attributed cause ("it worked because
  I ran an unrelated check first") stays plausible forever; only reuse
  outcomes expose it. Closed by feedback + the health line.
* **Stale lesson drift** — the hazard was fixed at the tool layer, the
  lesson keeps occupying context. Closed by the same mechanism, or by
  graduating the lesson into a hard guard and retiring it.
* **Cold start** — an empty store returns nothing for months; seed it
  with written-down team practice instead of waiting.
"""
from __future__ import annotations

from dataclasses import dataclass, field


HEALTH_LINE = 0.5      # below this, after enough reuses, a lesson is archived
MIN_REUSES = 5


@dataclass
class Experience:
    """One L1 entry. `lesson` is what gets injected; `steps` is the L0
    trace it was distilled from, kept for audit, never injected whole."""

    exp_id: str
    task_kind: str
    outcome: str                     # success | failure
    lesson: str
    keywords: list[str]
    steps: list[str] = field(default_factory=list)   # L0 pointer
    retrieval_count: int = 0
    reuse_outcomes: list[bool] = field(default_factory=list)
    effectiveness: float = 0.5       # EMA, starts neutral
    archived: bool = False

    @property
    def reuses(self) -> int:
        return len(self.reuse_outcomes)


@dataclass
class Heuristic:
    """One L2 entry: a cross-task rule distilled from several similar
    L1 entries. Confidence rises with the entries backing it."""

    insight: str
    derived_from: list[str]


class ExperienceStore:
    def __init__(self, top_k: int = 3, min_l1_for_l2: int = 3) -> None:
        self.entries: dict[str, Experience] = {}
        self.heuristics: list[Heuristic] = []
        self.top_k = top_k
        self.min_l1_for_l2 = min_l1_for_l2

    def record(self, exp: Experience) -> Experience:
        self.entries[exp.exp_id] = exp
        return exp

    # ── recall: the upper layer assembles ────────────────────────────
    def retrieve(self, task: str) -> list[Experience]:
        words = set(task.lower().split())
        scored = []
        for e in self.entries.values():
            if e.archived:
                continue
            kw = {k.lower() for k in e.keywords}
            score = len(words & kw) / len(kw) if kw else 0.0
            if score > 0.0:
                scored.append((score, e))
        scored.sort(key=lambda t: (t[0], t[1].effectiveness), reverse=True)
        hits = [e for _, e in scored[: self.top_k]]
        for e in hits:
            e.retrieval_count += 1
        return hits

    def render(self, hits: list[Experience]) -> str:
        """The context block the current task runs under. Lessons only —
        L0 steps stay in the store, referenced but not pasted."""
        lines = ["## Relevant past experience"]
        for e in hits:
            lines.append(f"- [{e.outcome}] {e.lesson}"
                         f" (effectiveness {e.effectiveness:.2f},"
                         f" L0 trace: {e.exp_id})")
        for h in self.heuristics:
            lines.append(f"- [heuristic] {h.insight}")
        lines.append("Use as background. Adapt, don't copy.")
        return "\n".join(lines)

    # ── the external signal: reuse outcomes write back ────────────────
    def feedback(self, injected: list[Experience],
                 downstream_success: bool) -> list[str]:
        """EMA-update every injected lesson with the downstream outcome.
        Returns the ids archived this round."""
        archived = []
        for e in injected:
            if e.archived:               # out of the pool: no longer injected
                continue
            e.reuse_outcomes.append(downstream_success)
            signal = 1.0 if downstream_success else 0.0
            e.effectiveness = 0.7 * e.effectiveness + 0.3 * signal
            if e.reuses >= MIN_REUSES and e.effectiveness < HEALTH_LINE:
                e.archived = True
                archived.append(e.exp_id)
        return archived

    # ── L2: cross-task distillation ───────────────────────────────────
    def distill(self, task_kind: str) -> Heuristic | None:
        """Enough similar L1 entries → one L2 heuristic. Deterministic
        here (joins the lessons); production uses a cheap LLM."""
        same = [e for e in self.entries.values()
                if e.task_kind == task_kind and not e.archived]
        if len(same) < self.min_l1_for_l2:
            return None
        insight = f"[{task_kind}] recurring lesson across {len(same)} runs: " + \
            same[0].lesson
        h = Heuristic(insight=insight, derived_from=[e.exp_id for e in same])
        self.heuristics.append(h)
        return h

    # ── graduation: soft lesson → hard guard candidate ───────────────
    def graduation_candidates(self) -> list[Experience]:
        """Deterministically checkable lessons with a proven track
        record belong in a pre-action guard, not in a prompt. The
        threshold reuses the pattern's own signal: no lesson graduates
        on plausibility alone."""
        return [e for e in self.entries.values()
                if not e.archived
                and e.effectiveness >= 0.7
                and e.reuses >= MIN_REUSES]
