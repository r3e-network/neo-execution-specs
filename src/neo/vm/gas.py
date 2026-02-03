"""Neo N3 GAS costs."""

# Opcode costs
OPCODE_PRICE = {
    0x00: 1,    # PUSHINT8
    0x10: 1,    # PUSH0
    0x40: 0,    # RET
    0x45: 512,  # SYSCALL
}
