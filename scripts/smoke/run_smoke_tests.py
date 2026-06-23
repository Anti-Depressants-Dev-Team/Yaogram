#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from checks import run_smoke_checks
else:
    from .checks import run_smoke_checks


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run Yaogram repository smoke tests.",
    )
    parser.add_argument(
        "--verify-build",
        action="store_true",
        help="Also require a Debug YaoGram binary under out/Debug.",
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parents[2],
        help="Repository root (defaults to the checkout containing this script).",
    )
    args = parser.parse_args()

    results = run_smoke_checks(args.root, verify_build=args.verify_build)
    passed = 0
    for result in results:
        status = "PASS" if result.passed else "FAIL"
        print(f"[{status}] {result.name}: {result.detail}")
        if result.passed:
            passed += 1

    print()
    print(f"{passed}/{len(results)} smoke checks passed")
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
