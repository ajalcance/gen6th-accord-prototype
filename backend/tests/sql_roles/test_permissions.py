"""Required SQL succeeds; effective role/RLS boundaries reject the intended forbidden action."""

from typing import Any
from uuid import uuid4

import pytest

from accord.personas.runtime_role import ROLE_QUERY


async def seed(connection: Any) -> tuple[str, str]:
    workspace, persona, version = uuid4(), uuid4(), uuid4()
    await connection.execute(
        "INSERT INTO persona_workspace_members VALUES ($1, 'creator', 'creator')", workspace
    )
    await connection.execute(
        "INSERT INTO personas VALUES ($1, $2, 'creator', 1)", persona, workspace
    )
    await connection.execute(
        """INSERT INTO persona_versions
        (id, workspace_id, persona_id, revision, creator_ref, recorded_at, name,
         biography, human_contribution, ai_disclosure, event_id)
        VALUES ($1, $2, $3, 1, 'creator', now(), 'Synthetic', 'Fixture', 'Fixture',
                'Synthetic fixture', $4)""",
        version,
        workspace,
        persona,
        uuid4().hex,
    )
    return str(workspace), str(version)


async def denied(connection: Any, statement: str, code: str = "42501") -> None:
    await connection.execute("SAVEPOINT denied_operation")
    try:
        with pytest.raises(Exception) as error:
            await connection.execute(statement)
        actual = getattr(error.value, "sqlstate", None)
        assert actual == code, (
            f"Statement: {statement}; expected SQLSTATE={code}, actual={actual}; "
            f"{type(error.value).__name__}: {error.value}"
        )
    finally:
        await connection.execute("ROLLBACK TO SAVEPOINT denied_operation")


@pytest.mark.parametrize("workload", ["api", "reference", "compliance"])
async def test_roles_pass_existing_guard_without_admin_or_ddl(role_db: Any, workload: str) -> None:
    db = role_db.connection
    await role_db.assume(workload)
    assert await db.fetchval(ROLE_QUERY) is False
    attributes = await db.fetchrow(
        "SELECT rolsuper, rolbypassrls, rolcreatedb, rolcreaterole, rolreplication, "
        "rolinherit, rolcanlogin FROM pg_roles WHERE rolname = current_user"
    )
    assert not any(attributes)
    for statement in (
        "CREATE TABLE public.forbidden_table (id integer)",
        "CREATE TEMP TABLE forbidden_temp (id integer)",
        "ALTER TABLE personas DISABLE ROW LEVEL SECURITY",
        'SET LOCAL ROLE "' + role_db.operator.replace('"', '""') + '"',
        "INSERT INTO persona_workspace_members VALUES (gen_random_uuid(), 'x', 'creator')",
        "UPDATE persona_workspace_members SET role = 'creator'",
        "DELETE FROM persona_workspace_members",
        "INSERT INTO persona_identity_bindings DEFAULT VALUES",
        "UPDATE persona_identity_bindings SET actor_ref = 'x'",
        "DELETE FROM persona_identity_bindings",
    ):
        await denied(db, statement)


@pytest.mark.parametrize("workload", ["api", "reference"])
async def test_scoped_reads_membership_and_head_locks(role_db: Any, workload: str) -> None:
    db = role_db.connection
    workspace, _ = await seed(db)
    await role_db.assume(workload)
    assert await db.fetchval("SELECT count(*) FROM personas") == 0
    await db.execute("SELECT set_config('accord.workspace_id', $1, true)", str(uuid4()))
    assert await db.fetchval("SELECT count(*) FROM personas") == 0
    await db.execute("SELECT set_config('accord.workspace_id', $1, true)", workspace)
    assert await db.fetchval("SELECT head_revision FROM personas FOR UPDATE") == 1
    assert (
        await db.fetchval(
            "SELECT accord_workspace_membership($1::uuid, 'creator'::varchar)", workspace
        )
        == "creator"
    )
    assert (
        await db.fetchval(
            "SELECT accord_workspace_membership($1::uuid, 'creator'::varchar)", str(uuid4())
        )
        is None
    )
    await denied(db, "UPDATE personas SET owner_ref = 'creator'")
    await denied(db, "DELETE FROM personas")
    # Documented real authority needed for head locks, including the reference role.
    await db.execute("UPDATE personas SET head_revision = 2")
    assert await db.fetchval("SELECT head_revision FROM personas") == 2


