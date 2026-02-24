Operational Runbook
===================

CI/CD Quick Reference
---------------------

- Pull requests and pushes to ``main`` run lint, type-check, and Windows executable build validation.
- Successful merges to ``main`` trigger automated versioning, changelog/README update, docs build, Python package build, PyInstaller build, tagging, and GitHub release.
- Commits must use Conventional Commits for semantic versioning.

Release Controls
----------------

- ``feat:`` bumps minor.
- ``fix:`` bumps patch.
- ``BREAKING CHANGE:`` or ``!`` bumps major.
- No release is produced when no qualifying commits exist.
- Tags are ``vMAJOR.MINOR.PATCH`` and created only on ``main``.

Windows Artifact Build
----------------------

- ``python scripts/build_windows.py`` creates:

  - ``dist/intel620-cli.exe``
  - ``dist/intel620-gui.exe``

PyPI Publishing
---------------

- Disabled by default.
- Enable by setting repository variable ``PUBLISH_TO_PYPI=true`` and configuring ``PYPI_API_TOKEN``.
