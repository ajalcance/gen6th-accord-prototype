"""Durable reference-only face intents and immutable bounded transitions."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0015jobs"
down_revision: str | Sequence[str] | None = "0014production"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# Frozen migration SQL; metadata-created tests register equivalent policy separately.
STATEMENTS = (
    """
CREATE TABLE persona_face_jobs (
	id UUID NOT NULL,
	workspace_id UUID NOT NULL,
	version_id UUID NOT NULL,
	portrait_id UUID NOT NULL,
	request_id UUID NOT NULL,
	actor_ref VARCHAR(160) NOT NULL,
	config_id VARCHAR(64) NOT NULL,
	fingerprint VARCHAR(64) NOT NULL,
	command JSONB NOT NULL,
	recorded_at TIMESTAMP WITH TIME ZONE NOT NULL,
	PRIMARY KEY (id),
	UNIQUE (workspace_id, id),
	UNIQUE (workspace_id, request_id),
        FOREIGN KEY(workspace_id, version_id, portrait_id) REFERENCES persona_version_references
(workspace_id, version_id, portrait_id),
        CHECK (length(actor_ref) BETWEEN 1 AND 160 AND fingerprint ~ '^[0-9a-f]{64}$' AND
config_id ~ '^[0-9a-f]{64}$'),
	CHECK (jsonb_typeof(command) = 'object' AND octet_length(command::text) <= 4096)
)

""",
    """
CREATE TABLE persona_face_job_transitions (
	workspace_id UUID NOT NULL,
	job_id UUID NOT NULL,
	sequence INTEGER NOT NULL,
	request_id UUID NOT NULL,
	fingerprint VARCHAR(64) NOT NULL,
	dispatch_id UUID NOT NULL,
	state VARCHAR(16) NOT NULL,
	attempts INTEGER NOT NULL,
	recorded_at TIMESTAMP WITH TIME ZONE NOT NULL,
	lease_until TIMESTAMP WITH TIME ZONE,
	generation_id UUID,
	PRIMARY KEY (workspace_id, job_id, sequence),
	UNIQUE (workspace_id, request_id),
	FOREIGN KEY(workspace_id, job_id) REFERENCES persona_face_jobs (workspace_id, id),
	FOREIGN KEY(generation_id) REFERENCES persona_face_generations (id),
	CHECK (sequence BETWEEN 0 AND 32 AND attempts BETWEEN 0 AND 3),
        CHECK (fingerprint ~ '^[0-9a-f]{64}$' AND state IN
('queued','dispatched','running','succeeded','failed','cancelled')),
        CHECK ((state = 'running') = (lease_until IS NOT NULL) AND (state = 'succeeded') =
(generation_id IS NOT NULL))
)

""",
    """CREATE INDEX ix_face_jobs_subject ON persona_face_jobs (workspace_id, version_id,
portrait_id, recorded_at)""",
    """ALTER TABLE "persona_face_jobs" ENABLE ROW LEVEL SECURITY""",
    """ALTER TABLE "persona_face_jobs" FORCE ROW LEVEL SECURITY""",
    """CREATE POLICY tenant_scope ON "persona_face_jobs" USING (workspace_id =
NULLIF(current_setting('accord.workspace_id', true), '')::uuid) WITH CHECK (workspace_id =
NULLIF(current_setting('accord.workspace_id', true), '')::uuid)""",
    """CREATE TRIGGER immutable_record BEFORE UPDATE OR DELETE ON "persona_face_jobs" FOR EACH
ROW EXECUTE FUNCTION accord_persona_immutable()""",
    """ALTER TABLE "persona_face_job_transitions" ENABLE ROW LEVEL SECURITY""",
    """ALTER TABLE "persona_face_job_transitions" FORCE ROW LEVEL SECURITY""",
    """CREATE POLICY tenant_scope ON "persona_face_job_transitions" USING (workspace_id =
NULLIF(current_setting('accord.workspace_id', true), '')::uuid) WITH CHECK (workspace_id =
NULLIF(current_setting('accord.workspace_id', true), '')::uuid)""",
    """CREATE TRIGGER immutable_record BEFORE UPDATE OR DELETE ON "persona_face_job_transitions"
FOR EACH ROW EXECUTE FUNCTION accord_persona_immutable()""",
    """
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
""",
    """CREATE TRIGGER job_protocol BEFORE INSERT ON persona_face_job_transitions FOR EACH ROW
EXECUTE FUNCTION accord_face_job_transition()""",
)


def upgrade() -> None:
    for statement in STATEMENTS:
        op.execute(sa.text(statement))


def downgrade() -> None:
    op.execute(sa.text("""DO $$ BEGIN
      IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = current_user
                     AND (rolsuper OR rolbypassrls)) THEN
        RAISE EXCEPTION 'job rollback requires all-tenant migration authority';
      END IF;
    END $$"""))
    op.execute(
        sa.text(
            "LOCK TABLE persona_face_jobs, persona_face_job_transitions IN ACCESS EXCLUSIVE MODE"
        )
    )
    op.execute(sa.text("""DO $$ BEGIN
      IF EXISTS (SELECT 1 FROM persona_face_jobs) THEN
        RAISE EXCEPTION 'job rollback refuses populated intent';
      END IF;
    END $$"""))
    op.drop_table("persona_face_job_transitions")
    op.execute(sa.text("DROP FUNCTION accord_face_job_transition()"))
    op.drop_table("persona_face_jobs")
