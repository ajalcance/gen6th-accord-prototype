"""Envelope encryption binds source receipts and attribution; stores no supplied pixels."""

from unittest.mock import Mock
from uuid import uuid4

import pytest
from cryptography.exceptions import InvalidTag

from accord.personas.investigation_storage import load, store
from personas.investigation_fixtures import command, result
from personas.test_photo_storage import FixtureWrapper


@pytest.mark.asyncio
async def test_packet_roundtrip_and_row_context_tampering() -> None:
    intent, session, wrapper = command(), Mock(), FixtureWrapper()
    packet = result(intent=intent)
    await store(session, packet, intent, wrapper)
    row = session.add.call_args.args[0]
    assert packet.source_note.encode() not in row.ciphertext
    assert (await load(row, wrapper)) == packet
    row.version_id = uuid4()
    with pytest.raises(AssertionError):
        await load(row, wrapper)
    row.version_id = packet.version_id
    row.ciphertext = row.ciphertext[:-1] + bytes([row.ciphertext[-1] ^ 1])
    with pytest.raises(InvalidTag):
        await load(row, wrapper)
