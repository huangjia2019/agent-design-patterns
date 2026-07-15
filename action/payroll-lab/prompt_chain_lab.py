"""Lecture 24 hands-on: the payroll run as a prompt chain with gates.

Reuses the Prompt Chaining pattern from ../c-prompt-chaining/pattern.py.
Four steps, each its own prompt / model / gate:

    settle -> reconcile -> instructions -> payment_request

The model is mocked (deterministic, no API key): on its FIRST attempt at
the instructions step it transposes two digits of the payroll total --
exactly the kind of silent number mutation a model makes when it copies
figures by hand. Run one: the checksum gate catches it, the retry passes.
Run two: same chain, gate loosened to "non-empty" -- watch the bad number
flow all the way into the final payment request.

Run `python3 db.py` first, then `python3 prompt_chain_lab.py`.
"""
import sqlite3
import sys
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE.parent / "c-prompt-chaining"))
from pattern import ChainStep, PromptChain, keys_gate  # noqa: E402

DB = HERE / "payroll.db"
MONTH = "2026-06"
con = sqlite3.connect(DB)
TOTAL = con.execute(
    "SELECT SUM(base + bonus + adjustment) FROM payroll WHERE month=?", (MONTH,)
).fetchone()[0]
HEADCOUNT = con.execute(
    "SELECT COUNT(*) FROM payroll WHERE month=?", (MONTH,)).fetchone()[0]


def transpose(n):
    s = str(n)
    return int(s[:2] + s[3] + s[2] + s[4:])   # swap two inner digits


# ---- the mock model: deterministic, and flawed in a realistic way ----------

attempts = {"instructions": 0}


def mock_llm(prompt, system_prompt, model):
    if "[STEP:settle]" in system_prompt:
        return f"SETTLEMENT month={MONTH} headcount={HEADCOUNT} total={TOTAL}"
    if "[STEP:reconcile]" in system_prompt:
        return f"RECONCILED delta=0 total={TOTAL} approvals=all-applied"
    if "[STEP:instructions]" in system_prompt:
        attempts["instructions"] += 1
        # First attempt: the model copies the total by hand and transposes
        # two digits. Second attempt gets it right.
        total = transpose(TOTAL) if attempts["instructions"] == 1 else TOTAL
        return f"INSTRUCTIONS batches=4 headcount={HEADCOUNT} total={total}"
    if "[STEP:payment_request]" in system_prompt:
        # The final document trusts whatever the instructions step said.
        stated = prompt.split("total=")[-1].split()[0]
        return (f"PAYMENT-REQUEST month={MONTH} headcount={HEADCOUNT} "
                f"total={stated} status=APPROVAL-PENDING")
    return ""


def checksum_gate(output):
    """The stated total must equal the ledger total, to the yuan."""
    return f"total={TOTAL}" in output


def build_chain(instructions_gate, gate_description):
    steps = [
        ChainStep("settle", "summarize the month's settlement",
                  system_prompt="[STEP:settle] You are the settlement clerk.",
                  prompt_template="Summarize the payroll ledger for {user_input}.",
                  model="opus-tier",
                  gate=keys_gate([f"total={TOTAL}", f"headcount={HEADCOUNT}"]),
                  gate_description="keys: ledger total + headcount"),
        ChainStep("reconcile", "reconcile settlement against approvals",
                  system_prompt="[STEP:reconcile] You are the reconciliation clerk.",
                  prompt_template="Reconcile this settlement: {settle}",
                  model="sonnet-tier",
                  gate=checksum_gate,
                  gate_description="checksum: total matches ledger"),
        ChainStep("instructions", "write the transfer instructions",
                  system_prompt="[STEP:instructions] You are the instructions writer.",
                  prompt_template="Write transfer instructions from: {reconcile}",
                  model="haiku-tier",
                  gate=instructions_gate,
                  gate_description=gate_description),
        ChainStep("payment_request", "draft the payment request for sign-off",
                  system_prompt="[STEP:payment_request] You draft payment requests.",
                  prompt_template="Draft the payment request from: {instructions}",
                  model="haiku-tier",
                  gate=keys_gate(["APPROVAL-PENDING"]),
                  gate_description="keys: pending human approval"),
    ]
    return PromptChain(steps, mock_llm)


def show(trace, models):
    for run in trace.runs:
        flag = {"success": "PASS ", "gate_failed": "GATE!",
                "retry_exhausted": "DEAD ", "llm_error": "ERROR",
                "template_error": "WIRE!"}[run.result.value]
        print(f"   [{flag}] {run.step_id:16s} attempt {run.attempt} "
              f"({models[run.step_id]:11s} gate: {run.gate_description})")
        if run.result.value == "gate_failed":
            print(f"           rejected output: {run.output}")
    print(f"   final: {trace.final_output}")


MODELS = {"settle": "opus-tier", "reconcile": "sonnet-tier",
          "instructions": "haiku-tier", "payment_request": "haiku-tier"}

print(f"== ledger truth: {HEADCOUNT} people, total={TOTAL} ==")

print("\n== run 1: checksum gate between instructions and payment ==")
chain = build_chain(checksum_gate, "checksum: total matches ledger")
trace = chain.run(f"payroll {MONTH}")
show(trace, MODELS)

print("\n== run 2: same chain, gate loosened to 'non-empty' ==")
attempts["instructions"] = 0                      # the model will err again
chain = build_chain(lambda out: bool(out.strip()), "non-empty (naked)")
trace = chain.run(f"payroll {MONTH}")
show(trace, MODELS)
stated = trace.final_output.split("total=")[-1].split()[0]
print(f"\n[AUDIT] ledger says {TOTAL}, payment request says {stated} -- "
      f"difference of {abs(TOTAL - int(stated))} yuan, "
      f"and every step after the mutation reported SUCCESS.")
