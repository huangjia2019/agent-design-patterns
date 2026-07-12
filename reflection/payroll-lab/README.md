# payroll-lab — hands-on bench for the Reflection module

[简体中文](README.zh-CN.md)

Continues the payroll bench from [`../../action/payroll-lab/`](../../action/payroll-lab/):
same SQLite database, now at month-end — 798 payslips PAID, 2 REVERSED
(the saga rollback from the Action module). The agent wrote a monthly
report claiming 800 paid, 0 reversed. The Reflection module's question:
how does it find out the report is wrong?

```bash
python3 self_grade_lab.py            # introspection vs. one external signal
python3 self_grade_lab.py --strict   # a harsher self-critic changes the score, not the findings

python3 generator_critic_lab.py             # lecture 27: generator-critic, three scenes
python3 generator_critic_lab.py --stubborn  # rounds exhausted, hand to a human

python3 skill_package_lab.py                # lecture 28: verification gate + VERIFIED-only routing
python3 skill_package_lab.py --no-gate      # stored without the gate: 209/800 bases wrong

python3 experience_replay_lab.py                # lecture 29: recall changes the decision + reuse outcomes write back
python3 experience_replay_lab.py --no-feedback  # feedback loop cut: the superstition never leaves the pool
```

The introspective critic approves the wrong report twice (it can check
consistency, not truth). Two SQL counts against the ledger reject it
immediately. That contrast is the module's spine: reflection needs an
external signal to close the loop.

| Pattern (coordinate) | External signal | Directory |
|:--|:--|:--|
| Generator-Critic (Reflection × Chain) | reconciliation tests / schema | `generator_critic_lab.py` here + [`../a-generator-critic/`](../a-generator-critic/) |
| Skill Package (Reflection × Router) | verified-before-stored | `skill_package_lab.py` here + [`../b-skill-package/`](../b-skill-package/) |
| Experience Replay (Reflection × Hierarchy) | post-reuse success rate | `experience_replay_lab.py` here + [`../c-experience-replay/`](../c-experience-replay/) |
| Self-Heal Loop (Reflection × Loop) | deterministic CI signals | [`../d-self-heal-loop/`](../d-self-heal-loop/) |
