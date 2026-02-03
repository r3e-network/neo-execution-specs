"""Neo N3 Deployed Contract."""

from dataclasses import dataclass


@dataclass
class DeployedContract:
    """Deployed contract info."""
    script_hash: bytes
    nef_file: bytes
    manifest: dict
