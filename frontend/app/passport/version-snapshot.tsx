import type { PersonaDraft, PersonaVersion } from "../../lib/persona-contracts";
import { RecordedTime, Unsigned } from "./governance-common";

export function VersionSnapshot({ version }: { version: PersonaVersion }) {
  return (
    <article className="governance-card">
      <div className="governance-heading">
        <h3>Version {version.revision}</h3>
        <Unsigned />
      </div>
      <p className="help">
        <RecordedTime value={version.recorded_at} />
      </p>
      <ContentFields content={version.content} />
      <details>
        <summary>Version reference</summary>
        <dl className="governance-fields">
          <div>
            <dt>Version ID</dt>
            <dd>{version.version_id}</dd>
          </div>
          <div>
            <dt>Creator reference</dt>
            <dd>{version.creator_ref}</dd>
          </div>
        </dl>
      </details>
    </article>
  );
}

export function ContentFields({ content }: { content: PersonaDraft }) {
  return (
    <dl className="governance-fields">
      <div>
        <dt>Name</dt>
        <dd>{content.name}</dd>
      </div>
      <div>
        <dt>Biography</dt>
        <dd>{content.biography}</dd>
      </div>
      <div>
        <dt>Human contribution</dt>
        <dd>{content.human_contribution}</dd>
      </div>
      <div>
        <dt>AI disclosure</dt>
        <dd>{content.ai_disclosure}</dd>
      </div>
    </dl>
  );
}
