"""Append-only state-machine SQL for metadata-created schemas; migration freezes its own copy."""

from sqlalchemy import event

from accord.personas.database_policy import execute_ddl
from accord.personas.job_models import FaceJobTransition

PROTOCOL_SQL = """
CREATE FUNCTION accord_face_job_transition() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE previous persona_face_job_transitions; job persona_face_jobs;
BEGIN
  PERFORM pg_advisory_xact_lock(hashtextextended(
    'accord-face-job:' || NEW.workspace_id::text || ':' || NEW.job_id::text, 0));
  SELECT * INTO job FROM persona_face_jobs
    WHERE workspace_id = NEW.workspace_id AND id = NEW.job_id;
  IF NOT FOUND THEN RAISE EXCEPTION 'job intent required'; END IF;
  SELECT * INTO previous FROM persona_face_job_transitions
    WHERE workspace_id = NEW.workspace_id AND job_id = NEW.job_id ORDER BY sequence DESC LIMIT 1;
  IF NOT FOUND THEN
    IF NEW.sequence <> 0 OR NEW.state <> 'queued' OR NEW.attempts <> 0
      OR NEW.dispatch_id <> NEW.job_id
      THEN RAISE EXCEPTION 'initial queued state required'; END IF;
  ELSE
    IF NEW.sequence <> previous.sequence + 1 OR NEW.recorded_at < previous.recorded_at
      OR previous.state IN ('succeeded','cancelled')
      OR NEW.attempts <> previous.attempts + (CASE WHEN NEW.state = 'running' THEN 1 ELSE 0 END)
      THEN RAISE EXCEPTION 'invalid job sequence'; END IF;
    IF NEW.state = 'queued' THEN
      IF NEW.dispatch_id = previous.dispatch_id
        OR previous.state NOT IN ('queued','dispatched','running','failed')
        OR previous.attempts >= 3 OR previous.sequence >= 29 OR
        (previous.state = 'running' AND NEW.recorded_at < previous.lease_until) OR
        (previous.state IN ('queued','dispatched')
          AND NEW.recorded_at < previous.recorded_at + interval '2 minutes')
        THEN RAISE EXCEPTION 'job not recoverable'; END IF;
    ELSIF NEW.dispatch_id <> previous.dispatch_id THEN
      RAISE EXCEPTION 'dispatch binding changed';
    ELSIF NEW.state = 'dispatched' AND previous.state <> 'queued' THEN
      RAISE EXCEPTION 'job already dispatched';
    ELSIF NEW.state = 'running'
      AND (previous.state NOT IN ('queued','dispatched','failed','running')
      OR (previous.state = 'running' AND NEW.recorded_at < previous.lease_until)) THEN
      RAISE EXCEPTION 'job lease still active';
    ELSIF NEW.state IN ('succeeded','failed') AND previous.state <> 'running' THEN
      RAISE EXCEPTION 'job is not running';
    END IF;
  END IF;
  IF NEW.recorded_at < job.recorded_at OR (NEW.state = 'running' AND
    (NEW.lease_until <= NEW.recorded_at
      OR NEW.lease_until > NEW.recorded_at + interval '120 seconds'))
    THEN RAISE EXCEPTION 'invalid job clock'; END IF;
  IF NEW.state = 'succeeded' AND NOT EXISTS (SELECT 1 FROM persona_face_generations g
    WHERE g.id = NEW.generation_id AND g.workspace_id = job.workspace_id
      AND g.version_id = job.version_id AND g.portrait_id = job.portrait_id
      AND g.request_id = job.request_id AND g.actor_ref = job.actor_ref)
    THEN RAISE EXCEPTION 'job result binding changed'; END IF;
  RETURN NEW;
END; $$
"""


def register_job_policy() -> None:
    event.listen(FaceJobTransition.__table__, "after_create", execute_ddl(PROTOCOL_SQL))
    event.listen(
        FaceJobTransition.__table__,
        "after_create",
        execute_ddl(
            "CREATE TRIGGER job_protocol BEFORE INSERT ON persona_face_job_transitions "
            "FOR EACH ROW EXECUTE FUNCTION accord_face_job_transition()"
        ),
    )
    event.listen(
        FaceJobTransition.__table__,
        "after_drop",
        execute_ddl("DROP FUNCTION accord_face_job_transition()"),
    )
