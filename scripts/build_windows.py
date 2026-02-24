#!/usr/bin/env python3
from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"
BUILD = ROOT / "build"

ENTRYPOINTS: tuple[tuple[str, str], ...] = (
    ("main.py", "intel620-gui"),
    ("cli.py", "intel620-cli"),
)


def run_pyinstaller(entry: str, name: str) -> None:
    subprocess.run(
        [
            sys.executable,
            "-m",
            "PyInstaller",
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


def ensure_entrypoints_exist() -> None:
    missing = [entry for entry, _ in ENTRYPOINTS if not (ROOT / entry).exists()]
    if missing:
        files = ", ".join(missing)
        raise FileNotFoundError(f"Missing build entrypoint files: {files}")


def remove_spec_files() -> None:
    for spec_file in ROOT.glob("*.spec"):
        spec_file.unlink()


def verify_artifacts() -> None:
    expected = [DIST / f"{name}.exe" for _, name in ENTRYPOINTS]
    missing = [str(path.relative_to(ROOT)) for path in expected if not path.exists()]
    if missing:
        message = ", ".join(missing)
        raise RuntimeError(f"Build completed but missing expected artifact(s): {message}")


def clean_directories() -> None:
    for directory in (BUILD, DIST):
        if directory.exists():
            shutil.rmtree(directory)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build Intel620 Windows executables using PyInstaller."
    )
    parser.add_argument(
        "--no-clean",
        action="store_true",
        help="Keep existing build/dist folders before building.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    ensure_entrypoints_exist()
    if not args.no_clean:
        clean_directories()

    for entry, name in ENTRYPOINTS:
        run_pyinstaller(entry, name)

    remove_spec_files()
    verify_artifacts()

    print("Build succeeded. Artifacts:")
    for _, name in ENTRYPOINTS:
        print(f"- dist/{name}.exe")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
