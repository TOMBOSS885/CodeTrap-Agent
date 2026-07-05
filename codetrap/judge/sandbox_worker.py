from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
import sys


def disabled(*args, **kwargs):
    raise RuntimeError("operation disabled in sandbox")


def main() -> int:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    os.system = disabled
    solution_path = sys.argv[1]
    input_data = json.loads(sys.stdin.read())
    spec = importlib.util.spec_from_file_location("candidate_solution", solution_path)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load solution")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    if not hasattr(module, "solve"):
        raise RuntimeError("solution must define solve(input_data)")
    result = module.solve(input_data)
    print(json.dumps({"ok": True, "result": result}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(json.dumps({"ok": False, "error": type(exc).__name__, "message": str(exc)}, ensure_ascii=False))
        raise SystemExit(1)
