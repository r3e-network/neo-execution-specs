"""
Transaction - Represents a Neo N3 transaction.

Reference: Neo.Network.P2P.Payloads.Transaction
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from neo.types.uint256 import UInt256

if TYPE_CHECKING:
    from neo.io.binary_reader import BinaryReader
    from neo.io.binary_writer import BinaryWriter
    from neo.network.payloads.signer import Signer
    from neo.network.payloads.transaction_attribute import TransactionAttribute
    from neo.network.payloads.witness import Witness


MAX_TRANSACTION_SIZE = 102400
MAX_TRANSACTION_ATTRIBUTES = 16
HEADER_SIZE = 1 + 4 + 8 + 8 + 4  # Version + Nonce + SystemFee + NetworkFee + ValidUntilBlock


@dataclass
class Transaction:
    """Represents a Neo N3 transaction."""

    version: int = 0
    nonce: int = 0
    system_fee: int = 0
    network_fee: int = 0
    valid_until_block: int = 0
    signers: list["Signer"] = field(default_factory=list)
    attributes: list["TransactionAttribute"] = field(default_factory=list)
    script: bytes = b""
    witnesses: list["Witness"] = field(default_factory=list)
    _hash: UInt256 | None = field(default=None, repr=False)

    @property
    def hash(self) -> UInt256:
        """Get the transaction hash."""
        if self._hash is None:
            from neo.crypto.hash import hash256
            from neo.io.binary_writer import BinaryWriter

            writer = BinaryWriter()
            self.serialize_unsigned(writer)
            self._hash = UInt256(hash256(writer.to_bytes()))
        return self._hash

    @property
    def sender(self) -> bytes:
        """Get the sender (first signer's account)."""
        if self.signers and self.signers[0].account is not None:
            return self.signers[0].account.data
        return b"\x00" * 20

    @property
    def size(self) -> int:
        """Get the serialized size."""
        from neo.network.payloads.witness import _get_var_size

        size = HEADER_SIZE
        size += _get_var_size(len(self.signers))
        size += sum(s.size for s in self.signers)
        size += _get_var_size(len(self.attributes))
        size += sum(a.size for a in self.attributes)
        size += _get_var_size(len(self.script)) + len(self.script)
        size += _get_var_size(len(self.witnesses))
        size += sum(w.size for w in self.witnesses)
        return size

    def serialize_unsigned(self, writer: "BinaryWriter") -> None:
        """Serialize the unsigned transaction."""
        writer.write_byte(self.version)
        writer.write_uint32(self.nonce)
        writer.write_int64(self.system_fee)
        writer.write_int64(self.network_fee)
        writer.write_uint32(self.valid_until_block)
        writer.write_var_int(len(self.signers))
        for signer in self.signers:
            signer.serialize(writer)
        writer.write_var_int(len(self.attributes))
        for attr in self.attributes:
            attr.serialize(writer)
        writer.write_var_bytes(self.script)

    def serialize(self, writer: "BinaryWriter") -> None:
        """Serialize the full transaction."""
        self.serialize_unsigned(writer)
        writer.write_var_int(len(self.witnesses))
        for witness in self.witnesses:
            witness.serialize(writer)

    @classmethod
    def deserialize(cls, reader: "BinaryReader") -> "Transaction":
        """Deserialize a transaction."""
        tx = cls._deserialize_unsigned(reader)
        witness_count = reader.read_var_int(len(tx.signers))
        from neo.network.payloads.witness import Witness

        tx.witnesses = [Witness.deserialize(reader) for _ in range(witness_count)]
        if len(tx.witnesses) != len(tx.signers):
            raise ValueError("Witness count must match signer count")
        return tx

    @classmethod
    def _deserialize_unsigned(cls, reader: "BinaryReader") -> "Transaction":
        """Deserialize unsigned transaction data."""
        from neo.network.payloads.signer import Signer
        from neo.network.payloads.transaction_attribute import TransactionAttribute

        version = reader.read_byte()
        if version > 0:
            raise ValueError(f"Invalid version: {version}")

        nonce = reader.read_uint32()
        system_fee = reader.read_int64()
        if system_fee < 0:
            raise ValueError(f"Invalid system fee: {system_fee}")

        network_fee = reader.read_int64()
        if network_fee < 0:
            raise ValueError(f"Invalid network fee: {network_fee}")

        valid_until_block = reader.read_uint32()

        signer_count = reader.read_var_int(MAX_TRANSACTION_ATTRIBUTES)
        if signer_count == 0:
            raise ValueError("Signers cannot be empty")
        signers = [Signer.deserialize(reader) for _ in range(signer_count)]

        # Check for duplicate signer accounts
        seen_accounts: set[bytes] = set()
        for signer in signers:
            account = signer.account
            if account is None:
                continue
            account_key = account.data if hasattr(account, "data") else bytes(account)
            if account_key in seen_accounts:
                raise ValueError("Duplicate signer account")
            seen_accounts.add(account_key)

        attr_count = reader.read_var_int(MAX_TRANSACTION_ATTRIBUTES - signer_count)
        attributes = [TransactionAttribute.deserialize(reader) for _ in range(attr_count)]

        script = reader.read_var_bytes(0xFFFF)
        if len(script) == 0:
            raise ValueError("Script cannot be empty")

        return cls(
            version=version,
            nonce=nonce,
            system_fee=system_fee,
            network_fee=network_fee,
            valid_until_block=valid_until_block,
            signers=signers,
            attributes=attributes,
            script=script,
        )
