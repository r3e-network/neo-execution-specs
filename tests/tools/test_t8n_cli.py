"""Tests for neo-t8n CLI strict/permissive behavior."""

from __future__ import annotations

import json
from pathlib import Path

from neo.protocol_settings import ProtocolSettings
from neo.tools.t8n.cli import main
from neo.vm.opcode import OpCode
from neo.vm.script_builder import ScriptBuilder


def _write_json(path: Path, payload: object) -> None:
    path.write_text(json.dumps(payload), encoding="utf-8")


def _push_int_script_hex(value: int) -> str:
    sb = ScriptBuilder()
    sb.emit_push(value)
    return sb.to_bytes().hex()


def test_t8n_cli_permissive_mode_continues_after_invalid_tx(tmp_path: Path) -> None:
    alloc_path = tmp_path / "alloc.json"
    env_path = tmp_path / "env.json"
    txs_path = tmp_path / "txs.json"
    result_path = tmp_path / "result.json"
    alloc_out_path = tmp_path / "alloc-out.json"

    _write_json(alloc_path, {})
    _write_json(env_path, {"currentBlockNumber": 1})
    _write_json(
        txs_path,
        [
            {"script": "not-hex", "signers": []},
            {"script": _push_int_script_hex(5), "signers": []},
        ],
    )

    exit_code = main(
        [
            "--input-alloc",
            str(alloc_path),
            "--input-env",
            str(env_path),
            "--input-txs",
            str(txs_path),
            "--output-result",
            str(result_path),
            "--output-alloc",
            str(alloc_out_path),
        ]
    )

    assert exit_code == 0

    result = json.loads(result_path.read_text(encoding="utf-8"))
    receipts = result["receipts"]
    assert len(receipts) == 2
    assert receipts[0]["vmState"] == "FAULT"
    assert receipts[1]["vmState"] == "HALT"


def test_t8n_cli_strict_mode_fails_fast_on_invalid_tx(tmp_path: Path) -> None:
    alloc_path = tmp_path / "alloc.json"
    env_path = tmp_path / "env.json"
    txs_path = tmp_path / "txs.json"
    result_path = tmp_path / "result.json"
    alloc_out_path = tmp_path / "alloc-out.json"

    _write_json(alloc_path, {})
    _write_json(env_path, {"currentBlockNumber": 1})
    _write_json(
        txs_path,
        [
            {"script": "not-hex", "signers": []},
            {"script": _push_int_script_hex(5), "signers": []},
        ],
    )

    exit_code = main(
        [
            "--input-alloc",
            str(alloc_path),
            "--input-env",
            str(env_path),
            "--input-txs",
            str(txs_path),
            "--output-result",
            str(result_path),
            "--output-alloc",
            str(alloc_out_path),
            "--strict",
        ]
    )

    assert exit_code == 1


def test_t8n_cli_permissive_mode_continues_after_malformed_witness_rule(
    tmp_path: Path,
) -> None:
    alloc_path = tmp_path / "alloc.json"
    env_path = tmp_path / "env.json"
    txs_path = tmp_path / "txs.json"
    result_path = tmp_path / "result.json"
    alloc_out_path = tmp_path / "alloc-out.json"

    _write_json(alloc_path, {})
    _write_json(env_path, {"currentBlockNumber": 1})
    _write_json(
        txs_path,
        [
            {
                "script": _push_int_script_hex(1),
                "signers": [{"account": "11" * 20, "scopes": 0x40, "rules": [{"action": 1}]}],
            },
            {"script": _push_int_script_hex(5), "signers": []},
        ],
    )

    exit_code = main(
        [
            "--input-alloc",
            str(alloc_path),
            "--input-env",
            str(env_path),
            "--input-txs",
            str(txs_path),
            "--output-result",
            str(result_path),
            "--output-alloc",
            str(alloc_out_path),
        ]
    )

    assert exit_code == 0

    result = json.loads(result_path.read_text(encoding="utf-8"))
    receipts = result["receipts"]
    assert len(receipts) == 2
    assert receipts[0]["vmState"] == "FAULT"
    assert receipts[1]["vmState"] == "HALT"


