import type { CaptureMetadata } from "../../lib/persona-captures";
import type { ReferenceProps } from "./saved-captures";
import { useWriteDraft, usePreparedWrite } from "./prepared-write-state";
import { writeKey, unresolved } from "./prepared-write-common";
import { usePersonaPhoto } from "./persona-photo-state";
import { useReferencePreviews } from "./reference-previews";

type Props = ReferenceProps & { references: CaptureMetadata[] };
function useReferenceDraft({ source, version, denied, references }: Props) {
  const key = writeKey(source, "save", `${version.persona_id}:references`);
  const draft = useWriteDraft(key, { ids: "", confirm: "" });
  const mutation = usePreparedWrite(source.writeGateway!, "save", key, denied);
  const ids: string[] = draft.fields.ids
    ? JSON.parse(draft.fields.ids)
    : references.map((item) => item.portrait_id);
  const blocked =
    unresolved(mutation.state) ||
    mutation.requiresResolution ||
    mutation.state.phase === "conflict";
  const newerBase =
    mutation.state.phase === "conflict" &&
    mutation.intent &&
    "expected_revision" in mutation.intent &&
    mutation.intent.expected_revision < version.revision;
  return { draft, mutation, ids, blocked, newerBase };
}
export function useReferenceEditor(props: Props) {
  const state = useReferenceDraft(props);
  const { draft, mutation, ids } = state;
  const { source, version, denied } = props;
  const previews = useReferencePreviews();
  const photo = usePersonaPhoto(
    source.photos?.workspaceId === source.workspaceId
      ? source.photos
      : undefined,
    () => draft.change("confirm", ""),
    denied,
  );
  function change(next: string[]) {
    previews.retain(next);
    draft.change("ids", JSON.stringify(next));
  }
  function add() {
    const id = photo.state.id;
    if (!id || ids.length >= 8) return;
    previews.add(id, photo.file);
    photo.choose(null);
    if (!ids.includes(id)) change([...ids, id]);
  }
  function submit() {
    void mutation.submit({
      request_id: crypto.randomUUID(),
      persona_id: version.persona_id,
      expected_revision: version.revision,
      content: version.content,
      photo: { action: "keep", upload_id: null },
      references: { action: "replace", upload_ids: ids },
    });
  }
  function prepare() {
    draft.change("confirm", "");
    mutation.prepare();
  }
  return { ...state, props, previews, photo, change, add, submit, prepare };
}
export type ReferenceEditorState = ReturnType<typeof useReferenceEditor>;
