# Contributing to Neo Execution Specs

Thanks for contributing. This guide keeps contributions professional, reproducible, and release-safe.

## Prerequisites

- Python 3.11+
- Git
- Familiarity with Neo N3 protocol concepts

## Local Setup

```bash
git clone https://github.com/YOUR_USERNAME/neo-execution-specs.git
cd neo-execution-specs
python -m venv .venv
source .venv/bin/activate
pip install -e ".[all]"
```

## Branching

```bash
git checkout -b feature/your-feature
# or
git checkout -b fix/your-fix
```

## Required Quality Gates (before PR)

Run these from repo root:

```bash
# 1) Lint (includes scripts)
ruff check src tests scripts

# 2) Full test suite
pytest

# 3) Packaging integrity
python scripts/check_release_metadata.py
pip install build twine
rm -rf dist build
python -m build --sdist --wheel
twine check dist/*

# 4) Console entrypoints (installed wheel smoke)
pip install --force-reinstall dist/*.whl
neo-diff --help
neo-compat --help
neo-multicompat --help
neo-coverage --help
neo-t8n --help
```

## Optional / Informational Checks

```bash
# Type checking is currently non-gating while backlog is reduced
mypy src/neo --ignore-missing-imports
```

## Code Style

- Follow PEP 8 and existing project conventions.
- Keep lines at 100 chars max.
- Add type hints for new/updated public APIs.
- Add or update tests for behavior changes.
- Keep changes focused and minimal.

## Commit Message Convention

Use conventional commits:

- `feat:` new feature
- `fix:` bug fix
- `docs:` docs-only changes
- `test:` tests
- `refactor:` internal refactor without behavior change
- `chore:` tooling/workflow/maintenance

Examples:

- `feat(vm): add CALLT edge-case vector coverage`
- `fix(diff): normalize ByteString comparison semantics`
- `chore(ci): add release metadata consistency checks`

## Pull Request Checklist

- [ ] Tests pass locally (`pytest`)
- [ ] Lint passes (`ruff check src tests scripts`)
- [ ] Packaging checks pass (`check_release_metadata` + `build` + `twine check`)
- [ ] New behavior has tests
- [ ] Docs/changelog updated when relevant
- [ ] PR description clearly explains intent and impact

## Release Consistency Notes

For release PRs and tags:

- Keep `pyproject.toml` version and `src/neo/__init__.py` `__version__` identical.
- Add a matching version heading in `CHANGELOG.md` (`## [X.Y.Z] - YYYY-MM-DD`).
- Tag format must be `vX.Y.Z`.

## Questions

- Open a GitHub issue for bugs/questions.
- Check existing issues before creating a new one.
