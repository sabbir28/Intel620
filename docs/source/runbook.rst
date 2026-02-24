Operational Runbook
===================

CI/CD Quick Reference
---------------------

- Pull requests and pushes to ``main`` run lint, type-check, and tests.
- Successful merges to ``main`` trigger automated versioning, tagging, release packaging, and docs build.
- Commits must use Conventional Commits for semantic versioning.

Release Controls
----------------

- ``feat:`` bumps minor.
- ``fix:`` bumps patch.
- ``BREAKING CHANGE:`` or ``!`` bumps major.
- No release is produced when no qualifying commits exist.
- Tags are ``vMAJOR.MINOR.PATCH`` and created only on ``main``.

PyPI Publishing
---------------

- Disabled by default.
- Enable by setting repository variable ``PUBLISH_TO_PYPI=true`` and configuring ``PYPI_API_TOKEN``.
