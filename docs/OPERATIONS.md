# CI/CD and Release Operations

## Pipelines

- **CI (`ci.yml`)**: Runs on `pull_request` and `push` to `main` on `windows-latest`; enforces Ruff, mypy, and PyInstaller build validation.
- **CD (`release.yml`)**: Runs on `push` to `main`; computes semantic version, updates metadata/docs/changelog, builds docs, builds Python distributions, builds Windows executables with PyInstaller, creates annotated tags, creates GitHub Release, and optionally publishes to PyPI.

## Versioning and Tagging Rules

- `feat:` => minor bump
- `fix:` => patch bump
- `BREAKING CHANGE` or `!` in type/scope => major bump
- Tag format: `vMAJOR.MINOR.PATCH`
- Tags are annotated and immutable (release script fails if tag already exists)
- Tagging occurs only from `main` after successful quality/build gates

## Windows Build Outputs

PyInstaller build script (`scripts/build_windows.py`) generates deterministic release-friendly executables:

- `dist/intel620-cli.exe` (from `cli.py`)
- `dist/intel620-gui.exe` (from `main.py`)

## Determinism and Security

- Tooling dependencies are pinned in `pyproject.toml`.
- Build uses PEP 517 (`python -m build`) and PyInstaller artifact generation.
- Workflow permissions are minimized to required scopes.
- Release is blocked on any lint/type/build/docs failure.

## Failure Handling

- No version bump/tag/release is created if any release stage fails.
- If no qualifying Conventional Commit exists, pipeline exits cleanly without release side effects.

## Commit Message Examples

- `feat(gui): add advanced display diagnostics panel`
- `fix(dxgi): handle missing adapter names safely`
- `feat(core)!: replace adapter enumeration path`
- `chore(ci): tighten release artifact validation`
