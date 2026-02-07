"""Protocol settings compatibility tests against Neo v3.9.1 behavior."""

import pytest

from neo.hardfork import Hardfork
from neo.protocol_settings import ProtocolSettings


def test_mainnet_protocol_defaults_match_neo_v391():
    """Mainnet defaults should align with Neo v3.9.1 protocol configuration."""
    settings = ProtocolSettings.mainnet()

    assert settings.network == 860833102
    assert settings.address_version == 53
    assert settings.validators_count == 7
    assert settings.committee_members_count == 21
    assert settings.milliseconds_per_block == 15000
    assert settings.max_transactions_per_block == 512
    assert settings.max_valid_until_block_increment == 5760
    assert settings.memory_pool_max_transactions == 50000
    assert settings.max_traceable_blocks == 2102400
    assert settings.initial_gas_distribution == 52_000_000 * 100_000_000


def test_mainnet_hardfork_heights_match_neo_v390_plus():
    """Hardfork activation heights should match current Neo mainnet config."""
    settings = ProtocolSettings.mainnet()

    assert settings.hardforks[Hardfork.HF_ASPIDOCHELONE] == 1730000
    assert settings.hardforks[Hardfork.HF_BASILISK] == 4120000
    assert settings.hardforks[Hardfork.HF_COCKATRICE] == 5450000
    assert settings.hardforks[Hardfork.HF_DOMOVOI] == 5570000
    assert settings.hardforks[Hardfork.HF_ECHIDNA] == 7300000
    assert settings.hardforks[Hardfork.HF_FAUN] == 8800000


def test_hardfork_enablement_logic():
    """is_hardfork_enabled should mirror Neo behavior by block height."""
    settings = ProtocolSettings.mainnet()

    assert settings.is_hardfork_enabled(Hardfork.HF_ASPIDOCHELONE, 1730000)
    assert not settings.is_hardfork_enabled(Hardfork.HF_BASILISK, 4119999)
    assert settings.is_hardfork_enabled(Hardfork.HF_BASILISK, 4120000)


def test_omitted_leading_hardforks_are_filled_with_zero():
    """Neo fills omitted leading hardforks with zero when later fork is configured."""
    settings = ProtocolSettings(hardforks={Hardfork.HF_BASILISK: 4120000})

    assert settings.hardforks[Hardfork.HF_ASPIDOCHELONE] == 0
    assert settings.hardforks[Hardfork.HF_BASILISK] == 4120000
    assert settings.is_hardfork_enabled(Hardfork.HF_ASPIDOCHELONE, 0)
    assert not settings.is_hardfork_enabled(Hardfork.HF_BASILISK, 10)


def test_non_continuous_hardforks_are_rejected():
    """Gaps after the first configured fork should be rejected."""
    with pytest.raises(ValueError):
        ProtocolSettings(
            hardforks={
                Hardfork.HF_ASPIDOCHELONE: 100,
                Hardfork.HF_COCKATRICE: 200,
            }
        )


def test_custom_hardfork_non_monotonic_heights_are_rejected():
    """Earlier hardforks cannot have higher activation heights than later ones."""
    with pytest.raises(ValueError):
        ProtocolSettings(
            hardforks={
                Hardfork.HF_ASPIDOCHELONE: 10,
                Hardfork.HF_BASILISK: 1,
            }
        )


def test_mainnet_standby_committee_and_validators_count():
    """Mainnet standby committee size and validator projection should match Neo."""
    settings = ProtocolSettings.mainnet()

    assert len(settings.standby_committee) == 21
    assert len(settings.standby_validators) == 7
    assert settings.standby_validators == settings.standby_committee[:7]


def test_mainnet_seed_list_matches_neo_defaults():
    """Mainnet seed list should match Neo CLI defaults."""
    settings = ProtocolSettings.mainnet()

    assert settings.seed_list == [
        "seed1.neo.org:10333",
        "seed2.neo.org:10333",
        "seed3.neo.org:10333",
        "seed4.neo.org:10333",
        "seed5.neo.org:10333",
    ]


def test_bft_address_matches_neo_contract_logic_for_mainnet_validators():
    """BFT address derived from standby validators should stay deterministic."""
    settings = ProtocolSettings.mainnet()

    # Computed using Neo contract multisig script-hash logic for first 7 validators.
    assert str(settings.get_bft_address()) == "0x7fcd3a2c8e30d3f31b90e070e8b19307105eaf9e"


def test_default_constructor_stays_mainnet_compatible():
    """Plain constructor defaults should remain mainnet-compatible for ergonomics."""
    settings = ProtocolSettings()
    assert settings.network == 860833102
    assert settings.validators_count == 7
    assert settings.committee_members_count == 21


def test_testnet_protocol_defaults_match_neo_v391() -> None:
    """Testnet defaults should align with Neo v3.9.1 protocol configuration."""
    settings = ProtocolSettings.testnet()

    assert settings.network == 894710606
    assert settings.address_version == 53
    assert settings.validators_count == 7
    assert settings.committee_members_count == 21
    assert settings.milliseconds_per_block == 3000
    assert settings.max_transactions_per_block == 5000
    assert settings.max_valid_until_block_increment == 5760
    assert settings.memory_pool_max_transactions == 50000
    assert settings.max_traceable_blocks == 2102400
    assert settings.initial_gas_distribution == 52_000_000 * 100_000_000

    assert settings.hardforks[Hardfork.HF_ASPIDOCHELONE] == 210000
    assert settings.hardforks[Hardfork.HF_BASILISK] == 2680000
    assert settings.hardforks[Hardfork.HF_COCKATRICE] == 3967000
    assert settings.hardforks[Hardfork.HF_DOMOVOI] == 4144000
    assert settings.hardforks[Hardfork.HF_ECHIDNA] == 5870000
    assert settings.hardforks[Hardfork.HF_FAUN] == 12960000

    assert settings.seed_list == [
        "seed1t5.neo.org:20333",
        "seed2t5.neo.org:20333",
        "seed3t5.neo.org:20333",
        "seed4t5.neo.org:20333",
        "seed5t5.neo.org:20333",
    ]
