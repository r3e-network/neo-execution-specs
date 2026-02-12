"""Neo N3 Account State."""

from dataclasses import dataclass


@dataclass
class AccountState:
    """NEO account state."""

    balance: int = 0
    balance_height: int = 0
    vote_to: bytes | None = None
