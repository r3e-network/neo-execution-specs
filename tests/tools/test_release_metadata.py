"""Release metadata consistency checks."""

from __future__ import annotations

import re
import tomllib
from pathlib import Path


def test_package_versions_are_consistent() -> None:
    pyproject = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))
    project_version = str(pyproject["project"]["version"])

    init_text = Path("src/neo/__init__.py").read_text(encoding="utf-8")
    match = re.search(r"__version__\s*=\s*\"([^\"]+)\"", init_text)
    assert match is not None, "__version__ must be defined in src/neo/__init__.py"

    init_version = match.group(1)
    assert init_version == project_version


def test_changelog_contains_current_version_heading() -> None:
    pyproject = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))
    project_version = str(pyproject["project"]["version"])

    changelog = Path("CHANGELOG.md").read_text(encoding="utf-8")
    heading = f"## [{project_version}]"
    assert heading in changelog
