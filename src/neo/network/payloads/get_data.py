"""Neo N3 GetData Payload."""

from __future__ import annotations

from neo.network.payloads.inv import InvPayload


class GetDataPayload(InvPayload):
    """GetData request payload.

    Neo v3.9.1 uses the same wire shape as `InvPayload`.
    """
