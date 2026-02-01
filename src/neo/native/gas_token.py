"""GAS Token native contract."""

from __future__ import annotations
from typing import Any

from neo.types import UInt160
from neo.native.fungible_token import FungibleToken, AccountState


class GasToken(FungibleToken):
    """GAS token - utility token for the Neo blockchain."""
    
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
    
    def initialize(self, engine: Any) -> None:
        """Initialize GAS token on genesis."""
        # Mint initial GAS distribution
        initial_gas = engine.protocol_settings.initial_gas_distribution
        bft_address = engine.protocol_settings.get_bft_address()
        self.mint(engine, bft_address, initial_gas, False)
    
    def on_persist(self, engine: Any) -> None:
        """Process transactions in block - burn fees, mint rewards."""
        total_network_fee = 0
        
        for tx in engine.persisting_block.transactions:
            # Burn system fee and network fee
            self.burn(engine, tx.sender, tx.system_fee + tx.network_fee)
            total_network_fee += tx.network_fee
        
        # Mint network fee to primary validator
        if total_network_fee > 0:
            validators = engine.get_next_block_validators()
            primary_index = engine.persisting_block.primary_index
            primary = engine.get_script_hash_from_pubkey(validators[primary_index])
            self.mint(engine, primary, total_network_fee, False)
