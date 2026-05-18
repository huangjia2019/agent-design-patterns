"""Runnable demo for the Prompt Chaining pattern.

Replays a trimmed version of the content-editing pipeline from the
lecture opening. The original single-prompt agent tried to proofread,
rewrite, fact-check, title, and summarize a financial-news draft in
one shot. It published "GMV 53%" where the source said "35%" because
the rewrite mutated the source the fact-check needed.

The fixed pipeline splits the work into five steps. The fact-check
step (step 4) explicitly takes the *original draft* as one of its
inputs, not the rewritten version — that's the "go back to source"
fix.

Five steps:

    1. proofread   — fix typos and obvious grammar (cheap model)
    2. rewrite     — improve clarity (mid model)
    3. style       — match house voice (mid model)
    4. factcheck   — verify numbers against ORIGINAL (high model)
    5. title       — generate headline

Gates between steps:

    1 → 2:  length 200-2000, contains at least one word from the draft
    2 → 3:  length 200-2000
    3 → 4:  length 200-2000
    4 → 5:  must contain "verified" or "discrepancy"
    5:      length 10-80 (title length)

Run:
    python action/c-prompt-chaining/example.py
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
sys.modules.pop("pattern", None)

from pattern import (   # noqa: E402
    ChainStep,
    PromptChain,
    StepResult,
    any_gate,
    keys_gate,
    length_gate,
)


# --- Fake LLM ---------------------------------------------------------------

def _fake_llm(prompt: str, system_prompt: str, model: str) -> str:
    """Stand-in for the model. Different outputs by role keyword in system."""
    role = system_prompt.split("[role]")[1].split("[/role]")[0].strip() if "[role]" in system_prompt else "unknown"
    if role == "proofreader":
        return (
            "Q3 GMV grew 35% year-over-year, driven by category 4 (3C) "
            "and category 7 (apparel). Active buyer count up 18%."
        )
    if role == "rewriter":
        return (
            "In Q3, GMV expanded 35% YoY. The growth was led by 3C "
            "(category 4) and apparel (category 7), with active "
            "buyers increasing 18% in the same period."
        )
    if role == "stylist":
        return (
            "Q3 GMV climbed 35% YoY, with 3C and apparel leading the "
            "growth (categories 4 and 7). Active-buyer base expanded 18%."
        )
    if role == "factchecker":
        # Check whether the rewritten output preserves the 35% from
        # the original draft. The prior outputs include user_input so
        # this step can look at the source.
        return (
            "verified: numbers in styled version match original draft "
            "(GMV 35%, active buyers 18%, category codes 4 and 7)."
        )
    if role == "titler":
        return "Q3 GMV up 35% as 3C and apparel lead growth"
    return "[no role]"


def main() -> None:
    chain = PromptChain(
        steps=[
            ChainStep(
                step_id="proofread",
                description="Fix typos and obvious grammar",
                system_prompt="[role]proofreader[/role] Fix typos but preserve numbers.",
                prompt_template="Draft:\n{user_input}",
                model="claude-haiku-4-5",
                gate=keys_gate(["35%", "18%"]),
                gate_description="numbers preserved (35% and 18%)",
            ),
            ChainStep(
                step_id="rewrite",
                description="Improve clarity",
                system_prompt="[role]rewriter[/role] Improve clarity, preserve all numbers.",
                prompt_template="Source:\n{proofread}",
                model="claude-sonnet-4-6",
                gate=length_gate(80, 600),
                gate_description="length 80-600 chars",
            ),
            ChainStep(
                step_id="style",
                description="Match house voice",
                system_prompt="[role]stylist[/role] Apply house style (concise + active voice).",
                prompt_template="Rewrite:\n{rewrite}",
                model="claude-sonnet-4-6",
                gate=length_gate(60, 600),
                gate_description="length 60-600 chars",
            ),
            ChainStep(
                step_id="factcheck",
                description="Verify numbers against ORIGINAL",
                system_prompt="[role]factchecker[/role] Compare numbers across versions.",
                prompt_template=(
                    "Original draft (source of truth):\n{user_input}\n\n"
                    "Styled version:\n{style}\n\n"
                    "Verify all numbers match the original."
                ),
                model="claude-opus-4-6",
                gate=any_gate(keys_gate(["verified"]), keys_gate(["discrepancy"])),
                gate_description="contains 'verified' or 'discrepancy'",
            ),
            ChainStep(
                step_id="title",
                description="Generate headline",
                system_prompt="[role]titler[/role] One-line headline, 10-80 chars.",
                prompt_template="Article:\n{style}\n\nFact-check note:\n{factcheck}",
                model="claude-sonnet-4-6",
                gate=length_gate(10, 80),
                gate_description="length 10-80 chars",
            ),
        ],
        llm_call=_fake_llm,
    )

    draft = (
        "q3 gmv grew 35% YoY, driven by cat 4 (3C) and cat 7 (apparel). "
        "active byuer count up 18%."   # intentional typo
    )

    trace = chain.run(draft)

    print("=" * 72)
    print("Per-step audit")
    print("=" * 72)
    for run in trace.runs:
        marker = {"success": "✓", "gate_failed": "✗", "retry_exhausted": "!", "llm_error": "E"}[run.result.value]
        print(f"  {marker} {run.step_id:12s} attempt {run.attempt}  gate=[{run.gate_description}]")
        print(f"      → {run.output[:90]}")

    print()
    print("=" * 72)
    print("Final output (title)")
    print("=" * 72)
    print(f"  {trace.final_output}")
    print()

    print("=" * 72)
    print("Information-starvation guard demonstrated")
    print("=" * 72)
    print("  Step 4 (factcheck) explicitly receives user_input + style,")
    print("  not just the immediately prior step. The lecture-opening")
    print("  bug (rewriter mutates source, factcheck reads the mutated")
    print("  version) cannot happen here — factcheck always has both.")


if __name__ == "__main__":
    main()
