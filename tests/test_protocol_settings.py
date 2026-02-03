"""Tests for Protocol Settings."""

import pytest
from neo.protocol_settings import ProtocolSettings


class TestProtocolSettings:
    """Tests for ProtocolSettings class."""
    
    def test_default_values(self):
        """Test default protocol settings."""
        settings = ProtocolSettings()
        assert settings.network == 860833102  # MainNet
        assert settings.address_version == 53
        assert settings.validators_count == 7
        assert settings.committee_members_count == 21
        assert settings.milliseconds_per_block == 15000
        assert settings.max_transactions_per_block == 512
        assert settings.memory_pool_max_transactions == 50000
        assert settings.max_traceable_blocks == 2102400
    
    def test_initial_gas_distribution(self):
        """Test initial GAS distribution."""
        settings = ProtocolSettings()
        # 52 million GAS with 8 decimals
        expected = 52_000_000 * 100_000_000
        assert settings.initial_gas_distribution == expected
    
    def test_custom_network(self):
        """Test custom network magic."""
        settings = ProtocolSettings(network=12345)
        assert settings.network == 12345
    
    def test_custom_validators(self):
        """Test custom validator count."""
        settings = ProtocolSettings(validators_count=21)
        assert settings.validators_count == 21
    
    def test_hardforks_empty(self):
        """Test empty hardforks by default."""
        settings = ProtocolSettings()
        assert settings.hardforks == {}
    
    def test_hardforks_custom(self):
        """Test custom hardforks."""
        hardforks = {"HF_Aspidochelone": 1730000}
        settings = ProtocolSettings(hardforks=hardforks)
        assert settings.hardforks == hardforks
    
    def test_standby_committee_empty(self):
        """Test empty standby committee by default."""
        settings = ProtocolSettings()
        assert settings.standby_committee == []
    
    def test_standby_committee_custom(self):
        """Test custom standby committee."""
        committee = [b'\x02' + b'\x00' * 32, b'\x03' + b'\x00' * 32]
        settings = ProtocolSettings(standby_committee=committee)
        assert settings.standby_committee == committee
    
    def test_testnet_settings(self):
        """Test TestNet-like settings."""
        settings = ProtocolSettings(
            network=894710606,  # TestNet magic
            validators_count=7,
            committee_members_count=21,
        )
        assert settings.network == 894710606
    
    def test_block_time_seconds(self):
        """Test block time in seconds."""
        settings = ProtocolSettings()
        block_time_seconds = settings.milliseconds_per_block / 1000
        assert block_time_seconds == 15.0
    
    def test_blocks_per_day(self):
        """Test approximate blocks per day."""
        settings = ProtocolSettings()
        seconds_per_day = 24 * 60 * 60
        block_time_seconds = settings.milliseconds_per_block / 1000
        blocks_per_day = seconds_per_day / block_time_seconds
        assert blocks_per_day == 5760  # 24 * 60 * 60 / 15
