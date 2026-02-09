"""StdLib native contract - Standard library functions."""

from __future__ import annotations
import base64
import json
import regex
from typing import Any, List

from neo.native.native_contract import NativeContract, CallFlags


# Base58 alphabet
BASE58_ALPHABET = b'123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz'
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
        self._register_method("serialize", self.serialize,
                            cpu_fee=1 << 12, call_flags=CallFlags.NONE)
        self._register_method("deserialize", self.deserialize,
                            cpu_fee=1 << 14, call_flags=CallFlags.NONE)
        self._register_method("jsonSerialize", self.json_serialize,
                            cpu_fee=1 << 12, call_flags=CallFlags.NONE)
        self._register_method("jsonDeserialize", self.json_deserialize,
                            cpu_fee=1 << 14, call_flags=CallFlags.NONE)
        self._register_method("itoa", self.itoa,
                            cpu_fee=1 << 12, call_flags=CallFlags.NONE)
        self._register_method("atoi", self.atoi,
                            cpu_fee=1 << 6, call_flags=CallFlags.NONE)
        self._register_method("base64Encode", self.base64_encode,
                            cpu_fee=1 << 5, call_flags=CallFlags.NONE)
        self._register_method("base64Decode", self.base64_decode,
                            cpu_fee=1 << 5, call_flags=CallFlags.NONE)
        self._register_method("base58Encode", self.base58_encode,
                            cpu_fee=1 << 13, call_flags=CallFlags.NONE)
        self._register_method("base58Decode", self.base58_decode,
                            cpu_fee=1 << 10, call_flags=CallFlags.NONE)
        self._register_method("base58CheckEncode", self.base58_check_encode,
                            cpu_fee=1 << 16, call_flags=CallFlags.NONE)
        self._register_method("base58CheckDecode", self.base58_check_decode,
                            cpu_fee=1 << 16, call_flags=CallFlags.NONE)
        self._register_method("memoryCompare", self.memory_compare,
                            cpu_fee=1 << 5, call_flags=CallFlags.NONE)
        self._register_method("memorySearch", self.memory_search,
                            cpu_fee=1 << 6, call_flags=CallFlags.NONE)
        self._register_method("stringSplit", self.string_split,
                            cpu_fee=1 << 8, call_flags=CallFlags.NONE)
        self._register_method("strLen", self.str_len,
                            cpu_fee=1 << 8, call_flags=CallFlags.NONE)
        # Hardfork HF_Echidna methods
        self._register_method("base64UrlEncode", self.base64_url_encode,
                            cpu_fee=1 << 5, call_flags=CallFlags.NONE)
        self._register_method("base64UrlDecode", self.base64_url_decode,
                            cpu_fee=1 << 5, call_flags=CallFlags.NONE)
        # Hardfork HF_Faun methods
        self._register_method("hexEncode", self.hex_encode,
                            cpu_fee=1 << 5, call_flags=CallFlags.NONE)
        self._register_method("hexDecode", self.hex_decode,
                            cpu_fee=1 << 5, call_flags=CallFlags.NONE)
    
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
            data = item.to_bytes((item.bit_length() + 8) // 8, 'little', signed=True)
            return bytes([0x21, len(data)]) + data
        elif isinstance(item, bytes):
            # ByteString
            length = len(item)
            if length < 0x100:
                return bytes([0x28, length]) + item
            elif length < 0x10000:
                return bytes([0x29]) + length.to_bytes(2, 'little') + item
            else:
                return bytes([0x2A]) + length.to_bytes(4, 'little') + item
        elif isinstance(item, str):
            # String as ByteString
            encoded = item.encode('utf-8')
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
            int_data = data[offset:offset + length]
            offset += length
            return int.from_bytes(int_data, 'little', signed=True), offset
        elif type_byte == 0x28:  # ByteString (1-byte length)
            length = data[offset]
            offset += 1
            return data[offset:offset + length], offset + length
        elif type_byte == 0x29:  # ByteString (2-byte length)
            length = int.from_bytes(data[offset:offset + 2], 'little')
            offset += 2
            return data[offset:offset + length], offset + length
        elif type_byte == 0x2A:  # ByteString (4-byte length)
            length = int.from_bytes(data[offset:offset + 4], 'little')
            offset += 4
            return data[offset:offset + length], offset + length
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
            result = {}
            for _ in range(count):
                key, offset = self._binary_deserialize(data, offset)
                value, offset = self._binary_deserialize(data, offset)
                result[key] = value
            return result, offset
        else:
            raise ValueError(f"Unknown type byte: {type_byte}")
    
    def json_serialize(self, item: Any) -> bytes:
        """Serialize a stack item to JSON bytes."""
        return json.dumps(self._to_json_value(item)).encode('utf-8')
    
    def json_deserialize(self, data: bytes) -> Any:
        """Deserialize JSON bytes to a stack item."""
        return self._from_json_value(json.loads(data.decode('utf-8')))
    
    def _to_json_value(self, item: Any) -> Any:
        """Convert stack item to JSON-compatible value."""
        if item is None:
            return None
        elif isinstance(item, bool):
            return item
        elif isinstance(item, int):
            return item
        elif isinstance(item, bytes):
            return base64.b64encode(item).decode('ascii')
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
        
        For base 16 with negative numbers, uses two's complement representation
        matching C# BigInteger.ToString("X") behavior.
        """
        if base == 10:
            return str(value)
        elif base == 16:
            if value < 0:
                # Use two's complement representation, matching C# BigInteger.ToString("X")
                # Convert to bytes then to hex
                byte_len = (value.bit_length() + 8) // 8  # Include sign bit
                bytes_val = value.to_bytes(byte_len, 'big', signed=True)
                return bytes_val.hex().upper()
            else:
                return format(value, 'X')
        else:
            raise ValueError(f"Invalid base: {base}")
    
    def atoi(self, value: str, base: int = 10) -> int:
        """Convert a string to an integer."""
        if len(value) > MAX_INPUT_LENGTH:
            raise ValueError("Input too long")
        
        if base == 10:
            return int(value, 10)
        elif base == 16:
            return int(value, 16)
        else:
            raise ValueError(f"Invalid base: {base}")
    
    def base64_encode(self, data: bytes) -> str:
        """Encode bytes to base64 string."""
        if len(data) > MAX_INPUT_LENGTH:
            raise ValueError("Input too long")
        return base64.b64encode(data).decode('ascii')
    
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
        num = int.from_bytes(data, 'big')
        
        # Convert to base58
        result = []
        while num > 0:
            num, remainder = divmod(num, 58)
            result.append(BASE58_ALPHABET[remainder:remainder + 1])
        
        # Add leading '1's for leading zeros
        result.extend([b'1'] * leading_zeros)
        
        return b''.join(reversed(result)).decode('ascii')
    
    def base58_decode(self, s: str) -> bytes:
        """Decode base58 string to bytes."""
        if len(s) > MAX_INPUT_LENGTH:
            raise ValueError("Input too long")
        
        # Count leading '1's
        leading_ones = 0
        for char in s:
            if char == '1':
                leading_ones += 1
            else:
                break
        
        # Convert from base58
        num = 0
        for char in s:
            idx = BASE58_ALPHABET.find(char.encode('ascii'))
            if idx < 0:
                raise ValueError(f"Invalid base58 character: {char}")
            num = num * 58 + idx
        
        # Convert to bytes
        if num == 0:
            result = b''
        else:
            result = num.to_bytes((num.bit_length() + 7) // 8, 'big')
        
        # Add leading zeros
        return b'\x00' * leading_ones + result
    
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
    
    def memory_search(self, mem: bytes, value: bytes, start: int = 0, 
                      backward: bool = False) -> int:
        """Search for a value in memory."""
        if len(mem) > MAX_INPUT_LENGTH:
            raise ValueError("Input too long")
        
        if backward:
            idx = mem[:start].rfind(value)
        else:
            idx = mem.find(value, start)
        
        return idx
    
    def string_split(self, s: str, separator: str, 
                     remove_empty_entries: bool = False) -> List[str]:
        """Split a string by separator."""
        if len(s) > MAX_INPUT_LENGTH:
            raise ValueError("Input too long")
        
        parts = s.split(separator)
        if remove_empty_entries:
            parts = [p for p in parts if p]
        return parts
    
    def str_len(self, s: str) -> int:
        """Get the length of a string in grapheme clusters.
        
        Uses Unicode grapheme cluster segmentation to match C# StringInfo.LengthInTextElements.
        """
        if len(s) > MAX_INPUT_LENGTH:
            raise ValueError("Input too long")
        
        # Use regex \X pattern for grapheme cluster matching
        return len(regex.findall(r'\X', s))
    
    def base64_url_encode(self, data: str) -> str:
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
        if len(data) > MAX_INPUT_LENGTH:
            raise ValueError("Input too long")
        
        # Encode to base64 and convert to URL-safe format
        encoded = base64.urlsafe_b64encode(data.encode('utf-8')).decode('ascii')
        # Remove padding
        return encoded.rstrip('=')
    
    def base64_url_decode(self, s: str) -> str:
        """Decode base64url string.
        
        Args:
            s: Base64url encoded string
            
        Returns:
            Decoded string
        """
        if len(s) > MAX_INPUT_LENGTH:
            raise ValueError("Input too long")
        
        # Add padding if needed
        padding = 4 - (len(s) % 4)
        if padding != 4:
            s += '=' * padding
        
        return base64.urlsafe_b64decode(s).decode('utf-8')
    
    def hex_encode(self, data: bytes) -> str:
        """Encode bytes to hexadecimal string.
        
        Args:
            data: Bytes to encode
            
        Returns:
            Hexadecimal string (lowercase)
        """
        if len(data) > MAX_INPUT_LENGTH:
            raise ValueError("Input too long")
        return data.hex()
    
    def hex_decode(self, s: str) -> bytes:
        """Decode hexadecimal string to bytes.
        
        Args:
            s: Hexadecimal string
            
        Returns:
            Decoded bytes
        """
        if len(s) > MAX_INPUT_LENGTH:
            raise ValueError("Input too long")
        return bytes.fromhex(s)
