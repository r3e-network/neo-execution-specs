"""Tests for ExecutionEngine."""

from neo.vm import ExecutionEngine, VMState


def test_engine_creation():
    """Test engine creation."""
    engine = ExecutionEngine()
    assert engine.state == VMState.NONE
    assert len(engine.invocation_stack) == 0


def test_load_script():
    """Test loading a script."""
    engine = ExecutionEngine()
    script = bytes([0x10])  # PUSH0
    ctx = engine.load_script(script)
    assert ctx.script == script
    assert len(engine.invocation_stack) == 1
