"""GAS Token native contract."""

from __future__ import annotations
from typing import Any, Optional

from neo.types import UInt160
from neo.native.fungible_token import FungibleToken, AccountState


class GasToken(FungibleToken):
    """GAS token - utility token for the Neo blockchain.
    
    GAS is used to pay for transaction fees and smart contract execution.
    It has 8 decimal places and is generated through NEO holding.
    """
    
    # Initial GAS distribution: 30 million GAS
    INITIAL_GAS = 30_000_000 * 10**8
    
    def __init__(self) -> None:
        super().__init__()
    
    @property
    def name(self) -> str:
        return "GasToken"
    
    @property
    def symbol(self) -> str:
        return "GAS"
    
    @property
    def decimals(self) -> int:
        return 8
    
    @property
    def factor(self) -> int:
        """1 GAS = 10^8 datoshi."""
        return 10 ** 8
    
    def initialize(self, engine: Any) -> None:
        """Initialize GAS token on genesis.
        
        Mints the initial GAS distribution to the BFT address.
        """
        initial_gas = engine.protocol_settings.initial_gas_distribution
        bft_address = engine.protocol_settings.get_bft_address()
        self.mint(engine, bft_address, initial_gas, False)
    
    def on_persist(self, engine: Any) -> None:
        """Process transactions in block.
        
        For each transaction:
        - Burns system fee and network fee from sender
        - Mints network fee to primary validator
        """
        total_network_fee = 0
        
        for tx in engine.persisting_block.transactions:
            # Burn system fee and network fee from sender
            total_fee = tx.system_fee + tx.network_fee
            if total_fee > 0:
                self.burn(engine, tx.sender, total_fee)
            total_network_fee += tx.network_fee
        
        # Mint network fee to primary validator
        if total_network_fee > 0:
            validators = engine.get_next_block_validators()
            if validators:
                primary_index = engine.persisting_block.primary_index
                primary_pubkey = validators[primary_index % len(validators)]
                primary = engine.get_script_hash_from_pubkey(primary_pubkey)
                self.mint(engine, primary, total_network_fee, False)
    
    def mint(self, engine: Any, account: UInt160, amount: int, 
             call_on_payment: bool = True) -> None:
        """Mint GAS to an account.
        
        Args:
            engine: The application engine
            account: The account to mint to
            amount: Amount in datoshi (1 GAS = 10^8 datoshi)
            call_on_payment: Whether to call onNEP17Payment
        """
        super().mint(engine, account, amount, call_on_payment)
    
    def burn(self, engine: Any, account: UInt160, amount: int) -> None:
        """Burn GAS from an account.
        
        Args:
            engine: The application engine
            account: The account to burn from
            amount: Amount in datoshi (1 GAS = 10^8 datoshi)
        """
        super().burn(engine, account, amount)
    
    def transfer(self, engine: Any, from_account: UInt160, to_account: UInt160,
                 amount: int, data: Any = None) -> bool:
        """Transfer GAS between accounts.
        
        Args:
            engine: The application engine
            from_account: Source account
            to_account: Destination account
            amount: Amount in datoshi
            data: Optional data to pass to onNEP17Payment
            
        Returns:
            True if transfer succeeded, False otherwise
        """
        return super().transfer(engine, from_account, to_account, amount, data)