def test_t8n_cli_strict_mode_fails_fast_on_malformed_witness_rule(
    tmp_path: Path,
) -> None:
    alloc_path = tmp_path / "alloc.json"
    env_path = tmp_path / "env.json"
    txs_path = tmp_path / "txs.json"
    result_path = tmp_path / "result.json"
    alloc_out_path = tmp_path / "alloc-out.json"

    _write_json(alloc_path, {})
    _write_json(env_path, {"currentBlockNumber": 1})
    _write_json(
        txs_path,
        [
            {
                "script": _push_int_script_hex(1),
                "signers": [{"account": "11" * 20, "scopes": 0x40, "rules": [{"action": 1}]}],
            },
            {"script": _push_int_script_hex(5), "signers": []},
        ],
    )

    exit_code = main(
        [
            "--input-alloc",
            str(alloc_path),
            "--input-env",
            str(env_path),
            "--input-txs",
            str(txs_path),
            "--output-result",
            str(result_path),
            "--output-alloc",
            str(alloc_out_path),
            "--strict",
        ]
    )

    assert exit_code == 1


def test_t8n_cli_permissive_mode_faults_on_tx_count_overflow(tmp_path: Path) -> None:
    alloc_path = tmp_path / "alloc.json"
    env_path = tmp_path / "env.json"
    txs_path = tmp_path / "txs.json"
    result_path = tmp_path / "result.json"
    alloc_out_path = tmp_path / "alloc-out.json"

    _write_json(alloc_path, {})
    _write_json(env_path, {"currentBlockNumber": 1})
    _write_json(
        txs_path,
        [{"script": _push_int_script_hex(1), "signers": []} for _ in range(513)],
    )

    exit_code = main(
        [
            "--input-alloc",
            str(alloc_path),
            "--input-env",
            str(env_path),
            "--input-txs",
            str(txs_path),
            "--output-result",
            str(result_path),
            "--output-alloc",
            str(alloc_out_path),
        ]
    )

    assert exit_code == 0

    result = json.loads(result_path.read_text(encoding="utf-8"))
    receipts = result["receipts"]
    assert len(receipts) == 513
    assert all(r["vmState"] == "FAULT" for r in receipts)
    assert "max transactions per block" in (receipts[0].get("exception", "")).lower()


def test_t8n_cli_strict_mode_fails_fast_on_tx_count_overflow(tmp_path: Path) -> None:
    alloc_path = tmp_path / "alloc.json"
    env_path = tmp_path / "env.json"
    txs_path = tmp_path / "txs.json"
    result_path = tmp_path / "result.json"
    alloc_out_path = tmp_path / "alloc-out.json"

    _write_json(alloc_path, {})
    _write_json(env_path, {"currentBlockNumber": 1})
    _write_json(
        txs_path,
        [{"script": _push_int_script_hex(1), "signers": []} for _ in range(513)],
    )

    exit_code = main(
        [
            "--input-alloc",
            str(alloc_path),
            "--input-env",
            str(env_path),
            "--input-txs",
            str(txs_path),
            "--output-result",
            str(result_path),
            "--output-alloc",
            str(alloc_out_path),
            "--strict",
        ]
    )

    assert exit_code == 1


def test_t8n_cli_permissive_mode_continues_after_missing_script_field(
    tmp_path: Path,
) -> None:
    alloc_path = tmp_path / "alloc.json"
    env_path = tmp_path / "env.json"
    txs_path = tmp_path / "txs.json"
    result_path = tmp_path / "result.json"
    alloc_out_path = tmp_path / "alloc-out.json"

    _write_json(alloc_path, {})
    _write_json(env_path, {"currentBlockNumber": 1})
    _write_json(
        txs_path,
        [
            {"signers": []},
            {"script": _push_int_script_hex(5), "signers": []},
        ],
    )

    exit_code = main(
        [
            "--input-alloc",
            str(alloc_path),
            "--input-env",
            str(env_path),
            "--input-txs",
            str(txs_path),
            "--output-result",
            str(result_path),
            "--output-alloc",
            str(alloc_out_path),
        ]
    )

    assert exit_code == 0

    result = json.loads(result_path.read_text(encoding="utf-8"))
    receipts = result["receipts"]
    assert len(receipts) == 2
    assert receipts[0]["vmState"] == "FAULT"
    assert receipts[1]["vmState"] == "HALT"


