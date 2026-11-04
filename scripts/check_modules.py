"""Run both modules' test suites from their expected working directories."""

import subprocess
import sys
from pathlib import Path


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    suites = (
        ("Code Manager and integration", root, ["-m", "pytest", "-q"]),
        (
            "Parsing and Analysis",
            root / "FlowBridge_ParsingAndAnalysis",
            ["-m", "unittest", "discover", "-s", "tests", "-q"],
        ),
    )
    for label, directory, arguments in suites:
        print(f"\n{label}", flush=True)
        result = subprocess.run([sys.executable, *arguments], cwd=directory)
        if result.returncode:
            return result.returncode
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
