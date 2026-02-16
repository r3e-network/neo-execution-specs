"""Treasury native contract."""

from __future__ import annotations

from typing import Any

from neo.hardfork import Hardfork
from neo.native.native_contract import CallFlags, NativeContract
from neo.types import UInt160


class Treasury(NativeContract):
    """Treasury contract surface for Neo v3.9.1."""

    @property
    def name(self) -> str:
        return "Treasury"

    def _register_methods(self) -> None:
        super()._register_methods()
        self._register_method(
            "onNEP11Payment",
            self.on_nep11_payment,
            cpu_fee=1 << 5,
            call_flags=CallFlags.NONE,
            active_in=Hardfork.HF_FAUN,
        )
        self._register_method(
            "onNEP17Payment",
            self.on_nep17_payment,
            cpu_fee=1 << 5,
            call_flags=CallFlags.NONE,
            active_in=Hardfork.HF_FAUN,
        )
        self._register_method(
            "verify",
            self.verify,
            cpu_fee=1 << 5,
            call_flags=CallFlags.READ_STATES,
            active_in=Hardfork.HF_FAUN,
        )

    def _native_supported_standards(self, context: Any) -> list[str]:
        if not self.is_hardfork_enabled(context, Hardfork.HF_FAUN):
            return []
        return ["NEP-26", "NEP-27", "NEP-30"]

    def on_nep11_payment(
        self, engine: Any, from_account: UInt160, amount: int, token_id: bytes, data: Any
    ) -> None:
        _ = (engine, from_account, amount, token_id, data)
        return None

    def on_nep17_payment(
        self, engine: Any, from_account: UInt160, amount: int, data: Any
    ) -> None:
        _ = (engine, from_account, amount, data)
        return None

    def verify(self, engine: Any | None = None) -> bool:
        checker = getattr(engine, "check_committee", None) if engine is not None else None
        if callable(checker):
            return bool(checker())
        return False
