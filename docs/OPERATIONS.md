# CI/CD and Release Operations

## Pipelines

- **CI (`ci.yml`)**: Runs on `pull_request` and `push` to `main`; enforces Ruff, mypy, pytest + coverage.
- **CD (`release.yml`)**: Runs on `push` to `main`; computes semantic version, updates metadata/docs/changelog, tags, builds artifacts, creates GitHub Release, optionally publishes to PyPI.

## Versioning and Tagging Rules

- `feat:` => minor bump
- `fix:` => patch bump
- `BREAKING CHANGE` or `!` in type/scope => major bump
- Tag format: `vMAJOR.MINOR.PATCH`
- Tags are annotated and immutable (release script fails if tag already exists)
- Release only occurs from `main` and only after successful CI gates in the same workflow

## Determinism and Security

- Tooling dependencies are pinned in `pyproject.toml`.
- Build uses PEP 517 (`python -m build`) and artifacts are generated from committed source.
- Workflows run with least privilege (`contents: write` only where required).
- `persist-credentials: false` used on checkout; credentials are scoped to explicit push/tag operations.

## Failure Handling

- Any lint/type/test/build/docs failure blocks tagging and release.
- No version bump/tag/release is created on failure.
- If no releasable Conventional Commit exists, pipeline exits cleanly without release side effects.

## Commit Message Examples

- `feat(ui): add adaptive refresh-rate diagnostics`
- `fix(api): handle null monitor EDID`
- `feat(core)!: replace legacy display probe`
- `chore(ci): refresh pinned tooling versions`
