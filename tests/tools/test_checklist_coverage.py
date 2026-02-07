"""Tests for Neo protocol checklist coverage enforcement."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from neo.tools.diff.checklist import NEO_V391_CHECKLIST_IDS
from neo.tools.diff.coverage import (
    compute_checklist_coverage,
    load_checklist_ids_from_markdown,
    load_coverage_manifest,
    main,
)

CHECKLIST_TEMPLATE = Path("docs/verification/neo-v3.9.1-checklist-template.md")
COVERAGE_MANIFEST = Path("tests/vectors/checklist_coverage.json")
VECTORS_ROOT = Path("tests/vectors")


def test_checklist_template_matches_python_ids() -> None:
    markdown_ids = load_checklist_ids_from_markdown(CHECKLIST_TEMPLATE)
    assert markdown_ids == set(NEO_V391_CHECKLIST_IDS)


def test_coverage_manifest_covers_all_ids() -> None:
    coverage_entries = load_coverage_manifest(COVERAGE_MANIFEST)
    assert set(coverage_entries) == set(NEO_V391_CHECKLIST_IDS)


def test_checklist_coverage_is_100_percent() -> None:
    coverage_entries = load_coverage_manifest(COVERAGE_MANIFEST)
    report = compute_checklist_coverage(
        checklist_ids=NEO_V391_CHECKLIST_IDS,
        coverage_entries=coverage_entries,
        vectors_root=VECTORS_ROOT,
    )

    assert report.total == len(NEO_V391_CHECKLIST_IDS)
    assert report.covered == report.total
    assert report.percentage == 100.0
    assert report.missing == []


def test_checklist_coverage_rejects_unknown_vector_references() -> None:
    with pytest.raises(ValueError, match="unknown vectors"):
        compute_checklist_coverage(
            checklist_ids=["vm/constants/push_variants"],
            coverage_entries={
                "vm/constants/push_variants": {
                    "vectors": ["DOES_NOT_EXIST"],
                    "evidence": [],
                }
            },
            vectors_root=VECTORS_ROOT,
        )


def test_neo_coverage_cli_passes_for_repo_state() -> None:
    exit_code = main(
        [
            "--checklist-template",
            str(CHECKLIST_TEMPLATE),
            "--coverage-manifest",
            str(COVERAGE_MANIFEST),
            "--vectors-root",
            str(VECTORS_ROOT),
        ]
    )

    assert exit_code == 0


def test_neo_coverage_cli_fails_on_template_id_drift(tmp_path: Path) -> None:
    malformed_template = tmp_path / "checklist-template.md"
    malformed_template.write_text(
        CHECKLIST_TEMPLATE.read_text(encoding="utf-8")
        + "\n| `extra/not-in-python` | Drift row. | | |\n",
        encoding="utf-8",
    )

    exit_code = main(
        [
            "--checklist-template",
            str(malformed_template),
            "--coverage-manifest",
            str(COVERAGE_MANIFEST),
            "--vectors-root",
            str(VECTORS_ROOT),
        ]
    )

    assert exit_code == 1


def test_neo_coverage_cli_fails_on_manifest_id_drift(tmp_path: Path) -> None:
    malformed_manifest = tmp_path / "checklist_coverage.json"
    coverage_entries = load_coverage_manifest(COVERAGE_MANIFEST)
    coverage_entries["extra/not-in-checklist"] = {
        "vectors": [],
        "evidence": ["intentionally injected for drift test"],
    }
    malformed_manifest.write_text(json.dumps(coverage_entries, indent=2), encoding="utf-8")

    exit_code = main(
        [
            "--checklist-template",
            str(CHECKLIST_TEMPLATE),
            "--coverage-manifest",
            str(malformed_manifest),
            "--vectors-root",
            str(VECTORS_ROOT),
        ]
    )

    assert exit_code == 1
