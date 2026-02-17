"""Protocol settings for Neo N3 compatibility."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field

from neo.crypto.hash import hash160
from neo.hardfork import Hardfork
from neo.smartcontract.interop_service import get_interop_hash
from neo.types import UInt160
from neo.vm.opcode import OpCode

# Neo CLI v3.9.x mainnet defaults
_MAINNET_STANDBY_COMMITTEE_HEX: tuple[str, ...] = (
    "03b209fd4f53a7170ea4444e0cb0a6bb6a53c2bd016926989cf85f9b0fba17a70c",
    "02df48f60e8f3e01c48ff40b9b7f1310d7a8b2a193188befe1c2e3df740e895093",
    "03b8d9d5771d8f513aa0869b9cc8d50986403b78c6da36890638c3d46a5adce04a",
    "02ca0e27697b9c248f6f16e085fd0061e26f44da85b58ee835c110caa5ec3ba554",
    "024c7b7fb6c310fccf1ba33b082519d82964ea93868d676662d4a59ad548df0e7d",
    "02aaec38470f6aad0042c6e877cfd8087d2676b0f516fddd362801b9bd3936399e",
    "02486fd15702c4490a26703112a5cc1d0923fd697a33406bd5a1c00e0013b09a70",
    "023a36c72844610b4d34d1968662424011bf783ca9d984efa19a20babf5582f3fe",
    "03708b860c1de5d87f5b151a12c2a99feebd2e8b315ee8e7cf8aa19692a9e18379",
    "03c6aa6e12638b36e88adc1ccdceac4db9929575c3e03576c617c49cce7114a050",
    "03204223f8c86b8cd5c89ef12e4f0dbb314172e9241e30c9ef2293790793537cf0",
    "02a62c915cf19c7f19a50ec217e79fac2439bbaad658493de0c7d8ffa92ab0aa62",
    "03409f31f0d66bdc2f70a9730b66fe186658f84a8018204db01c106edc36553cd0",
    "0288342b141c30dc8ffcde0204929bb46aed5756b41ef4a56778d15ada8f0c6654",
    "020f2887f41474cfeb11fd262e982051c1541418137c02a0f4961af911045de639",
    "0222038884bbd1d8ff109ed3bdef3542e768eef76c1247aea8bc8171f532928c30",
    "03d281b42002647f0113f36c7b8efb30db66078dfaaa9ab3ff76d043a98d512fde",
    "02504acbc1f4b3bdad1d86d6e1a08603771db135a73e61c9d565ae06a1938cd2ad",
    "0226933336f1b75baa42d42b71d9091508b638046d19abd67f4e119bf64a7cfb4d",
    "03cdcea66032b82f5c30450e381e5295cae85c5e6943af716cc6b646352a6067dc",
    "02cd5a5547119e24feaa7c2a0f37b8c9366216bab7054de0065c9be42084003c8a",
)

_MAINNET_SEED_LIST: tuple[str, ...] = (
    "seed1.neo.org:10333",
    "seed2.neo.org:10333",
    "seed3.neo.org:10333",
    "seed4.neo.org:10333",
    "seed5.neo.org:10333",
)

_MAINNET_HARDFORKS: dict[Hardfork, int] = {
    Hardfork.HF_ASPIDOCHELONE: 1730000,
    Hardfork.HF_BASILISK: 4120000,
    Hardfork.HF_COCKATRICE: 5450000,
    Hardfork.HF_DOMOVOI: 5570000,
    Hardfork.HF_ECHIDNA: 7300000,
    Hardfork.HF_FAUN: 8800000,
}

# Neo CLI v3.9.x testnet defaults
_TESTNET_STANDBY_COMMITTEE_HEX: tuple[str, ...] = (
    "023e9b32ea89b94d066e649b124fd50e396ee91369e8e2a6ae1b11c170d022256d",
    "03009b7540e10f2562e5fd8fac9eaec25166a58b26e412348ff5a86927bfac22a2",
    "02ba2c70f5996f357a43198705859fae2cfea13e1172962800772b3d588a9d4abd",
    "03408dcd416396f64783ac587ea1e1593c57d9fea880c8a6a1920e92a259477806",
    "02a7834be9b32e2981d157cb5bbd3acb42cfd11ea5c3b10224d7a44e98c5910f1b",
    "0214baf0ceea3a66f17e7e1e839ea25fd8bed6cd82e6bb6e68250189065f44ff01",
    "030205e9cefaea5a1dfc580af20c8d5aa2468bb0148f1a5e4605fc622c80e604ba",
    "025831cee3708e87d78211bec0d1bfee9f4c85ae784762f042e7f31c0d40c329b8",
    "02cf9dc6e85d581480d91e88e8cbeaa0c153a046e89ded08b4cefd851e1d7325b5",
    "03840415b0a0fcf066bcc3dc92d8349ebd33a6ab1402ef649bae00e5d9f5840828",
    "026328aae34f149853430f526ecaa9cf9c8d78a4ea82d08bdf63dd03c4d0693be6",
    "02c69a8d084ee7319cfecf5161ff257aa2d1f53e79bf6c6f164cff5d94675c38b3",
    "0207da870cedb777fceff948641021714ec815110ca111ccc7a54c168e065bda70",
    "035056669864feea401d8c31e447fb82dd29f342a9476cfd449584ce2a6165e4d7",
    "0370c75c54445565df62cfe2e76fbec4ba00d1298867972213530cae6d418da636",
    "03957af9e77282ae3263544b7b2458903624adc3f5dee303957cb6570524a5f254",
    "03d84d22b8753cf225d263a3a782a4e16ca72ef323cfde04977c74f14873ab1e4c",
    "02147c1b1d5728e1954958daff2f88ee2fa50a06890a8a9db3fa9e972b66ae559f",
    "03c609bea5a4825908027e4ab217e7efc06e311f19ecad9d417089f14927a173d5",
    "0231edee3978d46c335e851c76059166eb8878516f459e085c0dd092f0f1d51c21",
    "03184b018d6b2bc093e535519732b3fd3f7551c8cffaf4621dd5a0b89482ca66c9",
)

_TESTNET_SEED_LIST: tuple[str, ...] = (
    "seed1t5.neo.org:20333",
    "seed2t5.neo.org:20333",
    "seed3t5.neo.org:20333",
    "seed4t5.neo.org:20333",
    "seed5t5.neo.org:20333",
)

_TESTNET_HARDFORKS: dict[Hardfork, int] = {
    Hardfork.HF_ASPIDOCHELONE: 210000,
    Hardfork.HF_BASILISK: 2680000,
    Hardfork.HF_COCKATRICE: 3967000,
    Hardfork.HF_DOMOVOI: 4144000,
    Hardfork.HF_ECHIDNA: 5870000,
    Hardfork.HF_FAUN: 12960000,
}


@dataclass
class ProtocolSettings:
    """Neo N3 protocol configuration."""

    network: int = 860833102
    address_version: int = 53
    validators_count: int = 7
    milliseconds_per_block: int = 15000
    max_valid_until_block_increment: int = 86400000 // 15000
    max_transactions_per_block: int = 512
    memory_pool_max_transactions: int = 50000
    max_traceable_blocks: int = 2102400
    initial_gas_distribution: int = 52_000_000 * 100_000_000

    hardforks: dict[Hardfork, int] = field(
        default_factory=lambda: dict(_MAINNET_HARDFORKS)
    )
    standby_committee: list[bytes] = field(
        default_factory=lambda: [bytes.fromhex(key) for key in _MAINNET_STANDBY_COMMITTEE_HEX]
    )
    seed_list: list[str] = field(default_factory=lambda: list(_MAINNET_SEED_LIST))

    # Backward-compatible attribute used by other modules.
    committee_members_count: int = 21

    def __post_init__(self) -> None:
        self.standby_committee = [
            self._normalize_pubkey(pubkey) for pubkey in self.standby_committee
        ]
        self.committee_members_count = len(self.standby_committee)

        normalized: dict[Hardfork, int] = {}
        for key, value in self.hardforks.items():
            hf = self._normalize_hardfork_key(key)
            normalized[hf] = int(value)

        normalized = self.ensure_omitted_hardforks(normalized)
        ordered = sorted(normalized.items(), key=lambda item: int(item[0]))
        self.hardforks = dict(ordered)

        self.validate_hardforks()

    @property
    def standby_validators(self) -> list[bytes]:
        """Get standby validators as the first N committee keys."""
        return list(self.standby_committee[: self.validators_count])

    @classmethod
    def mainnet(cls) -> ProtocolSettings:
        """Create Neo mainnet-compatible protocol settings."""
        return cls(
            network=860833102,
            address_version=53,
            validators_count=7,
            milliseconds_per_block=15000,
            max_valid_until_block_increment=86400000 // 15000,
            max_transactions_per_block=512,
            memory_pool_max_transactions=50000,
            max_traceable_blocks=2102400,
            initial_gas_distribution=52_000_000 * 100_000_000,
            hardforks=dict(_MAINNET_HARDFORKS),
            standby_committee=[bytes.fromhex(key) for key in _MAINNET_STANDBY_COMMITTEE_HEX],
            seed_list=list(_MAINNET_SEED_LIST),
        )

    @classmethod
    def testnet(cls) -> ProtocolSettings:
        """Create Neo testnet-compatible protocol settings."""
        return cls(
            network=894710606,
            address_version=53,
            validators_count=7,
            milliseconds_per_block=3000,
            max_valid_until_block_increment=86400000 // 15000,
            max_transactions_per_block=5000,
            memory_pool_max_transactions=50000,
            max_traceable_blocks=2102400,
            initial_gas_distribution=52_000_000 * 100_000_000,
            hardforks=dict(_TESTNET_HARDFORKS),
            standby_committee=[bytes.fromhex(key) for key in _TESTNET_STANDBY_COMMITTEE_HEX],
            seed_list=list(_TESTNET_SEED_LIST),
        )

    @staticmethod
    def _normalize_pubkey(pubkey: bytes | str) -> bytes:
        if isinstance(pubkey, bytes):
            value = pubkey
        elif isinstance(pubkey, str):
            hex_value = pubkey[2:] if pubkey.startswith("0x") else pubkey
            value = bytes.fromhex(hex_value)
        else:
            raise TypeError("Standby committee key must be bytes or hex string")

        if len(value) != 33:
            raise ValueError("Standby committee key must be a compressed 33-byte ECPoint")

        if value[0] not in (0x02, 0x03):
            raise ValueError("Standby committee key must use compressed ECPoint format")

        return value

    @staticmethod
    def _normalize_hardfork_key(key: Hardfork | str) -> Hardfork:
        if isinstance(key, Hardfork):
            return key

        name = key.strip()
        if not name:
            raise ValueError("Hardfork key cannot be empty")

        if not name.upper().startswith("HF_"):
            name = f"HF_{name}"

        normalized = name.upper()
        return Hardfork[normalized]

    @staticmethod
    def ensure_omitted_hardforks(hardforks: Mapping[Hardfork, int]) -> dict[Hardfork, int]:
        """Fill omitted *leading* hardforks with zero (matches Neo behavior)."""
        result = dict(hardforks)
        for hardfork in Hardfork:
            if hardfork not in result:
                result[hardfork] = 0
            else:
                break
        return result

    def validate_hardforks(self) -> None:
        """Validate hardfork continuity and monotonic activation heights."""
        if not self.hardforks:
            return

        ordered_keys = sorted(
            (self._normalize_hardfork_key(hf) for hf in self.hardforks.keys()),
            key=lambda hf: int(hf),
        )

        for index in range(len(ordered_keys) - 1):
            current = ordered_keys[index]
            next_hardfork = ordered_keys[index + 1]
            if int(next_hardfork) - int(current) > 1:
                raise ValueError(
                    "Hardfork configuration is not continuous. "
                    f"Gap between {current.name} and {next_hardfork.name}."
                )

        for index in range(len(ordered_keys) - 1):
            current = ordered_keys[index]
            next_hardfork = ordered_keys[index + 1]
            if self.hardforks[current] > self.hardforks[next_hardfork]:
                raise ValueError(
                    "Invalid hardfork configuration: "
                    f"{current.name} height {self.hardforks[current]} is greater than "
                    f"{next_hardfork.name} height {self.hardforks[next_hardfork]}."
                )

    def is_hardfork_enabled(self, hardfork: Hardfork, index: int) -> bool:
        """Check whether a hardfork is enabled at a given block index."""
        height = self.hardforks.get(hardfork)
        if height is None:
            return False
        return index >= height

    def get_bft_address(self) -> UInt160:
        """Compute BFT consensus address from standby validators."""
        validators = self.standby_validators
        if not validators:
            return UInt160.ZERO

        threshold = len(validators) - (len(validators) - 1) // 3
        script = self._create_multisig_redeem_script(threshold, validators)
        return UInt160(hash160(script))

    @staticmethod
    def _create_multisig_redeem_script(m: int, pubkeys: Iterable[bytes]) -> bytes:
        keys = sorted(pubkeys)
        count = len(keys)

        if not (1 <= m <= count <= 1024):
            raise ValueError(f"Invalid multisig parameters: m={m}, public_keys={count}")

        script = bytearray()
        script.extend(ProtocolSettings._emit_push_integer(m))

        for pubkey in keys:
            script.append(OpCode.PUSHDATA1)
            script.append(len(pubkey))
            script.extend(pubkey)

        script.extend(ProtocolSettings._emit_push_integer(count))
        script.append(OpCode.SYSCALL)
        script.extend(get_interop_hash("System.Crypto.CheckMultisig").to_bytes(4, "little"))

        return bytes(script)

    @staticmethod
    def _emit_push_integer(value: int) -> bytes:
        if value == -1:
            return bytes([OpCode.PUSHM1])

        if 0 <= value <= 16:
            return bytes([OpCode.PUSH0 + value])

        data = value.to_bytes((value.bit_length() + 8) // 8, "little", signed=True)

        if len(data) == 1:
            return bytes([OpCode.PUSHINT8]) + data
        if len(data) <= 2:
            return bytes([OpCode.PUSHINT16]) + data.ljust(2, b"\x00")
        if len(data) <= 4:
            return bytes([OpCode.PUSHINT32]) + data.ljust(4, b"\x00")
        if len(data) <= 8:
            return bytes([OpCode.PUSHINT64]) + data.ljust(8, b"\x00")
        if len(data) <= 16:
            return bytes([OpCode.PUSHINT128]) + data.ljust(16, b"\x00")
        if len(data) <= 32:
            return bytes([OpCode.PUSHINT256]) + data.ljust(32, b"\x00")

        raise ValueError("Integer exceeds PUSHINT256 limit")
