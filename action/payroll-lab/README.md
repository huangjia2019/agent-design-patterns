# payroll-lab — hands-on bench for the Action module

[简体中文](README.zh-CN.md)

A mock payroll system (single-file SQLite: 800 employees, one month of draft
payslips, two approved-but-unapplied changes) used as the running hands-on
bench for the Action patterns in this directory. Fake data, real schema,
visible side effects. No API key, no cloud — Python 3 only.

```bash
python3 db.py           # create payroll.db + baseline snapshot
python3 naked_loop.py   # a ~50-line PRA loop with NO guardrails
python3 db.py --diff    # see every row it touched
```

The loop applies the approvals and pays 800 people in one shot — and also
"helpfully" normalizes two bank accounts and wipes a dissent note nobody
asked it to touch. Then:

```bash
python3 db.py && python3 db.py --inject-typo   # a fat-fingered 999999 approval
python3 naked_loop.py                          # watch it apply that too
```

That failure is what the four Action patterns fix, one layer at a time:

| Pattern (coordinate) | Directory |
|:--|:--|
| Tool Dispatch (Action × Router) | `tool_dispatch_lab.py` here (payroll five-scene demo) + [`../a-tool-dispatch/`](../a-tool-dispatch/) |
| Plan-and-Execute (Action × Orchestration) | [`../b-plan-and-execute/`](../b-plan-and-execute/) |
| Prompt Chaining (Action × Chain) | [`../c-prompt-chaining/`](../c-prompt-chaining/) |
| Guardrail Sandwich (Action × Hierarchy) | [`../d-guardrail-sandwich/`](../d-guardrail-sandwich/) |

`action_trace.py` is the shared observability layer: the four production
metrics (tool-call success rate, argument repair rate, guardrail block rate,
scope creep ratio) plus a health check. Run it directly for a demo where the
scope-creep alarm fires on the naked loop's behaviour.
