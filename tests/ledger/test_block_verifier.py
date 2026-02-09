"""Tests for block verification."""

from neo.ledger.block_verifier import BlockVerifier
from neo.ledger.verify_result import VerifyResult
from neo.network.payloads.block import Block
from neo.network.payloads.witness import Witness


class TestBlockVerifier:
    """Block verifier tests."""
    
    def test_verify_structure_valid(self):
        """Valid block structure should pass."""
        block = Block(
            version=0,
            witness=Witness(
                invocation_script=b"\x00",
                verification_script=b"\x00"
            )
        )
        result = BlockVerifier.verify_structure(block)
        assert result == VerifyResult.SUCCEED
    
    def test_verify_structure_invalid_version(self):
        """Invalid version should fail."""
        block = Block(
            version=1,
            witness=Witness(
                invocation_script=b"\x00",
                verification_script=b"\x00"
            )
        )
        result = BlockVerifier.verify_structure(block)
        assert result == VerifyResult.INVALID
    
    def test_verify_structure_no_witness(self):
        """No witness should fail."""
        block = Block(version=0, witness=None)
        result = BlockVerifier.verify_structure(block)
        assert result == VerifyResult.INVALID
    
    def test_verify_chain_link_genesis(self):
        """Genesis block should pass chain link."""
        block = Block(index=0)
        result = BlockVerifier.verify_chain_link(block, None)
        assert result == VerifyResult.SUCCEED
    
    def test_verify_chain_link_no_prev(self):
        """Non-genesis without prev should fail."""
        block = Block(index=1)
        result = BlockVerifier.verify_chain_link(block, None)
        assert result == VerifyResult.INVALID
