import { useEffect, useRef, useState } from "react";
import { parseDraft, parseVersion } from "../../lib/persona-receipts";
import { useSavedSource, type SavedPersonaSource } from "./saved-source";
import { usePreparedWrite, useWriteDraft } from "./prepared-write-state";
import {
  WriteFeedback,
  unresolved,
  WriteConfirmation,
} from "./prepared-write-common";
import { CreationFields } from "./record-creation-fields";
import CreationCompletion from "./creation-completion";
import { usePersonaPhoto } from "./persona-photo-state";
import PersonaPhotoEditor from "./persona-photo-editor";
import CaptureHelper from "./capture-helper";

const empty = {
  name: "",
  biography: "",
  human_contribution: "",
  ai_disclosure: "",
  confirm: "",
};

export default function RecordCreation({
  records,
  open,
  prepare,
}: {
  records: () => void;
  open?: (id: string) => void;
  prepare?: (id: string) => void;
}) {
  const source = useSavedSource();
  const [generation, setGeneration] = useState(0);
  const owner = source
    ? `${source.workspaceId}:${source.sessionKey}`
    : "unconnected";
  return (
    <CreationForm
      key={`${owner}:${generation}`}
      draftKey={`${owner}:save:new-persona`}
      source={source}
      records={records}
      open={open}
      prepare={prepare}
      restart={() => setGeneration((value) => value + 1)}
    />
  );
}

function validSource(source: SavedPersonaSource | null) {
  return (
    !!source &&
    source.gateway.workspaceId === source.workspaceId &&
    source.writeGateway?.workspaceId === source.workspaceId
  );
}

function content(fields: Record<string, string>) {
  try {
    return parseDraft({
      name: fields.name ?? "",
      biography: fields.biography ?? "",
      human_contribution: fields.human_contribution ?? "",
      ai_disclosure: fields.ai_disclosure ?? "",
    });
  } catch {
    return null;
  }
}

type Props = {
  draftKey: string;
  source: SavedPersonaSource | null;
  records: () => void;
  open?: (id: string) => void;
  prepare?: (id: string) => void;
  restart: () => void;
};

function useCreation({ draftKey, source }: Props) {
  const draft = useWriteDraft(draftKey, empty);
  const [blocked, setBlocked] = useState(false);
  const photo = usePersonaPhoto(
    source?.photos?.workspaceId === source?.workspaceId
      ? source?.photos
      : undefined,
    () => draft.change("confirm", ""),
    () => setBlocked(true),
  );
  const connected = validSource(source) && !blocked;
  const mutation = usePreparedWrite(
    connected ? source!.writeGateway! : null,
    "save",
    draftKey,
    () => setBlocked(true),
  );
  const saved =
    draft.fields.created === "yes" || mutation.state.phase === "succeeded";
  const value = content(draft.fields);
  const allowed =
    connected &&
    photo.change?.action === "attach" &&
    !!value &&
    draft.fields.confirm === "yes" &&
    !saved &&
    mutation.state.phase !== "conflict" &&
    !unresolved(mutation.state) &&
    !mutation.requiresResolution;
  useCreationMarker(draft, mutation, draftKey);
  const submit = useCreationSubmit(mutation, photo, value, allowed);
  return { draft, mutation, photo, saved, allowed, connected, blocked, submit };
}

function useCreationSubmit(
  mutation: ReturnType<typeof usePreparedWrite>,
  photo: ReturnType<typeof usePersonaPhoto>,
  value: ReturnType<typeof content>,
  allowed: boolean,
) {
  const submitting = useRef(false);
  return function submit() {
    if (!allowed || !value || submitting.current) return;
    submitting.current = true;
    void mutation
      .submit({
        request_id: crypto.randomUUID(),
        persona_id: null,
        expected_revision: 0,
        content: value,
        ...(photo.change ? { photo: photo.change } : {}),
      })
      .then((result) => {
        if (result?.phase === "succeeded") photo.choose(null);
      })
      .finally(() => {
        submitting.current = false;
      });
  };
}

type CreationState = ReturnType<typeof useCreation>;

