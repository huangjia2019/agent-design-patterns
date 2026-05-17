# b · Semantic Compaction

> Column lecture **02-03** · pattern · perception × sequential
>
> [中文 README](README.zh-CN.md)

## The problem

Once the agent runs long enough, the candidate set won't fit even after
priority triage. You have to compact. Naïvely summarising the conversation
loses the one signal you can't afford to lose: which approaches the agent
has *already ruled out*. The classic failure mode is a 487-token connection-
pool stack trace getting flattened to "a database error occurred", after
which the agent spends three hours retrying approaches it already knew were
wrong.

## The pattern

Three layers, applied in order, stopping at the first layer that meets the
budget:

| Level | What it does | When |
|---|---|---|
| **L1 Clear tools** | Replace long tool outputs with placeholders | First try |
| **L2 Fold to anchor** | Merge old turns into a 5-field anchor state (intent / changes / decisions / **excluded approaches** / next steps) | When L1 isn't enough |
| **L3 Collapse errors** | Keep only the 3 most-recent error traces in full, summarise the rest into a "do not retry" list | Last resort |

Two non-negotiable invariants:

* **Error traces are never dropped.** The agent's feedback loop dies the
  moment they are.
* **Excluded approaches survive every level.** This is the slot that breaks
  the "agent keeps retrying ruled-out fixes" failure mode.

Trigger at ~60% window capacity, not 95%. Quality degradation starts well
before the window is full; the 95% community default just means "compact
after the agent has already gotten dumber".

## Quickstart

```bash
python perception/b-semantic-compaction/example.py
pytest perception/b-semantic-compaction/
```

The demo simulates a 30-turn debugging session, runs compaction, and prints
the resulting anchor state. You should see the three ruled-out approaches
(cache warming, retry-with-backoff, query rewriting) preserved in
`EXCLUDED (do not retry):` even though all 27 normal turns were collapsed.

## Files in this folder

| File | What it is |
|---|---|
| `pattern.py` | `SemanticCompactor` + `CompactionAnchor` + `Turn` + `CompactionEvent` — ≈ 220 lines |
| `example.py` | Debugging session demo with a deterministic stub LLM (runs without API keys) |
| `test_pattern.py` | Eight invariants, including the L1→L2→L3 ladder behaviour |

## Engineering references (verified)

* OpenHands' configurable condenser: [`openhands/core/config/condenser_config.py`](https://github.com/All-Hands-AI/OpenHands/blob/main/openhands/core/config/condenser_config.py)
  — five built-in condensers (NoOp, RecentEvents, LLMSummarizing,
  ObservationMasking, AmortizedForgetting). The V0 file is marked legacy;
  V1 lives in [software-agent-sdk](https://github.com/OpenHands/software-agent-sdk)
* Aider's tiny recursive-halving compactor: [`aider/history.py`](https://github.com/Aider-AI/aider/blob/main/aider/history.py)
  — 49 lines, depth cap 5, multi-model fallback
* Anthropic Claude Code compaction reference: [Best Practices · Context management](https://docs.claude.com/en/docs/claude-code/best-practices)
  — default 95% auto-trigger; community guidance commonly recommends 55–70%
* Manus' Context Engineering blog: [The 487-token stack trace story](https://manus.im/blog/Context-Engineering-for-AI-Agents-Lessons-from-Building-Manus)

## When this pattern doesn't apply

If your session is short (single-turn Q&A, fixed-pipeline ETL) or your tool
outputs are small (sub-100-token API responses), the cost of running the
anchor LLM call exceeds the savings. Compact only when total tokens exceed
~60% of your budget.