def test_t8n_cli_permissive_mode_continues_after_non_numeric_system_fee(
    tmp_path: Path,
) -> None:
    alloc_path = tmp_path / "alloc.json"
    env_path = tmp_path / "env.json"
    txs_path = tmp_path / "txs.json"
    result_path = tmp_path / "result.json"
    alloc_out_path = tmp_path / "alloc-out.json"

    _write_json(alloc_path, {})
    _write_json(env_path, {"currentBlockNumber": 1})
    _write_json(
        txs_path,
        [
            {"script": _push_int_script_hex(1), "systemFee": "not-a-number", "signers": []},
            {"script": _push_int_script_hex(5), "signers": []},
        ],
    )

    exit_code = main(
        [
            "--input-alloc",
            str(alloc_path),
            "--input-env",
            str(env_path),
            "--input-txs",
            str(txs_path),
            "--output-result",
            str(result_path),
            "--output-alloc",
            str(alloc_out_path),
        ]
    )

    assert exit_code == 0

    result = json.loads(result_path.read_text(encoding="utf-8"))
    receipts = result["receipts"]
    assert len(receipts) == 2
    assert receipts[0]["vmState"] == "FAULT"
    assert receipts[1]["vmState"] == "HALT"


def test_t8n_cli_testnet_profile_allows_513_transactions(tmp_path: Path) -> None:
    alloc_path = tmp_path / "alloc.json"
    env_path = tmp_path / "env.json"
    txs_path = tmp_path / "txs.json"
    result_path = tmp_path / "result.json"
    alloc_out_path = tmp_path / "alloc-out.json"

    _write_json(alloc_path, {})
    _write_json(
        env_path,
        {"currentBlockNumber": 1, "network": ProtocolSettings.testnet().network},
    )
    _write_json(
        txs_path,
        [{"script": "not-hex", "signers": []} for _ in range(513)],
    )

    exit_code = main(
        [
            "--input-alloc",
            str(alloc_path),
            "--input-env",
            str(env_path),
            "--input-txs",
            str(txs_path),
            "--output-result",
            str(result_path),
            "--output-alloc",
            str(alloc_out_path),
        ]
    )

    assert exit_code == 0

    result = json.loads(result_path.read_text(encoding="utf-8"))
    receipts = result["receipts"]
    assert len(receipts) == 513
    assert all(r["vmState"] == "FAULT" for r in receipts)
    assert "max transactions per block" not in (receipts[0].get("exception", "")).lower()


def test_t8n_cli_permissive_mode_continues_after_non_object_tx_entry(
    tmp_path: Path,
) -> None:
    alloc_path = tmp_path / "alloc.json"
    env_path = tmp_path / "env.json"
    txs_path = tmp_path / "txs.json"
    result_path = tmp_path / "result.json"
    alloc_out_path = tmp_path / "alloc-out.json"

    _write_json(alloc_path, {})
    _write_json(env_path, {"currentBlockNumber": 1})
    _write_json(
        txs_path,
        [
            123,
            {"script": _push_int_script_hex(5), "signers": []},
        ],
    )

    exit_code = main(
        [
            "--input-alloc",
            str(alloc_path),
            "--input-env",
            str(env_path),
            "--input-txs",
            str(txs_path),
            "--output-result",
            str(result_path),
            "--output-alloc",
            str(alloc_out_path),
        ]
    )

    assert exit_code == 0

    result = json.loads(result_path.read_text(encoding="utf-8"))
    receipts = result["receipts"]
    assert len(receipts) == 2
    assert receipts[0]["vmState"] == "FAULT"
    assert receipts[1]["vmState"] == "HALT"


def test_t8n_cli_strict_mode_fails_fast_on_non_object_tx_entry(
    tmp_path: Path,
) -> None:
    alloc_path = tmp_path / "alloc.json"
    env_path = tmp_path / "env.json"
    txs_path = tmp_path / "txs.json"
    result_path = tmp_path / "result.json"
    alloc_out_path = tmp_path / "alloc-out.json"

    _write_json(alloc_path, {})
    _write_json(env_path, {"currentBlockNumber": 1})
    _write_json(
        txs_path,
        [
            123,
            {"script": _push_int_script_hex(5), "signers": []},
        ],
    )

    exit_code = main(
        [
            "--input-alloc",
            str(alloc_path),
            "--input-env",
            str(env_path),
            "--input-txs",
            str(txs_path),
            "--output-result",
            str(result_path),
            "--output-alloc",
            str(alloc_out_path),
            "--strict",
        ]
    )

    assert exit_code == 1


