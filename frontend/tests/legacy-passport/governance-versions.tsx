import { VersionPicker } from "./version-picker";
import { VersionSnapshot } from "../../app/passport/version-snapshot";
import { useEffect, useState } from "react";
import type { PersonaVersion } from "../../lib/persona-contracts";
import type { PersonaGateway } from "../../lib/persona-gateway";
import { EXAMPLE_PERSONA } from "./governance-fixtures";
import {
  GovernanceEmpty,
  GovernanceRead,
} from "../../app/passport/governance-common";
import { usePersonaQuery } from "../../app/passport/use-persona-query";

export default function GovernanceVersions({
  gateway,
  empty,
}: {
  gateway: PersonaGateway;
  empty: boolean;
}) {
  const [revision, setRevision] = useState(3);
  const { state, query } = usePersonaQuery<PersonaVersion>();
  useEffect(() => {
    if (!empty)
      void query.run((signal) =>
        gateway.load(EXAMPLE_PERSONA, revision, signal),
      );
    return () => query.clear();
  }, [gateway, revision, empty, query]);
  if (empty)
    return (
      <GovernanceEmpty title="No saved versions">
        Complete a System Capture record before requesting a save. Your browser
        draft stays editable; saving to the backend requires a verified
        connection.
      </GovernanceEmpty>
    );
  return (
    <section aria-label="Version history" className="governance-section">
      <div className="governance-heading">
        <div>
          <h3>Immutable version history</h3>
          <p className="help">
            Review and campaign decisions remain bound to the version they
            reference.
          </p>
        </div>
        <VersionPicker
          label="Version"
          revision={revision}
          change={setRevision}
        />
      </div>
      <GovernanceRead state={state} query={query}>
        {(version) => <VersionSnapshot version={version} />}
      </GovernanceRead>
    </section>
  );
}

export {
  ContentFields,
  VersionSnapshot,
} from "../../app/passport/version-snapshot";
