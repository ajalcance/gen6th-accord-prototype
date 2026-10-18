import { useState } from "react";
import type { PersonaVersion } from "../../lib/persona-contracts";
import type { SavedPersonaSource } from "./saved-source";
import { usePreparedWrite, useWriteDraft } from "./prepared-write-state";
import {
  writeKey,
  WriteFeedback,
  SubmitWriteForm,
  TextFields,
  uncertain,
  type TextFieldSpec,
} from "./prepared-write-common";
import VersionReconciliation from "./prepared-version-reconciliation";
import { usePersonaPhoto } from "./persona-photo-state";
import PersonaPhotoEditor from "./persona-photo-editor";

type Props = {
  source: SavedPersonaSource;
  version: PersonaVersion;
  denied: () => void;
};
const fields: TextFieldSpec[] = [
  {
    field: "name",
    label: "Saved draft name",
    max: 80,
    multiline: false,
    placeholder: "Name this persona record.",
  },
  {
    field: "biography",
    label: "Saved draft biography",
    placeholder: "Describe the persona and its intended context.",
  },
  {
    field: "human_contribution",
    label: "Saved draft contribution",
    placeholder:
      "Describe the human work, such as writing, direction or illustration.",
  },
  {
    field: "ai_disclosure",
    label: "Saved draft AI disclosure",
    placeholder: "Describe any AI use, or state that none was used.",
  },
];
function useVersionWrite({ source, version, denied }: Props) {
  const key = writeKey(source, "save", version.persona_id);
  const draft = useWriteDraft(key, {
    ...version.content,
    confirm: "",
  });
  const mutation = usePreparedWrite(source.writeGateway!, "save", key, denied);
  const photo = usePersonaPhoto(
    source.photos?.workspaceId === source.workspaceId
      ? source.photos
      : undefined,
    () => draft.change("confirm", ""),
    denied,
  );
  const [base, setBase] = useState(version);
  function submit() {
    void mutation
      .submit({
        request_id: crypto.randomUUID(),
        persona_id: base.persona_id,
        expected_revision: base.revision,
        content: {
          name: draft.fields.name,
          biography: draft.fields.biography,
          human_contribution: draft.fields.human_contribution,
          ai_disclosure: draft.fields.ai_disclosure,
        },
        ...(photo.change ? { photo: photo.change } : {}),
      })
      .then((result) => {
        if (result?.phase === "succeeded") photo.choose(null);
      });
  }
  function reconcile(latest: PersonaVersion) {
    setBase(latest);
    draft.change("confirm", "");
    mutation.prepare();
  }
  return { draft, mutation, photo, base, submit, reconcile };
}
export default function PreparedVersionWrite(props: Props) {
  const { draft, mutation, photo, base, submit, reconcile } =
    useVersionWrite(props);
  return (
    <section aria-label="Save a version">
      <h3>Save a new version</h3>
      <p className="help">
        Based on version {base.revision}. Saving creates a new immutable version
        and requires new independent review.
      </p>
      <SubmitWriteForm
        draft={draft}
        mutation={mutation}
        ready={
          photo.ready &&
          fields.every((spec) => draft.fields[spec.field]?.trim())
        }
        label="Save version"
        confirmation="I have reviewed this draft and want a new saved version."
        submit={submit}
      >
        <TextFields specs={fields} draft={draft} />
        <PersonaPhotoEditor photo={photo} editing />
      </SubmitWriteForm>
      <WriteFeedback {...mutation} retry={() => void mutation.retry()} />
      <VersionReconciliation
        source={props.source}
        personaId={props.version.persona_id}
        fields={draft.fields}
        blocked={uncertain(mutation.state) || mutation.requiresResolution}
        use={reconcile}
        denied={props.denied}
      />
    </section>
  );
}
