"""Integration tests for Neo execution specs.

Tests end-to-end execution of smart contracts.
"""

import pytest
from neo.vm.execution_engine import ExecutionEngine, VMState
from neo.vm.script_builder import ScriptBuilder
from neo.vm.opcode import OpCode
from neo.vm.types import Integer, ByteString, Array, Boolean


class TestVMIntegration:
    """VM integration tests."""
    
    def test_simple_arithmetic(self):
        """Test simple arithmetic operations."""
        sb = ScriptBuilder()
        sb.emit_push(10)
        sb.emit_push(20)
        sb.emit(OpCode.ADD)
        
        engine = ExecutionEngine()
        engine.load_script(sb.to_bytes())
        engine.execute()
        
        assert engine.state == VMState.HALT
        result = engine.result_stack.pop()
        assert result.get_integer() == 30
    
    def test_conditional_execution(self):
        """Test conditional execution."""
        sb = ScriptBuilder()
        sb.emit_push(True)
        sb.emit_jump(OpCode.JMPIFNOT, 5)  # Jump over PUSH1
        sb.emit_push(1)
        sb.emit_jump(OpCode.JMP, 3)  # Jump over PUSH2
        sb.emit_push(2)
        
        engine = ExecutionEngine()
        engine.load_script(sb.to_bytes())
        engine.execute()
        
        assert engine.state == VMState.HALT
        result = engine.result_stack.pop()
        assert result.get_integer() == 1
    
    def test_increment_decrement(self):
        """Test increment and decrement operations."""
        sb = ScriptBuilder()
        sb.emit_push(10)
        sb.emit(OpCode.INC)
        sb.emit(OpCode.INC)
        sb.emit(OpCode.DEC)
        
        engine = ExecutionEngine()
        engine.load_script(sb.to_bytes())
        engine.execute()
        
        assert engine.state == VMState.HALT
        result = engine.result_stack.pop()
        assert result.get_integer() == 11
    
    def test_array_operations(self):
        """Test array creation and manipulation."""
        sb = ScriptBuilder()
        sb.emit_push(3)
        sb.emit(OpCode.NEWARRAY)
        sb.emit(OpCode.DUP)
        sb.emit_push(0)
        sb.emit_push(100)
        sb.emit(OpCode.SETITEM)
        sb.emit(OpCode.DUP)
        sb.emit_push(0)
        sb.emit(OpCode.PICKITEM)
        
        engine = ExecutionEngine()
        engine.load_script(sb.to_bytes())
        engine.execute()
        
        assert engine.state == VMState.HALT
        result = engine.result_stack.pop()
        assert result.get_integer() == 100
    
    def test_string_operations(self):
        """Test string concatenation."""
        sb = ScriptBuilder()
        sb.emit_push(b"Hello")
        sb.emit_push(b" World")
        sb.emit(OpCode.CAT)
        
        engine = ExecutionEngine()
        engine.load_script(sb.to_bytes())
        engine.execute()
        
        assert engine.state == VMState.HALT
        result = engine.result_stack.pop()
        assert result.value == b"Hello World"
    
    def test_map_operations(self):
        """Test map creation and access."""
        sb = ScriptBuilder()
        sb.emit(OpCode.NEWMAP)
        sb.emit(OpCode.DUP)
        sb.emit_push(b"key")
        sb.emit_push(b"value")
        sb.emit(OpCode.SETITEM)
        sb.emit(OpCode.DUP)
        sb.emit_push(b"key")
        sb.emit(OpCode.PICKITEM)
        
        engine = ExecutionEngine()
        engine.load_script(sb.to_bytes())
        engine.execute()
        
        assert engine.state == VMState.HALT
        result = engine.result_stack.pop()
        assert result.value == b"value"


class TestCryptoIntegration:
    """Crypto integration tests."""
    
    def test_hash160(self):
        """Test hash160 computation."""
        from neo.crypto.hash import hash160
        
        data = b"test data"
        result = hash160(data)
        assert len(result) == 20
    
    def test_hash256(self):
        """Test hash256 computation."""
        from neo.crypto.hash import hash256
        
        data = b"test data"
        result = hash256(data)
        assert len(result) == 32
    
    def test_merkle_tree(self):
        """Test merkle tree computation."""
        from neo.crypto.merkle_tree import MerkleTree
        
        hashes = [b"\x01" * 32, b"\x02" * 32, b"\x03" * 32]
        root = MerkleTree.compute_root(hashes)
        assert len(root) == 32
    
    def test_merkle_proof(self):
        """Test merkle proof generation and verification."""
        from neo.crypto.merkle_tree import MerkleTree
        
        hashes = [b"\x01" * 32, b"\x02" * 32, b"\x03" * 32, b"\x04" * 32]
        tree = MerkleTree(hashes)
        root = tree.root
        
        # Get proof for first leaf
        proof = tree.get_proof(0)
        assert MerkleTree.verify_proof(hashes[0], proof, root, 0)


class TestStorageIntegration:
    """Storage integration tests."""
    
    def test_memory_snapshot_crud(self):
        """Test CRUD operations on memory snapshot."""
        from neo.persistence.snapshot import MemorySnapshot
        
        snapshot = MemorySnapshot()
        
        # Create
        snapshot.put(b"key1", b"value1")
        assert snapshot.get(b"key1") == b"value1"
        
        # Update
        snapshot.put(b"key1", b"value2")
        assert snapshot.get(b"key1") == b"value2"
        
        # Delete
        snapshot.delete(b"key1")
        assert snapshot.get(b"key1") is None
    
    def test_snapshot_isolation(self):
        """Test snapshot isolation before commit."""
        from neo.persistence.snapshot import MemorySnapshot
        
        snapshot = MemorySnapshot()
        snapshot._store[b"key1"] = b"original"
        
        # Make changes
        snapshot.put(b"key1", b"modified")
        snapshot.put(b"key2", b"new")
        
        # Changes visible in snapshot
        assert snapshot.get(b"key1") == b"modified"
        assert snapshot.get(b"key2") == b"new"
        
        # Original store unchanged
        assert snapshot._store[b"key1"] == b"original"
        assert b"key2" not in snapshot._store
        
        # After commit, store updated
        snapshot.commit()
        assert snapshot._store[b"key1"] == b"modified"
        assert snapshot._store[b"key2"] == b"new"
    
    def test_snapshot_find(self):
        """Test prefix search in snapshot."""
        from neo.persistence.snapshot import MemorySnapshot
        
        snapshot = MemorySnapshot()
        snapshot.put(b"prefix:1", b"value1")
        snapshot.put(b"prefix:2", b"value2")
        snapshot.put(b"other:1", b"value3")
        snapshot.commit()
        
        results = list(snapshot.find(b"prefix:"))
        assert len(results) == 2