function useCreationMarker(
  draft: ReturnType<typeof useWriteDraft>,
  mutation: ReturnType<typeof usePreparedWrite>,
  draftKey: string,
) {
  useEffect(() => {
    if (mutation.state.phase !== "succeeded") return;
    const entry = draft.store?.get(draftKey);
    // Preserve only an authored-intent completion marker, never a fetched receipt.
    if (entry)
      draft.store?.set(draftKey, {
        ...entry,
        fields: { ...entry.fields, created: "yes" },
      });
  }, [mutation.state, draft.store, draftKey]);
}

function CreationForm(props: Props) {
  const state = useCreation(props);
  if (state.saved)
    return (
      <CreationCompletion
        version={
          state.mutation.state.phase === "succeeded"
            ? parseVersion(state.mutation.state.receipt)
            : null
        }
        fields={state.draft.fields}
        records={props.records}
        open={props.open}
        prepare={props.prepare}
        restart={() => {
          state.draft.store?.delete(props.draftKey);
          props.restart();
        }}
      />
    );
  return (
    <section className="record-creation" aria-label="System Capture">
      <h1 tabIndex={-1}>System Capture</h1>
      <p className="help">
        Register the persona&apos;s face image, human contribution and AI
        disclosure.
      </p>
      <ol className="capture-steps" aria-label="Registration stages">
        <li aria-current="step">Capture &amp; details</li>
        <li>Confirm registration</li>
        <li>Prepare recognition</li>
      </ol>
      <CreationEditor state={state} records={props.records} />
      <CreationOutcome state={state} />
    </section>
  );
}

function CreationEditor({
  state,
  records,
}: {
  state: CreationState;
  records: () => void;
}) {
  const { draft, mutation, saved, allowed, submit } = state;
  return (
    <form
      aria-label="System Capture"
      onSubmit={(event) => {
        event.preventDefault();
        submit();
      }}
    >
      <fieldset disabled={saved || mutation.state.phase === "pending"}>
        <legend className="visually-hidden">Persona details</legend>
        <CreationLayout state={state} />
        <WriteConfirmation
          value={draft.fields.confirm ?? ""}
          change={(value) => draft.change("confirm", value)}
        >
          I confirm these details and approve this portrait as the first
          reference.
        </WriteConfirmation>
      </fieldset>
      <div className="creation-actions creation-submit-actions">
        <button className="primary" disabled={!allowed}>
          Register persona
        </button>
        <CaptureHelper
          values={draft.fields}
          photo={state.photo}
          connected={state.connected}
        />
        <button
          type="button"
          className="text-button creation-back"
          onClick={records}
        >
          Back to records
        </button>
        {creationStatus(state) && (
          <p className="help" role="status">
            {creationStatus(state)}
          </p>
        )}
      </div>
    </form>
  );
}

function CreationLayout({ state }: { state: CreationState }) {
  return (
    <div className="creation-layout">
      <PersonaPhotoEditor photo={state.photo} prominent />
      <section className="creation-details" aria-label="Persona details">
        <h2>Persona details</h2>
        <CreationFields
          fields={state.draft.fields}
          change={state.draft.change}
        />
      </section>
    </div>
  );
}

function creationStatus({ saved, blocked, connected }: CreationState) {
  if (saved) return "Save confirmed. This draft cannot be submitted again.";
  if (blocked)
    return "Access was denied. Your draft remains in this tab; restore access before saving.";
  return connected
    ? null
    : "Draft kept in this tab. Saving requires a connected, authorized workspace session.";
}

function CreationOutcome({ state }: { state: CreationState }) {
  const { draft, mutation, connected } = state;
  return (
    <>
      <WriteFeedback
        {...mutation}
        mayRetry={connected && mutation.mayRetry}
        retry={() => {
          if (connected) void mutation.retry();
        }}
      />
      {mutation.state.phase === "conflict" && (
        <div className="saved-feedback">
          <p>
            Check Records for an existing record before preparing another
            request. Your draft is retained.
          </p>
          <button
            type="button"
            className="secondary"
            onClick={() => {
              draft.change("confirm", "");
              mutation.prepare();
            }}
          >
            I checked Records; prepare a new request
          </button>
        </div>
      )}
    </>
  );
}
