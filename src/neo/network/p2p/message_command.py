"""Neo N3 Message Command."""

from enum import Enum


class MessageCommand(Enum):
    """P2P message commands."""

    # Handshaking
    VERSION = 0x00
    VERACK = 0x01

    # Connectivity
    GETADDR = 0x10
    ADDR = 0x11
    PING = 0x18
    PONG = 0x19

    # Synchronization
    GETHEADERS = 0x20
    HEADERS = 0x21
    GETBLOCKS = 0x24
    MEMPOOL = 0x25
    INV = 0x27
    GETDATA = 0x28
    GETBLOCKBYINDEX = 0x29
    NOTFOUND = 0x2a
    TRANSACTION = 0x2b
    TX = 0x2b
    BLOCK = 0x2c
    EXTENSIBLE = 0x2e
    REJECT = 0x2f

    # SPV protocol
    FILTERLOAD = 0x30
    FILTERADD = 0x31
    FILTERCLEAR = 0x32
    MERKLEBLOCK = 0x38

    # Others
    ALERT = 0x40
