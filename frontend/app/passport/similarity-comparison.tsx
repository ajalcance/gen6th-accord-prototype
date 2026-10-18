import { useEffect } from "react";
import type {
  QueryReceipt,
  SimilarityCandidate,
  SimilarityPage,
} from "../../lib/persona-similarity-contracts";
import type { FaceProfile } from "../../lib/persona-faces";
import type { PersonaVersion } from "../../lib/persona-contracts";
import { requireContract } from "../../lib/persona-validation";
import type { SavedPersonaSource } from "./saved-source";
import { usePersonaQuery } from "./use-persona-query";
import { ReadFeedback } from "./saved-record";
import SimilarityPreview from "./similarity-preview";
import ReferencePhoto from "./reference-photo";
import { VersionSnapshot } from "./version-snapshot";
import InvestigationPanel from "./investigation-panel";

const previewReady = () => undefined;
type ComparisonProps = {
  source: SavedPersonaSource;
  candidate: SimilarityCandidate;
  query: QueryReceipt;
  denied: () => void;
  scope: "current" | "history";
  page: SimilarityPage;
};
export default function SimilarityComparison({
  source,
  candidate,
  query: receipt,
  denied,
  scope,
  page,
}: ComparisonProps) {
  const { query, state } = useComparison(source, candidate, scope);
  useEffect(() => {
    if (state.phase === "denied") denied();
  }, [state.phase, denied]);
  return (
    <section aria-label="Candidate comparison">
      <h3>Compare {candidate.version.content.name}</h3>
      <ReadFeedback
        state={state}
        retry={() => void query.retry()}
        cancel={() => query.cancel()}
      />
      {state.phase === "ready" && source.similarity && source.captures && (
        <>
          <ComparisonImages
            source={source}
            candidate={candidate}
            query={receipt}
            denied={denied}
            faces={state.value.faces}
          />
          <VersionSnapshot version={state.value.version} />
          <InvestigationPanel
            source={source}
            candidate={candidate}
            receipt={receipt}
            page={page}
            denied={denied}
          />
        </>
      )}
    </section>
  );
}

function ComparisonImages({
  source,
  candidate,
  query: receipt,
  denied,
  faces,
}: Pick<ComparisonProps, "source" | "candidate" | "query" | "denied"> & {
  faces: FaceProfile;
}) {
  return (
    <div className="similarity-comparison">
      <SimilarityPreview
        gateway={source.similarity!}
        receipt={receipt}
        ready={previewReady}
        denied={denied}
      />
      <div>
        <ReferencePhoto
          gateway={source.captures!}
          version={candidate.version.version_id}
          portrait={candidate.portrait_id}
          faces={faces.latest!}
          denied={denied}
        />
        <p>Matched approved reference · generation {candidate.generation_id}</p>
      </div>
    </div>
  );
}

function useComparison(
  source: SavedPersonaSource,
  candidate: SimilarityCandidate,
  scope: "current" | "history",
) {
  const { query, state } = usePersonaQuery<{
    version: PersonaVersion;
    faces: FaceProfile;
  }>();
  useEffect(() => {
    void query.run(async (signal) => {
      requireContract(!!source.faces && !!source.captures);
      const version = await source.gateway.load(
        candidate.version.persona_id,
        scope === "current" ? null : candidate.version.revision,
        signal,
      );
      requireContract(version.version_id === candidate.version.version_id);
      const faces = await source.faces.query(
        { version_id: version.version_id, portrait_id: candidate.portrait_id },
        signal,
      );
      requireContract(
        faces.latest?.generation_id === candidate.generation_id &&
          faces.latest.state === "represented",
      );
      return { version, faces };
    });
    return () => query.stop();
  }, [source, candidate, query, scope]);
  return { query, state };
}
