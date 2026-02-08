"""Checklist coverage tooling inspired by Ethereum execution-spec verification."""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path

from neo.tools.diff.checklist import NEO_V391_CHECKLIST_IDS
from neo.tools.diff.runner import VectorLoader

_CHECKLIST_ID_PATTERN = re.compile(r"\|\s*`([^`]+)`\s*\|")
_ALLOWED_CRYPTO_VECTOR_FILES = {"hash.json", "hash_extended.json", "hash_deep.json", "hash_matrix.json"}


@dataclass
class ChecklistCoverageReport:
    """Computed checklist coverage summary."""

    total: int
    covered: int
    percentage: float
    missing: list[str]


def load_checklist_ids_from_markdown(path: Path) -> set[str]:
    """Extract checklist item IDs from the markdown template."""
    text = path.read_text(encoding="utf-8")
    ids: set[str] = set()

    for match in _CHECKLIST_ID_PATTERN.finditer(text):
        candidate = match.group(1)
        if "/" in candidate:
            ids.add(candidate)

    return ids


def load_coverage_manifest(path: Path) -> dict[str, dict[str, list[str]]]:
    """Load checklist coverage mapping from JSON manifest."""
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError("Coverage manifest must be a top-level object")

    entries: dict[str, dict[str, list[str]]] = {}
    for checklist_id, entry in raw.items():
        if not isinstance(checklist_id, str):
            raise ValueError("Coverage manifest keys must be strings")
        if not isinstance(entry, dict):
            raise ValueError(f"Coverage entry for {checklist_id} must be an object")

        vectors_raw = entry.get("vectors", [])
        evidence_raw = entry.get("evidence", [])

        if not isinstance(vectors_raw, list) or not all(isinstance(v, str) for v in vectors_raw):
            raise ValueError(f"Coverage entry {checklist_id} has invalid vectors list")
        if not isinstance(evidence_raw, list) or not all(isinstance(v, str) for v in evidence_raw):
            raise ValueError(f"Coverage entry {checklist_id} has invalid evidence list")

        entries[checklist_id] = {
            "vectors": list(vectors_raw),
            "evidence": list(evidence_raw),
        }

    return entries


def _iter_supported_vector_files(vectors_root: Path) -> list[Path]:
    vector_files: list[Path] = []

    for file_path in sorted(vectors_root.glob("**/*.json")):
        relative = file_path.relative_to(vectors_root)
        if not relative.parts:
            continue

        top_level = relative.parts[0]
        if top_level in {"vm", "native", "state"}:
            vector_files.append(file_path)
            continue

        if top_level == "crypto" and file_path.name in _ALLOWED_CRYPTO_VECTOR_FILES:
            vector_files.append(file_path)

    return vector_files


def _load_vector_names(vectors_root: Path) -> set[str]:
    vector_names: set[str] = set()

    for file_path in _iter_supported_vector_files(vectors_root):
        for vector in VectorLoader.load_file(file_path):
            vector_names.add(vector.name)

    return vector_names


def compute_checklist_coverage(
    checklist_ids: tuple[str, ...] | list[str] | set[str],
    coverage_entries: dict[str, dict[str, list[str]]],
    vectors_root: Path,
) -> ChecklistCoverageReport:
    """Compute checklist coverage and validate vector references."""
    checklist_set = set(checklist_ids)
    vector_names = _load_vector_names(vectors_root)

    invalid_vectors: dict[str, list[str]] = {}
    covered = 0
    missing: list[str] = []

    for checklist_id in sorted(checklist_set):
        entry = coverage_entries.get(checklist_id, {})
        vectors = entry.get("vectors", [])
        evidence = entry.get("evidence", [])

        unknown = sorted({vector for vector in vectors if vector not in vector_names})
        if unknown:
            invalid_vectors[checklist_id] = unknown

        has_vector_coverage = any(vector in vector_names for vector in vectors)
        has_external_evidence = len(evidence) > 0

        if has_vector_coverage or has_external_evidence:
            covered += 1
        else:
            missing.append(checklist_id)

    if invalid_vectors:
        details = "\n".join(
            f"- {checklist_id}: {', '.join(vectors)}"
            for checklist_id, vectors in sorted(invalid_vectors.items())
        )
        raise ValueError(f"Coverage manifest references unknown vectors:\n{details}")

    total = len(checklist_set)
    percentage = round((covered / total) * 100, 2) if total else 0.0

    return ChecklistCoverageReport(
        total=total,
        covered=covered,
        percentage=percentage,
        missing=missing,
    )


def _print_set_diff(title: str, values: set[str]) -> None:
    if not values:
        return
    print(title)
    for value in sorted(values):
        print(f"  - {value}")


def create_parser() -> argparse.ArgumentParser:
    """Create parser for the checklist coverage CLI."""
    parser = argparse.ArgumentParser(
        prog="neo-coverage",
        description="Validate Neo protocol checklist coverage against vectors and evidence.",
    )
    parser.add_argument(
        "--checklist-template",
        type=Path,
        default=Path("docs/verification/neo-v3.9.1-checklist-template.md"),
        help="Markdown checklist template path.",
    )
    parser.add_argument(
        "--coverage-manifest",
        type=Path,
        default=Path("tests/vectors/checklist_coverage.json"),
        help="JSON checklist coverage manifest path.",
    )
    parser.add_argument(
        "--vectors-root",
        type=Path,
        default=Path("tests/vectors"),
        help="Root directory containing vector files.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run checklist coverage validation."""
    parser = create_parser()
    args = parser.parse_args(argv)

    template_ids = load_checklist_ids_from_markdown(args.checklist_template)
    python_ids = set(NEO_V391_CHECKLIST_IDS)

    template_missing = python_ids - template_ids
    template_extra = template_ids - python_ids
    if template_missing or template_extra:
        print("Checklist template and Python checklist IDs are inconsistent.", file=sys.stderr)
        _print_set_diff("Missing in template:", template_missing)
        _print_set_diff("Extra in template:", template_extra)
        return 1

    coverage_entries = load_coverage_manifest(args.coverage_manifest)
    manifest_ids = set(coverage_entries)

    manifest_missing = python_ids - manifest_ids
    manifest_extra = manifest_ids - python_ids
    if manifest_missing or manifest_extra:
        print("Coverage manifest and checklist IDs are inconsistent.", file=sys.stderr)
        _print_set_diff("Missing in manifest:", manifest_missing)
        _print_set_diff("Extra in manifest:", manifest_extra)
        return 1

    try:
        report = compute_checklist_coverage(
            checklist_ids=NEO_V391_CHECKLIST_IDS,
            coverage_entries=coverage_entries,
            vectors_root=args.vectors_root,
        )
    except ValueError as error:
        print(str(error), file=sys.stderr)
        return 1

    print("Neo checklist coverage report")
    print(f"- Total checklist items: {report.total}")
    print(f"- Covered items: {report.covered}")
    print(f"- Coverage percentage: {report.percentage:.2f}%")

    if report.missing:
        print("- Missing checklist IDs:")
        for checklist_id in report.missing:
            print(f"  - {checklist_id}")
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
