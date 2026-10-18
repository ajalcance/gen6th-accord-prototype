"""Offline SQL preparation evidence only; database protocol execution requires owner/CI."""

from accord.personas.job_models import FaceJob, FaceJobTransition
from accord.personas.job_policy import PROTOCOL_SQL
from personas.test_migration_sql import render_upgrade


def test_jobs_migration_preserves_immutable_scoped_intents_and_transition_protocol() -> None:
    sql = render_upgrade()
    assert "0015jobs" in sql
    for table in (FaceJob.__tablename__, FaceJobTransition.__tablename__):
        assert f"CREATE TABLE {table}" in sql
        assert f'ALTER TABLE "{table}" FORCE ROW LEVEL SECURITY' in sql
        assert f'BEFORE UPDATE OR DELETE ON "{table}"' in sql
    assert "CREATE TRIGGER job_protocol" in sql
    assert " ".join(PROTOCOL_SQL.split()) in " ".join(sql.split())
    assert "pg_advisory_xact_lock" in PROTOCOL_SQL
    assert "previous.sequence + 1" in PROTOCOL_SQL
    assert "previous.attempts + (CASE WHEN NEW.state = 'running' THEN 1 ELSE 0 END)" in PROTOCOL_SQL
    assert "120 seconds" in PROTOCOL_SQL
    assert "persona_face_generations" in PROTOCOL_SQL
    assert "UPDATE persona_face_jobs" not in sql
