"""FindOptions - Options for storage search operations."""

from enum import IntFlag


class FindOptions(IntFlag):
    """Specify the options to be used during storage search."""
    
    # No option is set. Results will be iterator of (key, value).
    NONE = 0
    
    # Only keys need to be returned.
    KEYS_ONLY = 1 << 0
    
    # Prefix byte of keys should be removed before return.
    REMOVE_PREFIX = 1 << 1
    
    # Only values need to be returned.
    VALUES_ONLY = 1 << 2
    
    # Values should be deserialized before return.
    DESERIALIZE_VALUES = 1 << 3
    
    # Only field 0 of deserialized values. Requires DESERIALIZE_VALUES.
    PICK_FIELD0 = 1 << 4
    
    # Only field 1 of deserialized values. Requires DESERIALIZE_VALUES.
    PICK_FIELD1 = 1 << 5
    
    # Results should be returned in backwards (descending) order.
    BACKWARDS = 1 << 7
    
    # All options combined (for validation).
    ALL = (KEYS_ONLY | REMOVE_PREFIX | VALUES_ONLY | 
           DESERIALIZE_VALUES | PICK_FIELD0 | PICK_FIELD1 | BACKWARDS)
