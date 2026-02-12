"""Release metadata consistency checks."""

from __future__ import annotations

import importlib.util
import tomllib
from pathlib import Path
from types import ModuleType


def _load_script_module(module_name: str, script_path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location(module_name, script_path)
    assert spec is not None
    assert spec.loader is not None

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _write_minimal_repo_layout(
    root: Path,
    *,
    version: str,
    init_assignment: str | None = None,
    changelog_date: str = "2026-02-12",
) -> None:
    (root / "src/neo").mkdir(parents=True)

    pyproject = (
        "[project]\n"
        'name = "neo-execution-specs"\n'
        f'version = "{version}"\n'
    )
    (root / "pyproject.toml").write_text(pyproject, encoding="utf-8")

    if init_assignment is None:
        init_assignment = f'__version__ = "{version}"\n'
    (root / "src/neo/__init__.py").write_text(init_assignment, encoding="utf-8")

    changelog = (
        "# Changelog\n\n"
        f"## [{version}] - {changelog_date}\n\n"
        "- Test entry\n"
    )
    (root / "CHANGELOG.md").write_text(changelog, encoding="utf-8")


def test_metadata_validation_passes_for_repo_state() -> None:
    module = _load_script_module(
        "check_release_metadata_pass",
        Path("scripts/check_release_metadata.py"),
    )

    pyproject = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))
    version = str(pyproject["project"]["version"])

    assert module.main(["--tag", f"v{version}"]) == 0


def test_metadata_validation_rejects_mismatched_tag() -> None:
    module = _load_script_module(
        "check_release_metadata_fail",
        Path("scripts/check_release_metadata.py"),
    )

    assert module.main(["--tag", "v999.999.999"]) == 1


def test_metadata_validation_rejects_invalid_tag_format() -> None:
    module = _load_script_module(
        "check_release_metadata_invalid",
        Path("scripts/check_release_metadata.py"),
    )

    assert module.main(["--tag", "release-0.1.1"]) == 1


def test_metadata_validation_accepts_single_quoted_init_version(tmp_path: Path) -> None:
    module = _load_script_module(
        "check_release_metadata_single_quotes",
        Path("scripts/check_release_metadata.py"),
    )

    version = "1.2.3"
    _write_minimal_repo_layout(
        tmp_path,
        version=version,
        init_assignment=f"__version__ = '{version}'\n",
    )

    assert module.validate_metadata(root=tmp_path, tag=f"v{version}") == []


def test_metadata_validation_rejects_invalid_changelog_calendar_date(tmp_path: Path) -> None:
    module = _load_script_module(
        "check_release_metadata_bad_date",
        Path("scripts/check_release_metadata.py"),
    )

    version = "1.2.3"
    _write_minimal_repo_layout(
        tmp_path,
        version=version,
        changelog_date="2026-13-40",
    )

    errors = module.validate_metadata(root=tmp_path, tag=f"v{version}")
    assert len(errors) == 1
    assert "has invalid date: 2026-13-40" in errors[0]


def test_metadata_validation_rejects_non_semver_project_version(tmp_path: Path) -> None:
    module = _load_script_module(
        "check_release_metadata_non_semver",
        Path("scripts/check_release_metadata.py"),
    )

    _write_minimal_repo_layout(tmp_path, version="1.2")

    errors = module.validate_metadata(root=tmp_path)
    assert len(errors) == 1
    assert "Invalid project version '1.2'. Expected semantic version X.Y.Z" in errors[0]