def test_t8n_cli_permissive_mode_faults_when_tx_envelope_exceeds_size_limit(
    tmp_path: Path,
) -> None:
    alloc_path = tmp_path / "alloc.json"
    env_path = tmp_path / "env.json"
    txs_path = tmp_path / "txs.json"
    result_path = tmp_path / "result.json"
    alloc_out_path = tmp_path / "alloc-out.json"

    _write_json(alloc_path, {})
    _write_json(env_path, {"currentBlockNumber": 1})
    _write_json(
        txs_path,
        [{"script": (f"{int(OpCode.NOP):02x}") * 102400, "signers": []}],
    )

    exit_code = main(
        [
            "--input-alloc",
            str(alloc_path),
            "--input-env",
            str(env_path),
            "--input-txs",
            str(txs_path),
            "--output-result",
            str(result_path),
            "--output-alloc",
            str(alloc_out_path),
        ]
    )

    assert exit_code == 0

    result = json.loads(result_path.read_text(encoding="utf-8"))
    receipts = result["receipts"]
    assert len(receipts) == 1
    assert receipts[0]["vmState"] == "FAULT"
    assert "transaction size" in (receipts[0].get("exception", "")).lower()


def test_t8n_cli_allows_exact_tx_size_boundary_without_signers(
    tmp_path: Path,
) -> None:
    alloc_path = tmp_path / "alloc.json"
    env_path = tmp_path / "env.json"
    txs_path = tmp_path / "txs.json"
    result_path = tmp_path / "result.json"
    alloc_out_path = tmp_path / "alloc-out.json"

    _write_json(alloc_path, {})
    _write_json(env_path, {"currentBlockNumber": 1})
    _write_json(
        txs_path,
        [{"script": (f"{int(OpCode.NOP):02x}") * (102400 - 32), "signers": []}],
    )

    exit_code = main(
        [
            "--input-alloc",
            str(alloc_path),
            "--input-env",
            str(env_path),
            "--input-txs",
            str(txs_path),
            "--output-result",
            str(result_path),
            "--output-alloc",
            str(alloc_out_path),
        ]
    )

    assert exit_code == 0

    result = json.loads(result_path.read_text(encoding="utf-8"))
    receipts = result["receipts"]
    assert len(receipts) == 1
    assert receipts[0]["vmState"] == "HALT"


def test_t8n_cli_allows_exact_tx_size_boundary_with_one_signer(
    tmp_path: Path,
) -> None:
    alloc_path = tmp_path / "alloc.json"
    env_path = tmp_path / "env.json"
    txs_path = tmp_path / "txs.json"
    result_path = tmp_path / "result.json"
    alloc_out_path = tmp_path / "alloc-out.json"

    _write_json(alloc_path, {})
    _write_json(env_path, {"currentBlockNumber": 1})
    _write_json(
        txs_path,
        [
            {
                "script": (f"{int(OpCode.NOP):02x}") * (102400 - (32 + 21)),
                "signers": [{"account": "11" * 20, "scopes": 0x01}],
            }
        ],
    )

    exit_code = main(
        [
            "--input-alloc",
            str(alloc_path),
            "--input-env",
            str(env_path),
            "--input-txs",
            str(txs_path),
            "--output-result",
            str(result_path),
            "--output-alloc",
            str(alloc_out_path),
        ]
    )

    assert exit_code == 0

    result = json.loads(result_path.read_text(encoding="utf-8"))
    receipts = result["receipts"]
    assert len(receipts) == 1
    assert receipts[0]["vmState"] == "HALT"


def test_t8n_cli_allows_exact_tx_size_boundary_with_max_scoped_signer_payload(
    tmp_path: Path,
) -> None:
    alloc_path = tmp_path / "alloc.json"
    env_path = tmp_path / "env.json"
    txs_path = tmp_path / "txs.json"
    result_path = tmp_path / "result.json"
    alloc_out_path = tmp_path / "alloc-out.json"

    allowed_contracts = [f"{i + 1:040x}" for i in range(16)]
    allowed_groups = [f"02{i + 1:064x}" for i in range(16)]
    rules = [
        {"action": 1, "condition": {"type": 0x00, "expression": True}}
        for _ in range(16)
    ]
    signer_size = 21 + (1 + 20 * 16) + (1 + 33 * 16) + (1 + 3 * 16)
    script_len = 102400 - (32 + signer_size)

    _write_json(alloc_path, {})
    _write_json(env_path, {"currentBlockNumber": 1})
    _write_json(
        txs_path,
        [
            {
                "script": (f"{int(OpCode.NOP):02x}") * script_len,
                "signers": [
                    {
                        "account": "11" * 20,
                        "scopes": 0x71,
                        "allowedContracts": allowed_contracts,
                        "allowedGroups": allowed_groups,
                        "rules": rules,
                    }
                ],
            }
        ],
    )

    exit_code = main(
        [
            "--input-alloc",
            str(alloc_path),
            "--input-env",
            str(env_path),
            "--input-txs",
            str(txs_path),
            "--output-result",
            str(result_path),
            "--output-alloc",
            str(alloc_out_path),
        ]
    )

    assert exit_code == 0

    result = json.loads(result_path.read_text(encoding="utf-8"))
    receipts = result["receipts"]
    assert len(receipts) == 1
    assert receipts[0]["vmState"] == "HALT"


