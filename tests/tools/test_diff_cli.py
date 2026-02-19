"""Unit tests for neo-diff CLI helpers."""

from __future__ import annotations

from argparse import Namespace
from io import StringIO
from types import SimpleNamespace

from neo.tools.diff.cli import _output_report


class _Reporter:
    def __init__(self, failed: int, errors: int) -> None:
        self.report = SimpleNamespace(failed=failed, errors=errors)
        self._text_calls = 0
        self._json_calls = 0

    def write_json(self, _path) -> None:
        self._json_calls += 1

    def write_text(self, _stream) -> None:
        self._text_calls += 1


def test_output_report_returns_nonzero_when_errors_exist() -> None:
    reporter = _Reporter(failed=0, errors=1)
    args = Namespace(output=None)

    exit_code = _output_report(reporter, args)

    assert exit_code == 1
    assert reporter._text_calls == 1
    assert reporter._json_calls == 0


def test_output_report_returns_zero_when_clean() -> None:
    reporter = _Reporter(failed=0, errors=0)
    args = Namespace(output=None)

    exit_code = _output_report(reporter, args)

    assert exit_code == 0
    assert reporter._text_calls == 1
    assert reporter._json_calls == 0


def test_output_report_writes_json_when_output_path_given(tmp_path) -> None:
    reporter = _Reporter(failed=0, errors=0)
    args = Namespace(output=tmp_path / "report.json")

    stdout = StringIO()
    # _output_report prints through reporter, not stdout directly, but this call
    # ensures JSON branch is exercised.
    _ = stdout
    exit_code = _output_report(reporter, args)

    assert exit_code == 0
    assert reporter._json_calls == 1
    assert reporter._text_calls == 1