async def test_api_evidence_insert_and_immutable_lock(role_db: Any) -> None:
    db = role_db.connection
    workspace, version = await seed(db)
    await role_db.assume("api", workspace)
    evidence = uuid4()
    await db.execute(
        """INSERT INTO persona_private_evidence
        (id, workspace_id, version_id, owner_ref, request_id, fingerprint, media_type,
         byte_length, sha256, recorded_at, expires_at)
        VALUES ($1, $2::uuid, $3::uuid, 'creator', $4, $5, 'text/plain', 1, $5,
                now(), now() + interval '7 days')""",
        evidence,
        workspace,
        version,
        uuid4(),
        "a" * 64,
    )
    await db.execute(
        """INSERT INTO private_evidence_payloads
        (evidence_id, workspace_id, ciphertext, nonce, key_id, wrapped_key)
        VALUES ($1, $2::uuid, $3, $4, 'fixture-key', $5)""",
        evidence,
        workspace,
        b"x" * 17,
        b"n" * 12,
        b"wrapped",
    )
    await db.execute(
        """INSERT INTO persona_evidence_inspections VALUES
        ($1, $2::uuid, 'clean', 'fixture', 'fixture', now())""",
        evidence,
        workspace,
    )
    assert await db.fetchval("SELECT id FROM persona_private_evidence FOR UPDATE") == evidence
    await db.execute("SELECT id FROM persona_passport_publications FOR UPDATE")
    await denied(db, "UPDATE persona_private_evidence SET id = id", "P0001")
    await denied(db, "UPDATE persona_private_evidence SET owner_ref = 'creator'")
    await denied(db, "DELETE FROM private_evidence_payloads")
    await denied(db, "DELETE FROM persona_private_evidence")


@pytest.mark.parametrize("workload", ["api", "reference"])
async def test_cross_workspace_insert_is_rls_denied(role_db: Any, workload: str) -> None:
    db = role_db.connection
    await role_db.assume(workload, str(uuid4()))
    if workload == "api":
        statement = "INSERT INTO personas VALUES (gen_random_uuid(), gen_random_uuid(), 'x', 1)"
        await denied(db, statement)
    else:
        await denied(
            db,
            """INSERT INTO persona_face_generations VALUES
            (gen_random_uuid(), gen_random_uuid(), gen_random_uuid(), gen_random_uuid(),
             gen_random_uuid(), 'fixture', repeat('a', 64), now(),
             decode(repeat('78', 17), 'hex'), decode(repeat('6e', 12), 'hex'),
             'fixture-key', decode('78', 'hex'))""",
        )


@pytest.mark.parametrize("workload", ["reference", "compliance"])
async def test_workers_cannot_access_originals_or_provision_jobs(
    role_db: Any, workload: str
) -> None:
    db = role_db.connection
    await role_db.assume(workload)
    for statement in (
        "SELECT * FROM persona_portrait_payloads",
        "SELECT * FROM private_evidence_payloads",
        "SELECT * FROM persona_private_evidence",
        "SELECT * FROM persona_identity_bindings",
        "SELECT * FROM persona_campaign_offers",
    ):
        await denied(db, statement)
    await denied(db, "INSERT INTO persona_face_jobs DEFAULT VALUES")
    if workload == "compliance":
        await denied(db, "SELECT * FROM persona_portrait_captures")
        await denied(db, "SELECT accord_workspace_membership(gen_random_uuid(), 'x'::varchar)")


async def test_compliance_spine_ingest_seal_detection_and_retention(role_db: Any) -> None:
    db = role_db.connection
    await role_db.assume("compliance")
    event_id = uuid4().hex
    await db.execute(
        """INSERT INTO events
        (event_id, ts, schema_v, actor_type, tenant_id, category, action, outcome, severity,
         source, metadata) VALUES ($1, now(), 1, 'system', $2, 'persona',
         'persona.version_saved', 'success', 'info', 'server', '{}')""",
        event_id,
        uuid4(),
    )
    assert await db.fetchval("SELECT count(*) FROM events") == 1
    assert await db.fetchval("SELECT nextval('audit_log_seq_seq')") > 0
    await db.execute(
        """INSERT INTO audit_log
        (event_id, ts, actor_type, action, outcome, severity, metadata, compliance_tags,
         prev_hash, entry_hash) VALUES ($1, now(), 'system', 'persona.version_saved',
         'success', 'info', '{}', '[]', $2, $3)""",
        event_id,
        "0" * 64,
        "a" * 64,
    )
    await db.execute(
        "INSERT INTO detection_receipts VALUES ($1, $2, now(), $3, true, '[]')",
        event_id,
        uuid4(),
        "a" * 64,
    )
    for statement in (
        "DELETE FROM audit_log",
        "DELETE FROM detection_receipts",
        "UPDATE audit_log SET event_id = event_id",
        "UPDATE detection_receipts SET event_id = event_id",
    ):
        await denied(db, statement)
    await db.execute("DELETE FROM events WHERE event_id = $1", event_id)
    assert await db.fetchval("SELECT count(*) FROM events") == 0


@pytest.mark.parametrize("workload", ["api", "reference"])
async def test_only_compliance_can_seal_delete_events_or_use_sequence(
    role_db: Any, workload: str
) -> None:
    db = role_db.connection
    await role_db.assume(workload)
    await denied(db, "INSERT INTO audit_log DEFAULT VALUES")
    await denied(db, "INSERT INTO detection_receipts DEFAULT VALUES")
    await denied(db, "DELETE FROM events")
    await denied(db, "SELECT nextval('audit_log_seq_seq')")
