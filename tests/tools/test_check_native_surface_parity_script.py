"""Tests for scripts/check_native_surface_parity.py."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from types import ModuleType


def _load_module(module_name: str, script_path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location(module_name, script_path)
    assert spec is not None
    assert spec.loader is not None

    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def _surface(module: ModuleType, *, updatecounter: int = 0) -> object:
    return module.NativeSurface(
        id=-1,
        hash="0x01",
        updatecounter=updatecounter,
        methods=(
            module.MethodSurface(
                name="m",
                parameters=(("x", "Integer"),),
                returntype="Boolean",
                offset=0,
                safe=True,
            ),
        ),
        events=(
            module.EventSurface(
                name="E",
                parameters=(("x", "Integer"),),
            ),
        ),
        supportedstandards=("NEP-17",),
    )


def test_compare_surfaces_reports_clean_match() -> None:
    script = Path("scripts/check_native_surface_parity.py")
    module = _load_module("check_native_surface_parity_match", script)

    local = {"ContractA": _surface(module, updatecounter=1)}
    remote = {"ContractA": _surface(module, updatecounter=1)}

    report = module.compare_surfaces(
        rpc_url="http://example",
        network_magic=860833102,
        block_index=123,
        local=local,
        remote=remote,
    )

    assert report.ok is True
    assert report.checked_contracts == 1
    assert report.missing_local == []
    assert report.missing_remote == []
    assert report.id_hash_mismatch == []
    assert report.method_mismatch == []
    assert report.event_mismatch == []
    assert report.standards_mismatch == []
    assert report.updatecounter_mismatch == []


def test_compare_surfaces_reports_mismatch_categories() -> None:
    script = Path("scripts/check_native_surface_parity.py")
    module = _load_module("check_native_surface_parity_mismatch", script)

    local = {
        "ContractA": _surface(module, updatecounter=1),
        "ContractOnlyLocal": _surface(module, updatecounter=0),
    }
    remote = {
        "ContractA": _surface(module, updatecounter=2),
        "ContractOnlyRemote": _surface(module, updatecounter=0),
    }

    report = module.compare_surfaces(
        rpc_url="http://example",
        network_magic=860833102,
        block_index=123,
        local=local,
        remote=remote,
    )

    assert report.ok is False
    assert report.missing_local == ["ContractOnlyRemote"]
    assert report.missing_remote == ["ContractOnlyLocal"]
    assert len(report.updatecounter_mismatch) == 1
    assert report.updatecounter_mismatch[0]["contract"] == "ContractA"


def test_main_writes_json_and_returns_success(tmp_path: Path, monkeypatch) -> None:
    script = Path("scripts/check_native_surface_parity.py")
    module = _load_module("check_native_surface_parity_main_ok", script)

    remote = {"ContractA": _surface(module, updatecounter=1)}
    local = {"ContractA": _surface(module, updatecounter=1)}

    def fake_fetch(rpc_url: str, timeout_seconds: float):
        assert rpc_url == "http://rpc.example:10332"
        assert timeout_seconds == 3.0
        return 860833102, 999, remote

    def fake_build(block_index: int, settings):
        assert block_index == 999
        assert settings.network == 860833102
        return local

    monkeypatch.setattr(module, "_fetch_remote_state", fake_fetch)
    monkeypatch.setattr(module, "_build_local_state", fake_build)

    report_path = tmp_path / "native-surface-report.json"
    exit_code = module.main(
        [
            "--rpc-url",
            "http://rpc.example:10332",
            "--rpc-timeout-seconds",
            "3",
            "--json-output",
            str(report_path),
        ]
    )

    assert exit_code == 0
    payload = json.loads(report_path.read_text(encoding="utf-8"))
    assert payload["checked_contracts"] == 1
    assert payload["missing_local"] == []
    assert payload["updatecounter_mismatch"] == []
