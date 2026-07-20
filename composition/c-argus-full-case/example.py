"""Minimal Full System Assembly example."""
from __future__ import annotations

from pattern import MODULE_ORDER


def main() -> None:
    print("Full System Assembly evidence order:")
    for index, module in enumerate(MODULE_ORDER, start=1):
        print(f"{index}. {module.value}")
    print("Run composition/payroll-lab/capstone_lab.py for the complete case.")


if __name__ == "__main__":
    main()
