"""
Transaction Verifier - Transaction verification logic.

Reference: Neo.Ledger.TransactionVerifier
"""

from __future__ import annotations
from typing import TYPE_CHECKING

from neo.ledger.verify_result import VerifyResult

if TYPE_CHECKING:
    from neo.network.payloads.transaction import Transaction
    from neo.persistence.snapshot import Snapshot

# Constants
MAX_TRANSACTION_SIZE = 102400
MAX_VALID_UNTIL_BLOCK_INCREMENT = 5760  # ~24 hours at 15s blocks
MAX_TRANSACTION_ATTRIBUTES = 16

class TransactionVerifier:
    """Verifies transactions for validity."""
    
    @staticmethod
    def verify_state_independent(tx: "Transaction") -> VerifyResult:
        """
        Verify transaction without blockchain state.
        
        Checks:
        - Size limits
        - Version
        - Script validity
        - Signer validity
        - Attribute validity
        """
        # Check size
        if tx.size > MAX_TRANSACTION_SIZE:
            return VerifyResult.INVALID
        
        # Check version
        if tx.version > 0:
            return VerifyResult.INVALID
        
        # Check script
        if not tx.script or len(tx.script) == 0:
            return VerifyResult.INVALID
        
        # Check signers
        if not tx.signers or len(tx.signers) == 0:
            return VerifyResult.INVALID
        
        # Check for duplicate signers
        signer_accounts: set[bytes] = set()
        for signer in tx.signers:
            if signer.account is None:
                return VerifyResult.INVALID
            account_bytes = signer.account.data
            if account_bytes in signer_accounts:
                return VerifyResult.INVALID
            signer_accounts.add(account_bytes)
        
        # Check attributes count
        if len(tx.attributes) > MAX_TRANSACTION_ATTRIBUTES:
            return VerifyResult.INVALID
        
        # Check fees
        if tx.system_fee < 0:
            return VerifyResult.INVALID
        if tx.network_fee < 0:
            return VerifyResult.INVALID
        
        return VerifyResult.SUCCEED
    
    @staticmethod
    def verify_state_dependent(
        tx: "Transaction",
        snapshot: "Snapshot",
        block_height: int
    ) -> VerifyResult:
        """
        Verify transaction with blockchain state.
        
        Checks:
        - ValidUntilBlock
        - Conflicts
        - Balance
        - Witness verification
        """
        # Check ValidUntilBlock
        if tx.valid_until_block <= block_height:
            return VerifyResult.EXPIRED
        
        if tx.valid_until_block > block_height + MAX_VALID_UNTIL_BLOCK_INCREMENT:
            return VerifyResult.INVALID
        
        # Check for conflicts with existing transactions
        if TransactionVerifier._has_conflicts(tx, snapshot):
            return VerifyResult.HAS_CONFLICTS
        
        # Check sender balance
        if not TransactionVerifier._verify_balance(tx, snapshot):
            return VerifyResult.INSUFFICIENT_FUNDS

        # Verify witnesses (signature / contract verification)
        witness_result = TransactionVerifier.verify_witnesses(tx, snapshot)
        if witness_result != VerifyResult.SUCCEED:
            return witness_result

        return VerifyResult.SUCCEED
    
    @staticmethod
    def _has_conflicts(tx: "Transaction", snapshot: "Snapshot") -> bool:
        """Check if transaction conflicts with existing ones."""
        # Check Conflicts attribute
        for attr in tx.attributes:
            if hasattr(attr, 'hash') and attr.__class__.__name__ == 'Conflicts':
                # Check if conflicting tx exists
                if snapshot.contains_transaction(attr.hash):
                    return True
        return False
    
    @staticmethod
    def _verify_balance(tx: "Transaction", snapshot: "Snapshot") -> bool:
        """Verify sender has sufficient balance for fees."""
        if not tx.signers:
            return False
        
        sender = tx.signers[0].account
        total_fee = tx.system_fee + tx.network_fee
        
        # Get GAS balance
        balance = snapshot.get_gas_balance(sender)
        
        return balance >= total_fee
    
    @staticmethod
    def verify_witnesses(
        tx: "Transaction",
        snapshot: "Snapshot"
    ) -> VerifyResult:
        """Verify transaction witnesses."""
        if len(tx.witnesses) != len(tx.signers):
            return VerifyResult.INVALID
        
        # Each witness must verify against its signer
        for i, (signer, witness) in enumerate(zip(tx.signers, tx.witnesses)):
            if not TransactionVerifier._verify_witness(
                tx, signer, witness, snapshot
            ):
                return VerifyResult.INVALID
        
        return VerifyResult.SUCCEED
    
    @staticmethod
    def _verify_witness(
        tx: "Transaction",
        signer,
        witness,
        snapshot: "Snapshot"
    ) -> bool:
        """Verify a single witness by executing its scripts in the VM.

        Neo N3 witness verification:
        1. Hash the verification script and confirm it matches the signer account.
        2. Load the verification script first, then the invocation script on top.
        3. Execute — invocation runs first (pushes signatures), then verification
           consumes them and must leave ``True`` on the stack.
        """
        from neo.crypto.hash import hash160

        verification = getattr(witness, 'verification_script',
                               getattr(witness, 'verification', b''))
        invocation = getattr(witness, 'invocation_script',
                             getattr(witness, 'invocation', b''))

        if verification:
            # Standard account — hash must match signer
            script_hash = hash160(verification)
            if script_hash != bytes(signer.account):
                return False
        else:
            # Contract-based verification — fetch script from storage
            contract = snapshot.get_contract(signer.account)
            if contract is None:
                return False
            verification = getattr(contract, 'script', b'')
            if not verification:
                return False

        # Execute the witness scripts in a sandboxed VM
        try:
            from neo.smartcontract.application_engine import ApplicationEngine
            from neo.smartcontract.trigger import TriggerType
            from neo.vm.execution_engine import VMState

            engine = ApplicationEngine(
                trigger=TriggerType.VERIFICATION,
                gas_limit=50_000_000,  # 0.5 GAS cap for verification
                snapshot=snapshot,
                script_container=tx,
            )

            # Load verification script first (entry script — executes second)
            engine.load_script(verification)

            # Load invocation script on top (executes first, pushes signatures)
            if invocation:
                engine.load_script(invocation)

            engine.execute()

            if engine.state != VMState.HALT:
                return False

            # Stack must contain exactly one truthy item
            if len(engine.result_stack) == 0:
                return False

            return engine.result_stack.peek().get_boolean()
        except (ValueError, TypeError, KeyError, AttributeError, IndexError, RuntimeError):
            return False
