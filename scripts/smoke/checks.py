from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class SmokeResult:
    name: str
    passed: bool
    detail: str


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def check_required_paths(root: Path) -> SmokeResult:
    required = [
        "CMakeLists.txt",
        "Telegram/CMakeLists.txt",
        "Telegram/configure.py",
        "Telegram/configure.bat",
        "Telegram/configure.sh",
        "Telegram/build/version",
        "Telegram/SourceFiles/core/version.h",
        "Telegram/SourceFiles/mtproto/scheme/api.tl",
        "Telegram/SourceFiles/mtproto/scheme/mtproto.tl",
        "Telegram/Resources/langs/lang.strings",
        ".gitmodules",
    ]
    missing = [path for path in required if not (root / path).is_file()]
    if missing:
        return SmokeResult(
            "required_paths",
            False,
            "Missing files: " + ", ".join(missing),
        )
    return SmokeResult("required_paths", True, f"All {len(required)} required paths exist")


def check_yaogram_branding(root: Path) -> SmokeResult:
    version_h = (root / "Telegram/SourceFiles/core/version.h").read_text(encoding="utf-8")
    cmake = (root / "Telegram/CMakeLists.txt").read_text(encoding="utf-8")

    checks = [
        ('AppName = "YaoGram"' in version_h, 'version.h AppName'),
        ('AppFile = "YaoGram"' in version_h, 'version.h AppFile'),
        ("OUTPUT_NAME YaoGram" in cmake, "CMake OUTPUT_NAME YaoGram"),
    ]
    failed = [label for ok, label in checks if not ok]
    if failed:
        return SmokeResult(
            "yaogram_branding",
            False,
            "Branding checks failed: " + ", ".join(failed),
        )
    return SmokeResult("yaogram_branding", True, "YaoGram branding constants are present")


def check_version_file(root: Path) -> SmokeResult:
    text = (root / "Telegram/build/version").read_text(encoding="utf-8")
    fields = {
        "AppVersion": r"^AppVersion\s+(\d+)\s*$",
        "AppVersionStr": r"^AppVersionStr\s+(\S+)\s*$",
    }
    missing = []
    for name, pattern in fields.items():
        if not re.search(pattern, text, re.MULTILINE):
            missing.append(name)
    if missing:
        return SmokeResult(
            "version_file",
            False,
            "Missing version fields: " + ", ".join(missing),
        )
    return SmokeResult("version_file", True, "Telegram/build/version parses cleanly")


def check_git_submodules(root: Path) -> SmokeResult:
    gitmodules = (root / ".gitmodules").read_text(encoding="utf-8")
    expected = re.findall(r"^\s*path = (.+)$", gitmodules, re.MULTILINE)
    if not expected:
        return SmokeResult("git_submodules", False, ".gitmodules does not list any paths")

    try:
        proc = subprocess.run(
            ["git", "submodule", "status", "--recursive"],
            cwd=root,
            check=False,
            capture_output=True,
            text=True,
        )
    except OSError as error:
        return SmokeResult(
            "git_submodules",
            False,
            f"Could not run git submodule status: {error}",
        )

    if proc.returncode != 0:
        return SmokeResult(
            "git_submodules",
            False,
            proc.stderr.strip() or "git submodule status failed",
        )

    lines = [line.strip() for line in proc.stdout.splitlines() if line.strip()]
    uninitialized = [line for line in lines if line.startswith("-")]
    if uninitialized:
        return SmokeResult(
            "git_submodules",
            False,
            "Uninitialized submodules: " + ", ".join(uninitialized[:5]),
        )

    if len(lines) < len(expected):
        return SmokeResult(
            "git_submodules",
            False,
            f"Expected {len(expected)} submodule entries, found {len(lines)}",
        )

    return SmokeResult(
        "git_submodules",
        True,
        f"Submodule registry and checkout look healthy ({len(lines)} entries)",
    )


def check_api_schemes(root: Path) -> SmokeResult:
    paths = [
        root / "Telegram/SourceFiles/mtproto/scheme/api.tl",
        root / "Telegram/SourceFiles/mtproto/scheme/mtproto.tl",
    ]
    constructor_pattern = re.compile(r"^[a-zA-Z0-9_.#]+ = .+;$")
    for path in paths:
        text = path.read_text(encoding="utf-8")
        if len(text.strip()) < 100:
            return SmokeResult(
                "api_schemes",
                False,
                f"{path.name} looks too small to be valid",
            )
        if not any(constructor_pattern.match(line.strip()) for line in text.splitlines()):
            return SmokeResult(
                "api_schemes",
                False,
                f"{path.name} does not contain TL constructor definitions",
            )
    return SmokeResult("api_schemes", True, "api.tl and mtproto.tl look valid")


def check_build_output(root: Path) -> SmokeResult:
    candidates = [
        root / "out/Debug/YaoGram.exe",
        root / "out/Debug/YaoGram",
        root / "out/Debug/YaoGram.app/Contents/MacOS/YaoGram",
    ]
    existing = [path for path in candidates if path.is_file()]
    if not existing:
        return SmokeResult(
            "build_output",
            False,
            "No Debug YaoGram binary found under out/Debug",
        )
    path = existing[0]
    size = path.stat().st_size
    if size < 1024 * 1024:
        return SmokeResult(
            "build_output",
            False,
            f"{path.relative_to(root)} exists but is suspiciously small ({size} bytes)",
        )
    return SmokeResult(
        "build_output",
        True,
        f"Found {path.relative_to(root)} ({size:,} bytes)",
    )


def run_smoke_checks(
    root: Path,
    *,
    verify_build: bool,
) -> list[SmokeResult]:
    results = [
        check_required_paths(root),
        check_yaogram_branding(root),
        check_version_file(root),
        check_git_submodules(root),
        check_api_schemes(root),
    ]
    if verify_build:
        results.append(check_build_output(root))
    return results
