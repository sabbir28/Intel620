#!/usr/bin/env python3
from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"
BUILD = ROOT / "build"


def run_pyinstaller(entry: str, name: str) -> None:
    subprocess.run(
        [
            "pyinstaller",
            "--noconfirm",
            "--clean",
            "--onefile",
            "--name",
            name,
            entry,
        ],
        cwd=ROOT,
        check=True,
    )


def main() -> int:
    if BUILD.exists():
        shutil.rmtree(BUILD)

    run_pyinstaller("BootUp.py", "intel620-gui")
    run_pyinstaller("GPU.py", "intel620-cli")

    # keep only executable artifacts for release payload consistency
    spec_files = list(ROOT.glob("*.spec"))
    for spec in spec_files:
        spec.unlink()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
