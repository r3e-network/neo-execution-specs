"""Tests for TRY/CATCH/FINALLY exception handling."""

from neo.vm.execution_engine import ExecutionEngine, VMState


class TestTryCatchFinally:
    """Test TRY/CATCH/FINALLY exception handling."""
    
    def test_try_no_exception(self):
        """Test TRY block without exception."""
        # TRY { push 42 } CATCH { push 0 } -> should get 42
        script = bytes([
            0x3b, 8, 0,      # TRY catch=8, finally=0
            0x0c, 1, 42,     # PUSHDATA1 42
            0x3d, 5,         # ENDTRY +5 (jump past catch)
            0x10,            # PUSH0 (catch block)
            0x3d, 0,         # ENDTRY +0
        ])
        
        engine = ExecutionEngine()
        engine.load_script(script)
        state = engine.execute()
        
        assert state == VMState.HALT
        assert engine.result_stack.peek().get_integer() == 42
    
    def test_try_with_throw(self):
        """Test TRY block with THROW."""
        # TRY { push "err"; throw } CATCH { drop; push 99 }
        script = bytes([
            0x3b, 11, 0,     # TRY catch=11, finally=0
            0x0c, 3, 101, 114, 114,  # PUSHDATA1 "err"
            0x3a,            # THROW
            0x3d, 8,         # ENDTRY +8 (jump to end)
            0x45,            # DROP (catch: drop exception)
            0x0c, 1, 99,     # PUSHDATA1 99
            0x3d, 2,         # ENDTRY +2 (jump past itself)
        ])
        
        engine = ExecutionEngine()
        engine.load_script(script)
        state = engine.execute()
        
        assert state == VMState.HALT
        assert engine.result_stack.peek().get_integer() == 99
    
    def test_try_finally_no_exception(self):
        """Test TRY/FINALLY without exception."""
        # TRY { push 1 } FINALLY { push 2 }
        script = bytes([
            0x3b, 0, 7,      # TRY catch=0, finally=7
            0x0c, 1, 1,      # PUSHDATA1 1
            0x3d, 4,         # ENDTRY +4 (to end)
            0x0c, 1, 2,      # PUSHDATA1 2 (finally)
            0x3f,            # ENDFINALLY
        ])
        
        engine = ExecutionEngine()
        engine.load_script(script)
        state = engine.execute()
        
        assert state == VMState.HALT
        assert len(engine.result_stack) == 2
    
    def test_abort_cannot_be_caught(self):
        """Test that ABORT cannot be caught."""
        script = bytes([
            0x3b, 5, 0,      # TRY catch=5, finally=0
            0x38,            # ABORT
            0x3d, 4,         # ENDTRY (not reached)
            0x0c, 1, 99,     # PUSHDATA1 99 (catch)
            0x3d, 0,         # ENDTRY
        ])
        
        engine = ExecutionEngine()
        engine.load_script(script)
        state = engine.execute()
        
        assert state == VMState.FAULT
    
    def test_assert_true_continues(self):
        """Test ASSERT with true continues execution."""
        script = bytes([
            0x08,            # PUSHT
            0x39,            # ASSERT
            0x0c, 1, 42,     # PUSHDATA1 42
        ])
        
        engine = ExecutionEngine()
        engine.load_script(script)
        state = engine.execute()
        
        assert state == VMState.HALT
        assert engine.result_stack.peek().get_integer() == 42
    
    def test_assert_false_faults(self):
        """Test ASSERT with false causes fault."""
        script = bytes([
            0x09,            # PUSHF
            0x39,            # ASSERT
        ])
        
        engine = ExecutionEngine()
        engine.load_script(script)
        state = engine.execute()
        
        assert state == VMState.FAULT


class TestExceptionPropagation:
    """Test exception propagation through call stack."""
    
    def test_uncaught_exception_faults(self):
        """Test uncaught exception causes fault."""
        script = bytes([
            0x0c, 3, 101, 114, 114,  # PUSHDATA1 "err"
            0x3a,            # THROW
        ])
        
        engine = ExecutionEngine()
        engine.load_script(script)
        state = engine.execute()
        
        assert state == VMState.FAULT
    
    def test_exception_in_catch_propagates(self):
        """Test exception in catch block propagates."""
        # TRY { throw } CATCH { throw again }
        script = bytes([
            0x3b, 10, 0,     # TRY catch=10
            0x0c, 3, 101, 114, 114,  # PUSHDATA1 "err"
            0x3a,            # THROW
            0x3d, 6,         # ENDTRY
            0x0c, 3, 101, 114, 114,  # PUSHDATA1 "err2" (catch)
            0x3a,            # THROW again
            0x3d, 0,         # ENDTRY
        ])
        
        engine = ExecutionEngine()
        engine.load_script(script)
        state = engine.execute()
        
        assert state == VMState.FAULT