def test_t8n_cli_faults_one_byte_over_tx_size_boundary_with_max_scoped_signer_payload(
    tmp_path: Path,
) -> None:
    alloc_path = tmp_path / "alloc.json"
    env_path = tmp_path / "env.json"
    txs_path = tmp_path / "txs.json"
    result_path = tmp_path / "result.json"
    alloc_out_path = tmp_path / "alloc-out.json"

    allowed_contracts = [f"{i + 1:040x}" for i in range(16)]
    allowed_groups = [f"02{i + 1:064x}" for i in range(16)]
    rules = [
        {"action": 1, "condition": {"type": 0x00, "expression": True}}
        for _ in range(16)
    ]
    signer_size = 21 + (1 + 20 * 16) + (1 + 33 * 16) + (1 + 3 * 16)
    script_len = 102400 - (32 + signer_size) + 1

    _write_json(alloc_path, {})
    _write_json(env_path, {"currentBlockNumber": 1})
    _write_json(
        txs_path,
        [
            {
                "script": (f"{int(OpCode.NOP):02x}") * script_len,
                "signers": [
                    {
                        "account": "11" * 20,
                        "scopes": 0x71,
                        "allowedContracts": allowed_contracts,
                        "allowedGroups": allowed_groups,
                        "rules": rules,
                    }
                ],
            }
        ],
    )

    exit_code = main(
        [
            "--input-alloc",
            str(alloc_path),
            "--input-env",
            str(env_path),
            "--input-txs",
            str(txs_path),
            "--output-result",
            str(result_path),
            "--output-alloc",
            str(alloc_out_path),
        ]
    )

    assert exit_code == 0

    result = json.loads(result_path.read_text(encoding="utf-8"))
    receipts = result["receipts"]
    assert len(receipts) == 1
    assert receipts[0]["vmState"] == "FAULT"
    assert "transaction size" in (receipts[0].get("exception", "")).lower()


def test_t8n_cli_tx_hash_is_canonical_for_hex_numeric_fields(tmp_path: Path) -> None:
    alloc_path = tmp_path / "alloc.json"
    env_path = tmp_path / "env.json"
    txs_hex_path = tmp_path / "txs-hex.json"
    txs_int_path = tmp_path / "txs-int.json"
    result_hex_path = tmp_path / "result-hex.json"
    result_int_path = tmp_path / "result-int.json"
    alloc_out_path = tmp_path / "alloc-out.json"

    _write_json(alloc_path, {})
    _write_json(env_path, {"currentBlockNumber": 100})
    _write_json(
        txs_hex_path,
        [
            {
                "script": _push_int_script_hex(1),
                "systemFee": "0x1",
                "networkFee": "0x2",
                "nonce": "0x3",
                "validUntilBlock": "0x65",
                "signers": [],
            }
        ],
    )
    _write_json(
        txs_int_path,
        [
            {
                "script": _push_int_script_hex(1),
                "systemFee": 1,
                "networkFee": 2,
                "nonce": 3,
                "validUntilBlock": 101,
                "signers": [],
            }
        ],
    )

    exit_hex = main(
        [
            "--input-alloc",
            str(alloc_path),
            "--input-env",
            str(env_path),
            "--input-txs",
            str(txs_hex_path),
            "--output-result",
            str(result_hex_path),
            "--output-alloc",
            str(alloc_out_path),
        ]
    )
    exit_int = main(
        [
            "--input-alloc",
            str(alloc_path),
            "--input-env",
            str(env_path),
            "--input-txs",
            str(txs_int_path),
            "--output-result",
            str(result_int_path),
            "--output-alloc",
            str(alloc_out_path),
        ]
    )

    assert exit_hex == 0
    assert exit_int == 0

    result_hex = json.loads(result_hex_path.read_text(encoding="utf-8"))
    result_int = json.loads(result_int_path.read_text(encoding="utf-8"))
    assert result_hex["receipts"][0]["vmState"] == "HALT"
    assert result_int["receipts"][0]["vmState"] == "HALT"
    assert result_hex["receipts"][0]["txHash"] == result_int["receipts"][0]["txHash"]
