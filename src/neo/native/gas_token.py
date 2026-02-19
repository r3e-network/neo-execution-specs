"""GAS Token native contract."""

from __future__ import annotations

from typing import Any

from neo.native.fungible_token import FungibleToken


class GasToken(FungibleToken):
    """GAS token - utility token for the Neo blockchain.
    
    GAS is used to pay for transaction fees and smart contract execution.
    It has 8 decimal places and is generated through NEO holding.
    """
    
    # Initial GAS distribution: 52 million GAS (matches C# ProtocolSettings.InitialGasDistribution)
    INITIAL_GAS = 52_000_000 * 10**8
    
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
        - Handles NotaryAssisted attribute fee deduction
        - Mints network fee to primary validator
        """
        total_network_fee = 0
        
        for tx in engine.persisting_block.transactions:
            # Burn system fee and network fee from sender
            total_fee = tx.system_fee + tx.network_fee
            if total_fee > 0:
                self.burn(engine, tx.sender, total_fee)
            total_network_fee += tx.network_fee
            
            # Handle NotaryAssisted attribute (type 0x22)
            notary_assisted = self._find_attribute(tx, 0x22)
            if notary_assisted is not None:
                n_keys = getattr(notary_assisted, 'n_keys', 0)
                attr_fee = self._get_attribute_fee(engine, 0x22)
                total_network_fee -= (n_keys + 1) * attr_fee
        
        # Mint network fee to primary validator
        if total_network_fee > 0:
            validators = engine.get_next_block_validators()
            if validators:
                primary_index = engine.persisting_block.primary_index
                primary_pubkey = validators[primary_index % len(validators)]
                primary = engine.get_script_hash_from_pubkey(primary_pubkey)
                self.mint(engine, primary, total_network_fee, False)
    
    @staticmethod
    def _find_attribute(tx: Any, attr_type: int) -> Any:
        """Find transaction attribute by type code."""
        for attr in getattr(tx, 'attributes', []) or []:
            if getattr(attr, 'type', None) == attr_type:
                return attr
        return None

    @staticmethod
    def _get_attribute_fee(engine: Any, attr_type: int) -> int:
        """Get attribute fee from PolicyContract."""
        from neo.native.native_contract import NativeContract
        policy = NativeContract.get_contract_by_name("PolicyContract")
        if policy is not None and hasattr(policy, 'get_attribute_fee'):
            return policy.get_attribute_fee(engine.snapshot, attr_type)
        return 0
