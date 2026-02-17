"""Check local native-contract surface parity against a Neo RPC endpoint."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, asdict
from pathlib import Path
from types import SimpleNamespace
from typing import Any
from urllib.error import URLError
from urllib.request import Request, urlopen

REPO_SRC = Path(__file__).resolve().parent.parent / "src"
if str(REPO_SRC) not in sys.path:
    sys.path.insert(0, str(REPO_SRC))

from neo.native import initialize_native_contracts  # noqa: E402
from neo.protocol_settings import ProtocolSettings  # noqa: E402


MAINNET_MAGIC = 860833102
TESTNET_MAGIC = 894710606


@dataclass(frozen=True)
class MethodSurface:
    name: str
    parameters: tuple[tuple[str, str], ...]
    returntype: str
    offset: int
    safe: bool


@dataclass(frozen=True)
class EventSurface:
    name: str
    parameters: tuple[tuple[str, str], ...]


@dataclass(frozen=True)
class NativeSurface:
    id: int
    hash: str
    updatecounter: int
    methods: tuple[MethodSurface, ...]
    events: tuple[EventSurface, ...]
    supportedstandards: tuple[str, ...]


@dataclass
class ComparisonReport:
    rpc_url: str
    network_magic: int | None
    block_index: int
    checked_contracts: int
    missing_local: list[str]
    missing_remote: list[str]
    id_hash_mismatch: list[dict[str, Any]]
    method_mismatch: list[dict[str, Any]]
    event_mismatch: list[dict[str, Any]]
    standards_mismatch: list[dict[str, Any]]
    updatecounter_mismatch: list[dict[str, Any]]

    @property
    def ok(self) -> bool:
        return not any(
            (
                self.missing_local,
                self.missing_remote,
                self.id_hash_mismatch,
                self.method_mismatch,
                self.event_mismatch,
                self.standards_mismatch,
                self.updatecounter_mismatch,
            )
        )


def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="check-native-surface-parity",
        description=(
            "Compare local generated native contract states against "
            "RPC getnativecontracts output."
        ),
    )
    parser.add_argument(
        "--rpc-url",
        type=str,
        default="http://seed1.neo.org:10332",
        help="RPC endpoint to query (default: mainnet seed1).",
    )
    parser.add_argument(
        "--network-profile",
        choices=("auto", "mainnet", "testnet"),
        default="auto",
        help=(
            "Protocol settings profile for local generation. "
            "'auto' infers from RPC network magic."
        ),
    )
    parser.add_argument(
        "--block-index",
        type=int,
        default=None,
        help=(
            "Block index for local hardfork context. "
            "Defaults to current RPC tip (getblockcount-1)."
        ),
    )
    parser.add_argument(
        "--rpc-timeout-seconds",
        type=float,
        default=10.0,
        help="RPC timeout in seconds (default: 10).",
    )
    parser.add_argument(
        "--json-output",
        type=Path,
        default=None,
        help="Optional path to write a JSON parity report.",
    )
    return parser


def _rpc_call(rpc_url: str, method: str, params: list[Any], timeout_seconds: float) -> Any:
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": method,
        "params": params,
    }
    request = Request(
        rpc_url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    with urlopen(request, timeout=timeout_seconds) as response:
        raw = json.loads(response.read().decode("utf-8"))
    if "error" in raw:
        raise ValueError(f"RPC error from {rpc_url}: {raw['error']}")
    return raw.get("result")


def _fetch_remote_state(rpc_url: str, timeout_seconds: float) -> tuple[int | None, int, dict[str, NativeSurface]]:
    version = _rpc_call(rpc_url, "getversion", [], timeout_seconds)
    magic: int | None = None
    if isinstance(version, dict):
        protocol = version.get("protocol")
        if isinstance(protocol, dict):
            value = protocol.get("network")
            if isinstance(value, int):
                magic = value

    block_count = _rpc_call(rpc_url, "getblockcount", [], timeout_seconds)
    if not isinstance(block_count, int):
        raise ValueError(f"Invalid getblockcount response from {rpc_url}: {block_count!r}")
    block_index = max(0, int(block_count) - 1)

    native_contracts = _rpc_call(rpc_url, "getnativecontracts", [], timeout_seconds)
    if not isinstance(native_contracts, list):
        raise ValueError(
            f"Invalid getnativecontracts response from {rpc_url}: {native_contracts!r}"
        )

    remote: dict[str, NativeSurface] = {}
    for entry in native_contracts:
        if not isinstance(entry, dict):
            continue
        manifest = entry.get("manifest")
        if not isinstance(manifest, dict):
            continue
        name = manifest.get("name")
        if not isinstance(name, str) or not name:
            continue

        remote[name] = _surface_from_manifest_entry(entry)

    return magic, block_index, remote


def _resolve_settings(profile: str, network_magic: int | None) -> ProtocolSettings:
    if profile == "mainnet":
        return ProtocolSettings.mainnet()
    if profile == "testnet":
        return ProtocolSettings.testnet()

    if network_magic == MAINNET_MAGIC:
        return ProtocolSettings.mainnet()
    if network_magic == TESTNET_MAGIC:
        return ProtocolSettings.testnet()

    raise ValueError(
        "Cannot auto-resolve network profile; pass --network-profile explicitly "
        f"(RPC network magic: {network_magic!r})."
    )


def _build_local_state(block_index: int, settings: ProtocolSettings) -> dict[str, NativeSurface]:
    contracts = initialize_native_contracts()
    contract_management = contracts["ContractManagement"]
    snapshot = SimpleNamespace(
        get=lambda _key: None,
        protocol_settings=settings,
        persisting_block=SimpleNamespace(index=block_index),
    )

    local: dict[str, NativeSurface] = {}
    for contract in contracts.values():
        state = contract_management.get_contract_state(snapshot, contract.hash)
        if state is None:
            continue
        manifest = json.loads(state.manifest.decode("utf-8"))
        name = manifest.get("name")
        if not isinstance(name, str) or not name:
            continue
        local[name] = _surface_from_local_state(state, manifest)
    return local


def _surface_from_manifest_entry(entry: dict[str, Any]) -> NativeSurface:
    manifest = entry.get("manifest", {})
    methods_raw = manifest.get("abi", {}).get("methods", [])
    events_raw = manifest.get("abi", {}).get("events", [])

    methods = tuple(_normalize_method(method) for method in methods_raw if isinstance(method, dict))
    events = tuple(_normalize_event(event) for event in events_raw if isinstance(event, dict))

    standards_raw = manifest.get("supportedstandards")
    standards = tuple(standards_raw) if isinstance(standards_raw, list) else tuple()

    contract_hash = str(entry.get("hash", "")).lower()
    contract_id = int(entry.get("id", 0))
    updatecounter = int(entry.get("updatecounter", 0))

    return NativeSurface(
        id=contract_id,
        hash=contract_hash,
        updatecounter=updatecounter,
        methods=methods,
        events=events,
        supportedstandards=standards,
    )


def _surface_from_local_state(state: Any, manifest: dict[str, Any]) -> NativeSurface:
    methods_raw = manifest.get("abi", {}).get("methods", [])
    events_raw = manifest.get("abi", {}).get("events", [])
    standards_raw = manifest.get("supportedstandards")

    methods = tuple(_normalize_method(method) for method in methods_raw if isinstance(method, dict))
    events = tuple(_normalize_event(event) for event in events_raw if isinstance(event, dict))
    standards = tuple(standards_raw) if isinstance(standards_raw, list) else tuple()

    return NativeSurface(
        id=int(state.id),
        hash=str(state.hash).lower(),
        updatecounter=int(state.update_counter),
        methods=methods,
        events=events,
        supportedstandards=standards,
    )


def _normalize_method(method: dict[str, Any]) -> MethodSurface:
    params_raw = method.get("parameters")
    parameters: tuple[tuple[str, str], ...]
    if isinstance(params_raw, list):
        parts: list[tuple[str, str]] = []
        for parameter in params_raw:
            if not isinstance(parameter, dict):
                continue
            parts.append((str(parameter.get("name", "")), str(parameter.get("type", ""))))
        parameters = tuple(parts)
    else:
        parameters = tuple()

    return MethodSurface(
        name=str(method.get("name", "")),
        parameters=parameters,
        returntype=str(method.get("returntype", "")),
        offset=int(method.get("offset", 0)),
        safe=bool(method.get("safe", False)),
    )


def _normalize_event(event: dict[str, Any]) -> EventSurface:
    params_raw = event.get("parameters")
    parameters: tuple[tuple[str, str], ...]
    if isinstance(params_raw, list):
        parts: list[tuple[str, str]] = []
        for parameter in params_raw:
            if not isinstance(parameter, dict):
                continue
            parts.append((str(parameter.get("name", "")), str(parameter.get("type", ""))))
        parameters = tuple(parts)
    else:
        parameters = tuple()

    return EventSurface(
        name=str(event.get("name", "")),
        parameters=parameters,
    )


def compare_surfaces(
    *,
    rpc_url: str,
    network_magic: int | None,
    block_index: int,
    local: dict[str, NativeSurface],
    remote: dict[str, NativeSurface],
) -> ComparisonReport:
    missing_local = sorted(name for name in remote if name not in local)
    missing_remote = sorted(name for name in local if name not in remote)

    id_hash_mismatch: list[dict[str, Any]] = []
    method_mismatch: list[dict[str, Any]] = []
    event_mismatch: list[dict[str, Any]] = []
    standards_mismatch: list[dict[str, Any]] = []
    updatecounter_mismatch: list[dict[str, Any]] = []

    for name in sorted(set(local) & set(remote)):
        local_contract = local[name]
        remote_contract = remote[name]

        if (
            local_contract.id != remote_contract.id
            or local_contract.hash != remote_contract.hash
        ):
            id_hash_mismatch.append(
                {
                    "contract": name,
                    "local": {"id": local_contract.id, "hash": local_contract.hash},
                    "remote": {"id": remote_contract.id, "hash": remote_contract.hash},
                }
            )

        if local_contract.methods != remote_contract.methods:
            method_mismatch.append(
                {
                    "contract": name,
                    "local_methods": [asdict(method) for method in local_contract.methods],
                    "remote_methods": [asdict(method) for method in remote_contract.methods],
                }
            )

        if local_contract.events != remote_contract.events:
            event_mismatch.append(
                {
                    "contract": name,
                    "local_events": [asdict(event) for event in local_contract.events],
                    "remote_events": [asdict(event) for event in remote_contract.events],
                }
            )

        if local_contract.supportedstandards != remote_contract.supportedstandards:
            standards_mismatch.append(
                {
                    "contract": name,
                    "local_standards": list(local_contract.supportedstandards),
                    "remote_standards": list(remote_contract.supportedstandards),
                }
            )

        if local_contract.updatecounter != remote_contract.updatecounter:
            updatecounter_mismatch.append(
                {
                    "contract": name,
                    "local_updatecounter": local_contract.updatecounter,
                    "remote_updatecounter": remote_contract.updatecounter,
                }
            )

    return ComparisonReport(
        rpc_url=rpc_url,
        network_magic=network_magic,
        block_index=block_index,
        checked_contracts=len(set(local) & set(remote)),
        missing_local=missing_local,
        missing_remote=missing_remote,
        id_hash_mismatch=id_hash_mismatch,
        method_mismatch=method_mismatch,
        event_mismatch=event_mismatch,
        standards_mismatch=standards_mismatch,
        updatecounter_mismatch=updatecounter_mismatch,
    )


def _print_report(report: ComparisonReport) -> None:
    print(
        f"RPC: {report.rpc_url} | network_magic={report.network_magic} | "
        f"block_index={report.block_index}"
    )
    print(f"Contracts compared: {report.checked_contracts}")
    print(f"missing_local: {len(report.missing_local)}")
    print(f"missing_remote: {len(report.missing_remote)}")
    print(f"id_hash_mismatch: {len(report.id_hash_mismatch)}")
    print(f"method_mismatch: {len(report.method_mismatch)}")
    print(f"event_mismatch: {len(report.event_mismatch)}")
    print(f"standards_mismatch: {len(report.standards_mismatch)}")
    print(f"updatecounter_mismatch: {len(report.updatecounter_mismatch)}")

    if report.ok:
        print("Native surface parity: OK")
        return

    def print_contracts(label: str, entries: list[Any]) -> None:
        if not entries:
            return
        print(f"{label}:")
        for entry in entries[:20]:
            if isinstance(entry, str):
                print(f"  - {entry}")
            elif isinstance(entry, dict):
                contract = entry.get("contract", "<unknown>")
                print(f"  - {contract}")

    print_contracts("Missing local contracts", report.missing_local)
    print_contracts("Missing remote contracts", report.missing_remote)
    print_contracts("ID/hash mismatches", report.id_hash_mismatch)
    print_contracts("Method mismatches", report.method_mismatch)
    print_contracts("Event mismatches", report.event_mismatch)
    print_contracts("Standards mismatches", report.standards_mismatch)
    print_contracts("Update-counter mismatches", report.updatecounter_mismatch)


def _write_json_report(path: Path, report: ComparisonReport) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(asdict(report), indent=2), encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    args = create_parser().parse_args(argv)

    try:
        network_magic, remote_tip_index, remote = _fetch_remote_state(
            args.rpc_url, args.rpc_timeout_seconds
        )
        settings = _resolve_settings(args.network_profile, network_magic)
        block_index = remote_tip_index if args.block_index is None else int(args.block_index)
        local = _build_local_state(block_index, settings)
        report = compare_surfaces(
            rpc_url=args.rpc_url,
            network_magic=network_magic,
            block_index=block_index,
            local=local,
            remote=remote,
        )
    except (OSError, URLError, ValueError) as exc:
        print(f"native surface parity check failed: {exc}", file=sys.stderr)
        return 2

    _print_report(report)
    if args.json_output is not None:
        _write_json_report(args.json_output, report)

    return 0 if report.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
