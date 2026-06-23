#!/usr/bin/env python3
from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SMOKE_RUNNER = REPO_ROOT / "scripts/smoke/run_smoke_tests.py"


def run_command(label: str, command: list[str], *, cwd: Path) -> int:
    print(f"==> {label}")
    print("    " + " ".join(command))
    proc = subprocess.run(command, cwd=cwd)
    return proc.returncode


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run Yaogram local smoke tests and optional Debug build verification.",
    )
    parser.add_argument(
        "--build",
        action="store_true",
        help="Build Debug Telegram target before verifying the YaoGram binary.",
    )
    parser.add_argument(
        "--verify-build",
        action="store_true",
        help="Require an existing Debug YaoGram binary under out/Debug.",
    )
    parser.add_argument(
        "--config",
        default="Debug",
        help="CMake configuration to build (default: Debug).",
    )
    args = parser.parse_args()

    if args.build and args.verify_build:
        print("Use either --build or --verify-build, not both.")
        return 2

    verify_build = args.verify_build or args.build

    smoke_command = [
        sys.executable,
        str(SMOKE_RUNNER),
    ]
    if verify_build:
        smoke_command.append("--verify-build")

    code = run_command("Smoke tests", smoke_command, cwd=REPO_ROOT)
    if code != 0:
        return code

    if not args.build:
        return 0

    cmake = shutil.which("cmake")
    if not cmake:
        print("cmake was not found on PATH; cannot run --build.")
        return 1

    build_code = run_command(
        f"Debug build ({args.config})",
        [
            cmake,
            "--build",
            "out",
            "--config",
            args.config,
            "--target",
            "Telegram",
        ],
        cwd=REPO_ROOT,
    )
    if build_code != 0:
        return build_code

    return run_command(
        "Post-build smoke verification",
        [
            sys.executable,
            str(SMOKE_RUNNER),
            "--verify-build",
        ],
        cwd=REPO_ROOT,
    )


if __name__ == "__main__":
    raise SystemExit(main())
