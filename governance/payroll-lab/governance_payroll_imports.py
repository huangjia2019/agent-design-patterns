"""Load Payroll Governance Lab siblings under collision-resistant module names."""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType


HERE = Path(__file__).parent
MODULE_PREFIX = "_adps_governance_payroll"


def load_local(name: str) -> ModuleType:
    """Load one sibling without claiming generic names such as ``bench``."""
    module_name = f"{MODULE_PREFIX}_{name}"
    cached = sys.modules.get(module_name)
    if cached is not None:
        return cached

    path = HERE / f"{name}.py"
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load governance payroll module: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    try:
        spec.loader.exec_module(module)
    except BaseException:
        sys.modules.pop(module_name, None)
        raise
    return module
