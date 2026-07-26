"""Run the Reflection-module payroll labs through one controlled CLI."""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


HERE = Path(__file__).parent

LECTURE_COMMANDS = {
    "26": ("self_grade_lab.py",),
    "27": ("generator_critic_lab.py",),
    "28": ("skill_package_lab.py",),
    "29": ("experience_replay_lab.py",),
    "30": ("self_heal_lab.py",),
}

VARIANT_FLAGS = {
    "26": "--strict",
    "27": "--rubber-stamp",
    "28": "--no-gate",
    "29": "--no-feedback",
    "30": "--meltdown",
}


def run_lecture(lecture: str, *, variant: bool = False) -> int:
    command = [sys.executable, *LECTURE_COMMANDS[lecture]]
    if variant:
        command.append(VARIANT_FLAGS[lecture])

    print(f"[runner] lecture={lecture} variant={'on' if variant else 'off'}", flush=True)
    completed = subprocess.run(command, cwd=HERE, check=False)
    return completed.returncode


def main() -> int:
    parser = argparse.ArgumentParser(description="Run Reflection-module payroll labs.")
    parser.add_argument("--lecture", choices=[*LECTURE_COMMANDS, "all"], default="all")
    parser.add_argument(
        "--variant",
        action="store_true",
        help="Run the selected lecture's contrast variant.",
    )
    args = parser.parse_args()

    lectures = LECTURE_COMMANDS if args.lecture == "all" else (args.lecture,)
    for lecture in lectures:
        print(f"\n{'=' * 72}\nLecture {lecture}\n{'=' * 72}", flush=True)
        return_code = run_lecture(lecture, variant=args.variant and args.lecture != "all")
        if return_code:
            return return_code
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
