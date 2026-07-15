"""Run the complete Action-module payroll story in lecture order.

Each lecture is an isolated experiment. The database is reset before every
scene so one pattern's side effects cannot make a later pattern look correct.
"""
from __future__ import annotations

import argparse
import sqlite3
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


HERE = Path(__file__).parent
DB = HERE / "payroll.db"
MONTH = "2026-06"


@dataclass(frozen=True)
class Scene:
    lecture: str
    title: str
    commands: tuple[tuple[str, ...], ...]


SCENES = (
    Scene(
        "21",
        "Naked PRA loop: scope creep",
        (("naked_loop.py",), ("action_trace.py",)),
    ),
    Scene(
        "21",
        "Naked PRA loop: approved 999999 passes through",
        (("db.py", "--inject-typo"), ("naked_loop.py",)),
    ),
    Scene("22", "Tool Dispatch", (("tool_dispatch_lab.py",),)),
    Scene("23", "Plan-and-Execute", (("plan_execute_lab.py",),)),
    Scene("24", "Prompt Chaining", (("prompt_chain_lab.py",),)),
    Scene(
        "25",
        "Guardrail Sandwich",
        (("db.py", "--inject-typo"), ("guardrail_lab.py",)),
    ),
)


def run_python(*args: str) -> None:
    subprocess.run([sys.executable, *args], cwd=HERE, check=True)


def reset_database() -> None:
    run_python("db.py")


def state_summary() -> str:
    con = sqlite3.connect(DB)
    try:
        payroll = dict(con.execute(
            "SELECT status, COUNT(*) FROM payroll WHERE month=? GROUP BY status",
            (MONTH,),
        ))
        approvals = dict(con.execute(
            "SELECT status, COUNT(*) FROM approvals GROUP BY status"
        ))
        return f"payroll={payroll}, approvals={approvals}"
    finally:
        con.close()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run lectures 21-25 as isolated payroll experiments."
    )
    parser.add_argument(
        "--lecture",
        choices=("all", "21", "22", "23", "24", "25"),
        default="all",
        help="run all scenes or one lecture (default: all)",
    )
    parser.add_argument(
        "--keep-state",
        action="store_true",
        help="keep the final scene's database state for inspection",
    )
    args = parser.parse_args()

    selected = [
        scene for scene in SCENES
        if args.lecture == "all" or scene.lecture == args.lecture
    ]

    try:
        for index, scene in enumerate(selected, start=1):
            print("\n" + "=" * 78, flush=True)
            print(
                f"[{index}/{len(selected)}] Lecture {scene.lecture} | {scene.title}",
                flush=True,
            )
            print("[runner] isolated reset", flush=True)
            reset_database()
            for command in scene.commands:
                print(f"[runner] {sys.executable} {' '.join(command)}", flush=True)
                run_python(*command)
            print(f"[runner] state: {state_summary()}", flush=True)
    finally:
        if not args.keep_state:
            print("\n[runner] restoring baseline database", flush=True)
            reset_database()

    print("[runner] complete", flush=True)


if __name__ == "__main__":
    main()
