"""Tests for mypy regression baseline checking utility."""

from __future__ import annotations

import importlib.util
from pathlib import Path
from types import ModuleType


def _load_script_module(module_name: str, script_path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location(module_name, script_path)
    assert spec is not None
    assert spec.loader is not None

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_parse_mypy_error_count_parses_summary_line() -> None:
    module = _load_script_module(
        "check_mypy_regressions_parse",
        Path("scripts/check_mypy_regressions.py"),
    )

    output = "Found 350 errors in 55 files (checked 212 source files)"
    assert module.parse_mypy_error_count(output=output, returncode=1) == 350


def test_parse_mypy_error_count_returns_zero_on_success() -> None:
    module = _load_script_module(
        "check_mypy_regressions_success",
        Path("scripts/check_mypy_regressions.py"),
    )

    output = "Success: no issues found in 212 source files"
    assert module.parse_mypy_error_count(output=output, returncode=0) == 0


def test_parse_mypy_error_count_returns_none_when_unparseable() -> None:
    module = _load_script_module(
        "check_mypy_regressions_unknown",
        Path("scripts/check_mypy_regressions.py"),
    )

    assert module.parse_mypy_error_count(output="weird output", returncode=1) is None


def test_check_baseline_accepts_equal_or_lower_error_count() -> None:
    module = _load_script_module(
        "check_mypy_regressions_baseline_pass",
        Path("scripts/check_mypy_regressions.py"),
    )

    assert module.check_baseline(current_errors=349, baseline_errors=350)
    assert module.check_baseline(current_errors=350, baseline_errors=350)


def test_check_baseline_rejects_higher_error_count() -> None:
    module = _load_script_module(
        "check_mypy_regressions_baseline_fail",
        Path("scripts/check_mypy_regressions.py"),
    )

    assert not module.check_baseline(current_errors=351, baseline_errors=350)


def test_run_mypy_invokes_module_via_current_python(monkeypatch) -> None:
    import sys
    from types import SimpleNamespace

    module = _load_script_module(
        "check_mypy_regressions_run_cmd",
        Path("scripts/check_mypy_regressions.py"),
    )

    captured: dict[str, list[str]] = {}

    def fake_run(command, capture_output, text, check):  # type: ignore[no-untyped-def]
        assert capture_output is True
        assert text is True
        assert check is False
        captured["command"] = command
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    monkeypatch.setattr(module.subprocess, "run", fake_run)

    module.run_mypy(target="src/neo", ignore_missing_imports=True)

    assert captured["command"][:3] == [sys.executable, "-m", "mypy"]
