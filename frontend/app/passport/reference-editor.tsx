import { useMemo } from "react";
import type { CaptureMetadata } from "../../lib/persona-captures";
import type { ReferenceProps } from "./saved-captures";
import { SubmitWriteForm, WriteFeedback } from "./prepared-write-common";
import { useCaptureProfile } from "./capture-status";
import PersonaPhotoEditor from "./persona-photo-editor";
import {
  useReferenceEditor,
  type ReferenceEditorState,
} from "./reference-editor-state";
import ReferenceSelection from "./reference-selection";

type Props = ReferenceProps & { references: CaptureMetadata[] };
export default function ReferenceEditor(props: Props) {
  const editor = useReferenceEditor(props);
  return (
    <section className="reference-set" aria-label="Approve reference set">
      <p className="help">
        Save up to eight checked portraits in a new version. Replacing the
        display photo does not change this reference set. Clear all to withdraw
        the set from the new version.
      </p>
      <ReferenceForm editor={editor} />
      <ReferenceFeedback editor={editor} />
    </section>
  );
}
function ReferenceForm({ editor }: { editor: ReferenceEditorState }) {
  const { draft, mutation, photo, blocked, ids, change, previews, submit } =
    editor;
  return (
    <SubmitWriteForm
      draft={draft}
      mutation={mutation}
      ready={!photo.file && !blocked}
      label="Save reference version"
      confirmation="I approve this ordered reference set for a new persona version."
      submit={submit}
    >
      <fieldset disabled={blocked}>
        <ReferenceSelection
          ids={ids}
          change={change}
          previews={previews.previews}
        />
        <ReferenceUpload editor={editor} />
      </fieldset>
    </SubmitWriteForm>
  );
}
function ReferenceUpload({ editor }: { editor: ReferenceEditorState }) {
  const { props, photo, ids, add } = editor;
  return (
    <>
      {ids.length < 8 && (
        <PersonaPhotoEditor photo={photo} editing referenceOnly />
      )}
      {photo.state.id && (
        <AddCheckedReference
          source={props.source}
          id={photo.state.id}
          digest={photo.state.sha256}
          denied={props.denied}
          add={add}
        />
      )}
    </>
  );
}
function ReferenceFeedback({ editor }: { editor: ReferenceEditorState }) {
  const { mutation, newerBase, prepare, props } = editor;
  return (
    <>
      <WriteFeedback {...mutation} retry={() => void mutation.retry()} />
      {mutation.state.phase === "conflict" && (
        <p role="alert">
          Reopen the latest saved record before preparing another reference
          version. Your authored selection remains in this tab.
        </p>
      )}
      {newerBase && (
        <button type="button" className="secondary" onClick={prepare}>
          Prepare references for version {props.version.revision}
        </button>
      )}
      {mutation.state.phase === "succeeded" && (
        <p>
          Reopen saved records to inspect the new immutable reference version.
        </p>
      )}
    </>
  );
}
function AddCheckedReference({
  source,
  id,
  digest,
  denied,
  add,
}: {
  source: ReferenceProps["source"];
  id: string;
  digest?: string;
  denied: () => void;
  add: () => void;
}) {
  const command = useMemo(() => ({ upload_id: id, version_id: null }), [id]);
  const { state } = useCaptureProfile(source, command, digest, denied);
  return (
    <button
      type="button"
      className="secondary"
      disabled={state.phase !== "ready" || !state.value.capture}
      onClick={add}
    >
      Add checked reference
    </button>
  );
}
