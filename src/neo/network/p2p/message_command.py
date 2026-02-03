"""Neo N3 Message Command."""

from enum import Enum


class MessageCommand(Enum):
    """P2P message commands."""
    VERSION = 0x00
    VERACK = 0x01
    GETADDR = 0x10
    ADDR = 0x11
    GETBLOCKS = 0x14
    MEMPOOL = 0x15
    INV = 0x27
    GETDATA = 0x28
    GETBLOCKBYINDEX = 0x29
    NOTFOUND = 0x2a
    TX = 0x2b
    BLOCK = 0x2c
    EXTENSIBLE = 0x2e
    REJECT = 0x2f
    PING = 0x31
    PONG = 0x32
