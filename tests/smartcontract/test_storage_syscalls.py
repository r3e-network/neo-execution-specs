"""Tests for storage syscalls."""

import pytest

from neo.smartcontract.syscalls import storage
from neo.smartcontract.storage.find_options import FindOptions
from neo.smartcontract.storage_context import StorageContext
from neo.types.uint160 import UInt160


class TestStorageSyscalls:
    """Storage syscall tests."""
    
    def test_storage_price_constant(self):
        """Storage price should be defined."""
        assert storage.STORAGE_PRICE == 100000
    
    def test_build_storage_key(self):
        """Build storage key from context contract ID (int32 LE) + user key."""
        script_hash = UInt160(b"\x01" * 20)
        ctx = StorageContext(id=-3, script_hash=script_hash)
        key = b"test_key"

        result = storage._build_storage_key(ctx, key)

        expected_id = (-3).to_bytes(4, byteorder="little", signed=True)
        assert result == expected_id + key
        assert len(result) == 4 + len(key)


class TestStorageContext:
    """Storage context tests."""
    
    def test_create_context(self):
        """Test storage context creation."""
        script_hash = UInt160(b"\x01" * 20)
        ctx = StorageContext(id=-1, script_hash=script_hash, is_read_only=False)

        assert ctx.script_hash == script_hash
        assert ctx.is_read_only is False
    
    def test_read_only_context(self):
        """Test read-only storage context."""
        script_hash = UInt160(b"\x01" * 20)
        ctx = StorageContext(id=-1, script_hash=script_hash, is_read_only=True)

        assert ctx.is_read_only is True


class TestStorageSizeLimits:
    """Storage.Put size-limit constants match C# ApplicationEngine.Storage.cs."""

    def test_max_key_size(self):
        assert storage.MAX_STORAGE_KEY_SIZE == 64

    def test_max_value_size(self):
        assert storage.MAX_STORAGE_VALUE_SIZE == 65535


class TestFindOptionsValidation:
    """Storage.Find option validation mirrors C# ApplicationEngine.Storage.cs:183-202."""

    def test_all_mask_value(self):
        # C# FindOptions.All = 191.
        assert int(FindOptions.ALL_MASK) == 191

    def test_valid_options_pass(self):
        for opt in (
            0,
            int(FindOptions.KEYS_ONLY),
            int(FindOptions.VALUES_ONLY),
            int(FindOptions.REMOVE_PREFIX),
            int(FindOptions.DESERIALIZE_VALUES),
            int(FindOptions.DESERIALIZE_VALUES | FindOptions.PICK_FIELD0),
            int(FindOptions.DESERIALIZE_VALUES | FindOptions.PICK_FIELD1),
            int(FindOptions.BACKWARDS),
            # A realistic full-but-consistent combination (no KeysOnly/ValuesOnly conflict).
            int(
                FindOptions.REMOVE_PREFIX
                | FindOptions.DESERIALIZE_VALUES
                | FindOptions.PICK_FIELD0
                | FindOptions.BACKWARDS
            ),
        ):
            storage._validate_find_options(opt)

    def test_out_of_range_bit_faults(self):
        # 64 is not a valid FindOptions bit.
        with pytest.raises(ValueError):
            storage._validate_find_options(64)

    def test_keys_only_with_values_only_faults(self):
        with pytest.raises(ValueError):
            storage._validate_find_options(
                int(FindOptions.KEYS_ONLY | FindOptions.VALUES_ONLY)
            )

    def test_values_only_with_remove_prefix_faults(self):
        with pytest.raises(ValueError):
            storage._validate_find_options(
                int(FindOptions.VALUES_ONLY | FindOptions.REMOVE_PREFIX)
            )

    def test_pick_field0_and_field1_faults(self):
        with pytest.raises(ValueError):
            storage._validate_find_options(
                int(
                    FindOptions.DESERIALIZE_VALUES
                    | FindOptions.PICK_FIELD0
                    | FindOptions.PICK_FIELD1
                )
            )

    def test_pick_field_without_deserialize_faults(self):
        with pytest.raises(ValueError):
            storage._validate_find_options(int(FindOptions.PICK_FIELD0))
