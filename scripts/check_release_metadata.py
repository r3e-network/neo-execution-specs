"""Validate release metadata consistency for neo-execution-specs."""

from __future__ import annotations

import argparse
import re
import tomllib
from datetime import date
from pathlib import Path

SEMVER_PATTERN = re.compile(r"^\d+\.\d+\.\d+$")
VERSION_TAG_PATTERN = re.compile(r"^v(?P<version>\d+\.\d+\.\d+)$")
VERSION_ASSIGNMENT_PATTERN = re.compile(r"__version__\s*=\s*['\"]([^'\"]+)['\"]")


def parse_tag_version(tag: str) -> str:
    """Extract and validate semantic version from a git tag."""
    match = VERSION_TAG_PATTERN.fullmatch(tag.strip())
    if not match:
        raise ValueError(f"Invalid tag format '{tag}'. Expected format: vX.Y.Z")
    return match.group("version")


def validate_semver_version(version: str, source: str) -> str | None:
    """Validate a semantic version in X.Y.Z format."""
    if SEMVER_PATTERN.fullmatch(version):
        return None
    return f"Invalid {source} version '{version}'. Expected semantic version X.Y.Z"


def read_project_version(pyproject_path: Path) -> str:
    """Read `project.version` from pyproject.toml."""
    pyproject = tomllib.loads(pyproject_path.read_text(encoding="utf-8"))
    project = pyproject.get("project")
    if not isinstance(project, dict) or "version" not in project:
        raise ValueError("Missing [project].version in pyproject.toml")
    return str(project["version"])


def read_init_version(init_path: Path) -> str:
    """Read `__version__` from src/neo/__init__.py."""
    init_text = init_path.read_text(encoding="utf-8")
    match = VERSION_ASSIGNMENT_PATTERN.search(init_text)
    if not match:
        raise ValueError(f"Could not locate __version__ assignment in {init_path}")
    return match.group(1)


def validate_changelog_heading(changelog: str, version: str) -> str | None:
    """Validate changelog heading for a version and ensure the date is a real calendar date."""
    heading_pattern = re.compile(
        rf"^## \[{re.escape(version)}\] - (?P<date>\d{{4}}-\d{{2}}-\d{{2}})$",
        re.MULTILINE,
    )
    match = heading_pattern.search(changelog)
    if match is None:
        return (
            "CHANGELOG.md missing dated heading for version "
            f"{version} (expected: '## [{version}] - YYYY-MM-DD')"
        )

    heading_date = match.group("date")
    try:
        date.fromisoformat(heading_date)
    except ValueError:
        return f"CHANGELOG.md heading for version {version} has invalid date: {heading_date}"

    return None


def validate_metadata(root: Path, tag: str | None = None) -> list[str]:
    """Return a list of metadata validation errors (empty means success)."""
    pyproject_path = root / "pyproject.toml"
    init_path = root / "src/neo/__init__.py"
    changelog_path = root / "CHANGELOG.md"

    try:
        project_version = read_project_version(pyproject_path)
    except Exception as exc:
        return [str(exc)]

    project_version_error = validate_semver_version(project_version, source="project")
    if project_version_error is not None:
        return [project_version_error]

    try:
        init_version = read_init_version(init_path)
    except Exception as exc:
        return [str(exc)]

    try:
        changelog = changelog_path.read_text(encoding="utf-8")
    except Exception as exc:
        return [str(exc)]

    expected_version = project_version
    errors: list[str] = []

    if tag is not None:
        try:
            expected_version = parse_tag_version(tag)
        except ValueError as exc:
            return [str(exc)]
        if project_version != expected_version:
            errors.append(
                f"pyproject.toml version mismatch: expected {expected_version}, got {project_version}"
            )

    if init_version != project_version:
        errors.append(
            f"src/neo/__init__.py version mismatch: expected {project_version}, got {init_version}"
        )

    changelog_error = validate_changelog_heading(changelog=changelog, version=expected_version)
    if changelog_error is not None:
        errors.append(changelog_error)

    return errors


def create_parser() -> argparse.ArgumentParser:
    """Create CLI parser for metadata validation."""
    parser = argparse.ArgumentParser(
        prog="check-release-metadata",
        description="Validate version/changelog consistency for release readiness.",
    )
    parser.add_argument(
        "--tag",
        type=str,
        default=None,
        help="Optional release tag to enforce (format: vX.Y.Z).",
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=Path("."),
        help="Repository root path (default: current directory).",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run validation and return 0 when metadata is consistent."""
    args = create_parser().parse_args(argv)
    root = args.root.resolve()

    errors = validate_metadata(root=root, tag=args.tag)
    if errors:
        for error in errors:
            print(error)
        return 1

    enforced = f" against {args.tag}" if args.tag else ""
    print(f"Release metadata validation passed{enforced}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
