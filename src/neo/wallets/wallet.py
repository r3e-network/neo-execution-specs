"""Neo N3 Wallet implementation."""

from dataclasses import dataclass, field
from typing import List, Optional

from neo.wallets.account import Account
from neo.wallets.key_pair import KeyPair


@dataclass
class Wallet:
    """NEP-6 compatible wallet."""
    
    name: str = "MyWallet"
    version: str = "1.0"
    accounts: List[Account] = field(default_factory=list)
    extra: dict = field(default_factory=dict)
    _path: Optional[str] = None
    
    def create_account(self, label: str = "") -> Account:
        """Create new account with random key."""
        key_pair = KeyPair.generate()
        account = Account.from_key_pair(key_pair, label)
        
        if not self.accounts:
            account.is_default = True
        
        self.accounts.append(account)
        return account
    
    def import_key(self, wif: str, label: str = "") -> Account:
        """Import account from WIF."""
        key_pair = KeyPair.from_wif(wif)
        account = Account.from_key_pair(key_pair, label)
        self.accounts.append(account)
        return account
    
    def get_account(self, script_hash: bytes) -> Optional[Account]:
        """Get account by script hash."""
        for account in self.accounts:
            if account.script_hash == script_hash:
                return account
        return None
    
    @property
    def default_account(self) -> Optional[Account]:
        """Get default account."""
        for account in self.accounts:
            if account.is_default:
                return account
        return self.accounts[0] if self.accounts else None
