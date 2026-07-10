"""ActionTrace -- the shared observability layer for the Action module (lectures 21-25).

Every action pattern in this directory (tool dispatch, plan-and-execute,
prompt chaining, guardrail sandwich) logs into the same trace, and the trace
computes the four production metrics the course tracks:

    tool call success rate   -- healthy > 80% per tool
    argument repair rate     -- healthy < 15%
    guardrail block rate     -- healthy between 1% and 20%
    scope creep ratio        -- healthy < 1.5; above 3.0 is an alarm

Run this file directly for a demo against the naked loop's behaviour.
"""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import IntEnum
from typing import Dict, List


class RiskLevel(IntEnum):
    LOW = 1        # reads
    MEDIUM = 2     # local writes
    HIGH = 3       # external API calls
    CRITICAL = 4   # irreversible: delete / drop / money transfer


@dataclass
class ActionEvent:
    """One atomic action decision."""
    action_id: str
    tool_name: str
    risk_level: RiskLevel
    arguments_repaired: bool = False   # tool-dispatch self-repair fired
    guardrail_blocked: bool = False    # input filter stopped it
    guardrail_reason: str = ""
    success: bool = False
    retry_count: int = 0
    planned: bool = True               # planned vs. improvised ("nobody asked")
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass
class ActionTrace:
    """The whole session's action sequence + the four production metrics."""
    session_id: str
    events: List[ActionEvent] = field(default_factory=list)

    def log(self, event: ActionEvent) -> None:
        self.events.append(event)

    def tool_call_success_rate(self) -> Dict[str, float]:
        per_tool: Dict[str, List[bool]] = {}
        for e in self.events:
            per_tool.setdefault(e.tool_name, []).append(e.success)
        return {t: sum(r) / len(r) for t, r in per_tool.items()}

    def argument_repair_rate(self) -> float:
        return (sum(e.arguments_repaired for e in self.events) / len(self.events)
                if self.events else 0.0)

    def guardrail_block_rate(self) -> float:
        return (sum(e.guardrail_blocked for e in self.events) / len(self.events)
                if self.events else 0.0)

    def scope_creep_ratio(self) -> float:
        planned = sum(e.planned for e in self.events)
        return len(self.events) / planned if planned else 0.0

    def health_check(self) -> Dict[str, str]:
        report: Dict[str, str] = {}
        for tool, rate in self.tool_call_success_rate().items():
            if rate < 0.80:
                report[f"tool::{tool}"] = f"WARN {rate:.0%} (<80%: bad schema or flaky impl)"
        if (ar := self.argument_repair_rate()) > 0.15:
            report["argument_repair"] = f"WARN {ar:.0%} (>15%: unreliable tool schema)"
        gb = self.guardrail_block_rate()
        if gb > 0.20:
            report["guardrail_block"] = f"WARN {gb:.0%} (>20%: agent keeps overreaching)"
        elif self.events and gb < 0.01:
            report["guardrail_block"] = f"WARN {gb:.0%} (<1%: guardrail may be asleep)"
        if (sc := self.scope_creep_ratio()) > 1.5:
            level = "ALARM" if sc > 3.0 else "WARN"
            report["scope_creep"] = f"{level} ratio={sc:.1f} (>1.5: agent is 'helpfully' improvising)"
        return report


if __name__ == "__main__":
    # Replay what naked_loop.py actually did, as a trace: 3 planned actions,
    # 4 improvised ones. Watch the scope-creep alarm fire.
    trace = ActionTrace(session_id="payroll-2026-06")
    planned = [("apply_approval", RiskLevel.MEDIUM), ("apply_approval", RiskLevel.MEDIUM),
               ("pay_everyone", RiskLevel.CRITICAL)]
    improvised = [("normalize_bank_account", RiskLevel.CRITICAL),
                  ("normalize_bank_account", RiskLevel.CRITICAL),
                  ("clear_note", RiskLevel.MEDIUM), ("clear_note", RiskLevel.MEDIUM)]
    for i, (tool, risk) in enumerate(planned + improvised):
        trace.log(ActionEvent(action_id=f"a{i}", tool_name=tool, risk_level=risk,
                              success=True, planned=(tool, risk) in planned))
    print(f"scope creep ratio: {trace.scope_creep_ratio():.2f}")
    for key, msg in trace.health_check().items():
        print(f"  {key}: {msg}")
