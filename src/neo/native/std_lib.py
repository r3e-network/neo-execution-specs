"""StdLib native contract - Standard library functions."""

from __future__ import annotations

import base64
import json
from typing import Any

import regex  # type: ignore[import-untyped]

from neo.hardfork import Hardfork
from neo.native.native_contract import CallFlags, NativeContract

# Base58 alphabet
BASE58_ALPHABET = b"123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
MAX_INPUT_LENGTH = 1024

class StdLib(NativeContract):
    """Standard library functions for Neo smart contracts."""

    def __init__(self) -> None:
        super().__init__()

    @property
    def name(self) -> str:
        return "StdLib"

    def _register_methods(self) -> None:
        """Register StdLib methods."""
        super()._register_methods()
        self._register_method(
            "serialize", self.serialize, cpu_fee=1 << 12, call_flags=CallFlags.NONE
        )
        self._register_method(
            "deserialize", self.deserialize, cpu_fee=1 << 14, call_flags=CallFlags.NONE
        )
        self._register_method(
            "jsonSerialize", self.json_serialize, cpu_fee=1 << 12, call_flags=CallFlags.NONE
        )
        self._register_method(
            "jsonDeserialize",
            self.json_deserialize,
            cpu_fee=1 << 14,
            call_flags=CallFlags.NONE,
            manifest_parameter_names=["json"],
        )
        self._register_method("itoa", self.itoa_base10, cpu_fee=1 << 12, call_flags=CallFlags.NONE)
        self._register_method("itoa", self.itoa, cpu_fee=1 << 12, call_flags=CallFlags.NONE)
        self._register_method("atoi", self.atoi_base10, cpu_fee=1 << 6, call_flags=CallFlags.NONE)
        self._register_method("atoi", self.atoi, cpu_fee=1 << 6, call_flags=CallFlags.NONE)
        self._register_method(
            "base64Encode", self.base64_encode, cpu_fee=1 << 5, call_flags=CallFlags.NONE
        )
        self._register_method(
            "base64Decode", self.base64_decode, cpu_fee=1 << 5, call_flags=CallFlags.NONE
        )
        self._register_method(
            "base58Encode", self.base58_encode, cpu_fee=1 << 13, call_flags=CallFlags.NONE
        )
        self._register_method(
            "base58Decode", self.base58_decode, cpu_fee=1 << 10, call_flags=CallFlags.NONE
        )
        self._register_method(
            "base58CheckEncode",
            self.base58_check_encode,
            cpu_fee=1 << 16,
            call_flags=CallFlags.NONE,
        )
        self._register_method(
            "base58CheckDecode",
            self.base58_check_decode,
            cpu_fee=1 << 16,
            call_flags=CallFlags.NONE,
        )
        self._register_method(
            "memoryCompare", self.memory_compare, cpu_fee=1 << 5, call_flags=CallFlags.NONE
        )
        self._register_method(
            "memorySearch", self.memory_search_from_start, cpu_fee=1 << 6, call_flags=CallFlags.NONE
        )
        self._register_method(
            "memorySearch", self.memory_search_with_start, cpu_fee=1 << 6, call_flags=CallFlags.NONE
        )
        self._register_method(
            "memorySearch", self.memory_search, cpu_fee=1 << 6, call_flags=CallFlags.NONE
        )
        self._register_method(
            "stringSplit",
            self.string_split_keep_empty,
            cpu_fee=1 << 8,
            call_flags=CallFlags.NONE,
            manifest_parameter_names=["str", "separator"],
        )
        self._register_method(
            "stringSplit",
            self.string_split,
            cpu_fee=1 << 8,
            call_flags=CallFlags.NONE,
            manifest_parameter_names=["str", "separator", "removeEmptyEntries"],
        )
        self._register_method(
            "strLen",
            self.str_len,
            cpu_fee=1 << 8,
            call_flags=CallFlags.NONE,
            manifest_parameter_names=["str"],
        )
        # Hardfork HF_Echidna methods
        self._register_method(
            "base64UrlEncode",
            self.base64_url_encode,
            cpu_fee=1 << 5,
            call_flags=CallFlags.NONE,
            active_in=Hardfork.HF_ECHIDNA,
        )
        self._register_method(
            "base64UrlDecode",
            self.base64_url_decode,
            cpu_fee=1 << 5,
            call_flags=CallFlags.NONE,
            active_in=Hardfork.HF_ECHIDNA,
        )
        # Hardfork HF_Faun methods
        self._register_method(
            "hexEncode",
            self.hex_encode,
            cpu_fee=1 << 5,
            call_flags=CallFlags.NONE,
            active_in=Hardfork.HF_FAUN,
            manifest_parameter_names=["bytes"],
        )
        self._register_method(
            "hexDecode",
            self.hex_decode,
            cpu_fee=1 << 5,
            call_flags=CallFlags.NONE,
            active_in=Hardfork.HF_FAUN,
            manifest_parameter_names=["str"],
        )

    def serialize(self, item: Any) -> bytes:
        """Serialize a stack item to bytes using Neo binary format."""
        return self._binary_serialize(item)

    def deserialize(self, data: bytes) -> Any:
        """Deserialize bytes to a stack item using Neo binary format."""
        return self._binary_deserialize(data)

    def _binary_serialize(self, item: Any, depth: int = 0) -> bytes:
        """Serialize item to Neo binary format."""
        if depth > 16:
            raise ValueError("Serialization depth exceeded")

        if item is None:
            return bytes([0x00])  # Null
        elif isinstance(item, bool):
            # StackItemType.Boolean = 0x20, followed by value byte
            return bytes([0x20, 0x01 if item else 0x00])
        elif isinstance(item, int):
            # Integer
            if item == 0:
                return bytes([0x21, 0x00])
            data = item.to_bytes((item.bit_length() + 8) // 8, "little", signed=True)
            return bytes([0x21, len(data)]) + data
        elif isinstance(item, bytes):
            # ByteString
            length = len(item)
            if length < 0x100:
                return bytes([0x28, length]) + item
            elif length < 0x10000:
                return bytes([0x29]) + length.to_bytes(2, "little") + item
            else:
                return bytes([0x2A]) + length.to_bytes(4, "little") + item
        elif isinstance(item, str):
            # String as ByteString
            encoded = item.encode("utf-8")
            return self._binary_serialize(encoded, depth)
        elif isinstance(item, list):
            # Array
            result = bytes([0x40, len(item)])
            for elem in item:
                result += self._binary_serialize(elem, depth + 1)
            return result
        elif isinstance(item, dict):
            # Map
            result = bytes([0x48, len(item)])
            for k, v in item.items():
                result += self._binary_serialize(k, depth + 1)
                result += self._binary_serialize(v, depth + 1)
            return result
        else:
            raise ValueError(f"Cannot serialize type: {type(item)}")

    def _binary_deserialize(self, data: bytes, offset: int = 0) -> tuple:
        """Deserialize from Neo binary format. Returns (value, new_offset)."""
        if offset >= len(data):
            raise ValueError("Invalid data")

        type_byte = data[offset]
        offset += 1

        if type_byte == 0x00:  # Null
            return None, offset
        elif type_byte == 0x20:  # Boolean
            if offset >= len(data):
                raise ValueError("Truncated boolean value")
            value_byte = data[offset]
            offset += 1
            return value_byte != 0, offset
        elif type_byte == 0x21:  # Integer
            if offset >= len(data):
                raise ValueError("Truncated integer length")
            length = data[offset]
            offset += 1
            if length == 0:
                return 0, offset
            int_data = data[offset : offset + length]
            offset += length
            return int.from_bytes(int_data, "little", signed=True), offset
        elif type_byte == 0x28:  # ByteString (1-byte length)
            length = data[offset]
            offset += 1
            return data[offset : offset + length], offset + length
        elif type_byte == 0x29:  # ByteString (2-byte length)
            length = int.from_bytes(data[offset : offset + 2], "little")
            offset += 2
            return data[offset : offset + length], offset + length
        elif type_byte == 0x2A:  # ByteString (4-byte length)
            length = int.from_bytes(data[offset : offset + 4], "little")
            offset += 4
            return data[offset : offset + length], offset + length
        elif type_byte == 0x40:  # Array
            count = data[offset]
            offset += 1
            result = []
            for _ in range(count):
                item, offset = self._binary_deserialize(data, offset)
                result.append(item)
            return result, offset
        elif type_byte == 0x48:  # Map
            count = data[offset]
            offset += 1
            map_result: dict[Any, Any] = {}
            for _ in range(count):
                key, offset = self._binary_deserialize(data, offset)
                value, offset = self._binary_deserialize(data, offset)
                map_result[key] = value
            return map_result, offset
        else:
            raise ValueError(f"Unknown type byte: {type_byte}")

    def json_serialize(self, item: Any) -> bytes:
        """Serialize a stack item to JSON bytes."""
        return json.dumps(self._to_json_value(item)).encode("utf-8")

    def json_deserialize(self, data: bytes) -> Any:
        """Deserialize JSON bytes to a stack item."""
        return self._from_json_value(json.loads(data.decode("utf-8")))

    def _to_json_value(self, item: Any) -> Any:
        """Convert stack item to JSON-compatible value."""
        if item is None:
            return None
        elif isinstance(item, bool):
            return item
        elif isinstance(item, int):
            return item
        elif isinstance(item, bytes):
            return base64.b64encode(item).decode("ascii")
        elif isinstance(item, str):
            return item
        elif isinstance(item, list):
            return [self._to_json_value(x) for x in item]
        elif isinstance(item, dict):
            return {str(k): self._to_json_value(v) for k, v in item.items()}
        else:
            return str(item)

    def _from_json_value(self, value: Any) -> Any:
        """Convert JSON value to stack item."""
        if value is None:
            return None
        elif isinstance(value, bool):
            return value
        elif isinstance(value, int):
            return value
        elif isinstance(value, float):
            return int(value)
        elif isinstance(value, str):
            return value
        elif isinstance(value, list):
            return [self._from_json_value(x) for x in value]
        elif isinstance(value, dict):
            return {k: self._from_json_value(v) for k, v in value.items()}
        else:
            return value

    def itoa(self, value: int, base: int = 10) -> str:
        """Convert an integer to a string.

        For base 16, follows Neo/.NET BigInteger formatting semantics.
        """
        if base == 10:
            return str(value)
        elif base == 16:
            if value >= 0:
                text = format(value, "x")
                # Keep positive values positive when parsed back from hex.
                if text and text[0] in "89abcdef":
                    return f"0{text}"
                return text

            # Encode negatives using minimal 2's-complement nibble width.
            nbits = 4
            while value < -(1 << (nbits - 1)):
                nbits += 4
            twos = (1 << nbits) + value
            text = format(twos, "x")
            # Trim redundant sign-extension nibbles.
            while len(text) > 1 and text[0] == "f" and text[1] in "89abcdef":
                text = text[1:]
            return text
        else:
            raise ValueError(f"Invalid base: {base}")

    def itoa_base10(self, value: int) -> str:
        """Overload shim for itoa(value)."""
        return self.itoa(value, 10)

    def atoi(self, value: str, base: int = 10) -> int:
        """Convert a string to an integer."""
        if len(value) > MAX_INPUT_LENGTH:
            raise ValueError("Input too long")

        if base == 10:
            return int(value, 10)
        elif base == 16:
            if value.startswith(("-", "+")):
                return int(value, 16)

            normalized = value.lower().removeprefix("0x")
            if not normalized:
                return 0

            unsigned = int(normalized, 16)
            bits = len(normalized) * 4
            if normalized[0] in "89abcdef":
                return unsigned - (1 << bits)
            return unsigned
        else:
            raise ValueError(f"Invalid base: {base}")

    def atoi_base10(self, value: str) -> int:
        """Overload shim for atoi(value)."""
        return self.atoi(value, 10)

    def base64_encode(self, data: bytes) -> str:
        """Encode bytes to base64 string."""
        if len(data) > MAX_INPUT_LENGTH:
            raise ValueError("Input too long")
        return base64.b64encode(data).decode("ascii")

    def base64_decode(self, s: str) -> bytes:
        """Decode base64 string to bytes."""
        if len(s) > MAX_INPUT_LENGTH:
            raise ValueError("Input too long")
        return base64.b64decode(s)

    def base58_encode(self, data: bytes) -> str:
        """Encode bytes to base58 string."""
        if len(data) > MAX_INPUT_LENGTH:
            raise ValueError("Input too long")

        # Count leading zeros
        leading_zeros = 0
        for byte in data:
            if byte == 0:
                leading_zeros += 1
            else:
                break

        # Convert to integer
        num = int.from_bytes(data, "big")

        # Convert to base58
        result = []
        while num > 0:
            num, remainder = divmod(num, 58)
            result.append(BASE58_ALPHABET[remainder : remainder + 1])

        # Add leading '1's for leading zeros
        result.extend([b"1"] * leading_zeros)

        return b"".join(reversed(result)).decode("ascii")

    def base58_decode(self, s: str) -> bytes:
        """Decode base58 string to bytes."""
        if len(s) > MAX_INPUT_LENGTH:
            raise ValueError("Input too long")

        # Count leading '1's
        leading_ones = 0
        for char in s:
            if char == "1":
                leading_ones += 1
            else:
                break

        # Convert from base58
        num = 0
        for char in s:
            idx = BASE58_ALPHABET.find(char.encode("ascii"))
            if idx < 0:
                raise ValueError(f"Invalid base58 character: {char}")
            num = num * 58 + idx

        # Convert to bytes
        if num == 0:
            result = b""
        else:
            result = num.to_bytes((num.bit_length() + 7) // 8, "big")

        # Add leading zeros
        return b"\x00" * leading_ones + result

    def base58_check_encode(self, data: bytes) -> str:
        """Encode bytes to base58 with checksum."""
        if len(data) > MAX_INPUT_LENGTH:
            raise ValueError("Input too long")

        from neo.crypto import sha256

        checksum = sha256(sha256(data))[:4]
        return self.base58_encode(data + checksum)

    def base58_check_decode(self, s: str) -> bytes:
        """Decode base58 with checksum verification."""
        if len(s) > MAX_INPUT_LENGTH:
            raise ValueError("Input too long")

        from neo.crypto import sha256

        data = self.base58_decode(s)
        if len(data) < 4:
            raise ValueError("Invalid base58check data")

        payload = data[:-4]
        checksum = data[-4:]
        expected_checksum = sha256(sha256(payload))[:4]

        if checksum != expected_checksum:
            raise ValueError("Invalid checksum")

        return payload

    def memory_compare(self, str1: bytes, str2: bytes) -> int:
        """Compare two byte arrays."""
        if len(str1) > MAX_INPUT_LENGTH or len(str2) > MAX_INPUT_LENGTH:
            raise ValueError("Input too long")

        if str1 < str2:
            return -1
        elif str1 > str2:
            return 1
        else:
            return 0

    def memory_search(
        self, mem: bytes, value: bytes, start: int = 0, backward: bool = False
    ) -> int:
        """Search for a value in memory."""
        if len(mem) > MAX_INPUT_LENGTH:
            raise ValueError("Input too long")

        if backward and start == 0:
            start = len(mem) - 1
        if backward:
            idx = mem[: start + 1].rfind(value)
        else:
            idx = mem.find(value, start)

        return idx

    def memory_search_from_start(self, mem: bytes, value: bytes) -> int:
        """Overload shim for memorySearch(mem, value)."""
        return self.memory_search(mem, value, 0, False)

    def memory_search_with_start(self, mem: bytes, value: bytes, start: int) -> int:
        """Overload shim for memorySearch(mem, value, start)."""
        return self.memory_search(mem, value, start, False)

    def string_split(self, s: str, separator: str, remove_empty_entries: bool = False) -> list[str]:
        """Split a string by separator."""
        if len(s) > MAX_INPUT_LENGTH:
            raise ValueError("Input too long")

        parts = s.split(separator)
        if remove_empty_entries:
            parts = [p for p in parts if p]
        return parts

    def string_split_keep_empty(self, s: str, separator: str) -> list[str]:
        """Overload shim for stringSplit(s, separator)."""
        return self.string_split(s, separator, False)

    def str_len(self, s: str) -> int:
        """Get the length of a string in grapheme clusters.

        Uses Unicode grapheme cluster segmentation to match C# StringInfo.LengthInTextElements.
        """
        if len(s) > MAX_INPUT_LENGTH:
            raise ValueError("Input too long")

        # Use regex \X pattern for grapheme cluster matching
        return len(regex.findall(r"\X", s))

    @staticmethod
    def _extract_context_and_value(
        value_or_context: Any, context: Any | None = None
    ) -> tuple[Any | None, Any]:
        """Support direct calls and native-engine dispatch for unary methods."""
        if context is not None:
            return context, value_or_context
        if hasattr(value_or_context, "pop") and hasattr(value_or_context, "snapshot"):
            engine = value_or_context
            return engine, engine.pop()
        return None, value_or_context

    @staticmethod
    def _as_str(value: Any) -> str:
        if isinstance(value, str):
            return value
        if isinstance(value, bytes):
            return value.decode("utf-8")
        if hasattr(value, "get_string"):
            return value.get_string()
        if hasattr(value, "get_bytes_unsafe"):
            return value.get_bytes_unsafe().decode("utf-8")
        return str(value)

    @staticmethod
    def _as_bytes(value: Any) -> bytes:
        if isinstance(value, bytes):
            return value
        if isinstance(value, str):
            return value.encode("utf-8")
        if hasattr(value, "get_bytes_unsafe"):
            return value.get_bytes_unsafe()
        if hasattr(value, "get_string"):
            return value.get_string().encode("utf-8")
        raise TypeError(f"Unsupported byte input type: {type(value)!r}")

    def base64_url_encode(self, data: str, context: Any | None = None) -> str:
        """Encode string to base64url format.

        Base64url is URL-safe base64 encoding that replaces:
        - '+' with '-'
        - '/' with '_'
        - Removes padding '='

        Args:
            data: String to encode

        Returns:
            Base64url encoded string
        """
        context, data_value = self._extract_context_and_value(data, context)
        if context is not None:
            NativeContract.require_hardfork(context, Hardfork.HF_ECHIDNA, "base64UrlEncode")

        text = self._as_str(data_value)
        if len(text) > MAX_INPUT_LENGTH:
            raise ValueError("Input too long")

        # Encode to base64 and convert to URL-safe format
        encoded = base64.urlsafe_b64encode(text.encode("utf-8")).decode("ascii")
        # Remove padding
        return encoded.rstrip("=")

    def base64_url_decode(self, s: str, context: Any | None = None) -> str:
        """Decode base64url string.

        Args:
            s: Base64url encoded string

        Returns:
            Decoded string
        """
        context, s_value = self._extract_context_and_value(s, context)
        if context is not None:
            NativeContract.require_hardfork(context, Hardfork.HF_ECHIDNA, "base64UrlDecode")

        text = self._as_str(s_value)
        if len(text) > MAX_INPUT_LENGTH:
            raise ValueError("Input too long")

        # Add padding if needed
        padding = 4 - (len(text) % 4)
        if padding != 4:
            text += "=" * padding

        return base64.urlsafe_b64decode(text).decode("utf-8")

    def hex_encode(self, data: bytes, context: Any | None = None) -> str:
        """Encode bytes to hexadecimal string.

        Args:
            data: Bytes to encode

        Returns:
            Hexadecimal string (lowercase)
        """
        context, data_value = self._extract_context_and_value(data, context)
        if context is not None:
            NativeContract.require_hardfork(context, Hardfork.HF_FAUN, "hexEncode")

        payload = self._as_bytes(data_value)
        if len(payload) > MAX_INPUT_LENGTH:
            raise ValueError("Input too long")
        return payload.hex()

    def hex_decode(self, s: str, context: Any | None = None) -> bytes:
        """Decode hexadecimal string to bytes.

        Args:
            s: Hexadecimal string

        Returns:
            Decoded bytes
        """
        context, s_value = self._extract_context_and_value(s, context)
        if context is not None:
            NativeContract.require_hardfork(context, Hardfork.HF_FAUN, "hexDecode")

        text = self._as_str(s_value)
        if len(text) > MAX_INPUT_LENGTH:
            raise ValueError("Input too long")
        return bytes.fromhex(text)
