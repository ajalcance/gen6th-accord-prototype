import { useState } from "react";
import {
  parseCreditContent,
  type Credit,
  type CreditGateway,
  type CreditProfile,
} from "../../lib/persona-credits";
import type { RecordWorkspaceProps } from "./record-journey";
import { useWriteDraft } from "./prepared-write-state";
import { useCreditMutation } from "./credit-state";
import {
  SubmitWriteForm,
  WriteFeedback,
  ReloadWrite,
} from "./prepared-write-common";
import CreditFields from "./credit-fields";

type Props = RecordWorkspaceProps & {
  gateway: CreditGateway;
  profile: CreditProfile;
  reload: () => void;
};
export default function CreditEditor(props: Props) {
  const [open, setOpen] = useState(false);
  return (
    <div>
      <button
        className="secondary"
        aria-expanded={open}
        onClick={() => setOpen(!open)}
      >
        {open ? "Close credit editor" : "Edit aliases & credits"}
      </button>
      {open && <CreditForm {...props} />}
    </div>
  );
}
function useCreditDraft(props: Props) {
  const key = `${props.source.workspaceId}:${props.source.sessionKey}:credit-save:${props.version.version_id}`;
  const draft = useWriteDraft(key, {
    aliases: props.profile.snapshot?.content.aliases.join("\n") ?? "",
    credits: JSON.stringify(props.profile.snapshot?.content.credits ?? []),
  });
  const mutation = useCreditMutation(props.gateway, key, props.denied);
  const credits: Credit[] = JSON.parse(draft.fields.credits || "[]");
  const aliases = draft.fields.aliases
    .split("\n")
    .map((value) => value.trim())
    .filter(Boolean);
  let content = null;
  try {
    content = parseCreditContent({ aliases, credits });
  } catch {
    /* Draft stays editable until valid. */
  }
  return {
    draft,
    mutation,
    credits,
    content,
    changeCredits: (rows: Credit[]) =>
      draft.change("credits", JSON.stringify(rows)),
  };
}
function CreditForm(props: Props) {
  const { draft, mutation, credits, content, changeCredits } =
    useCreditDraft(props);
  return (
    <div className="credit-editor">
      <p className="help">
        Only the performer owner can record changes. A replacement declaration
        requires contributors to confirm again. Credits stay within this
        workspace.
      </p>
      <SubmitWriteForm
        draft={draft}
        mutation={mutation}
        ready={content !== null}
        label="Record aliases & credits"
        confirmation="I reviewed these aliases and contributor declarations."
        submit={() => {
          if (content)
            void mutation.submit({
              request_id: crypto.randomUUID(),
              version_id: props.version.version_id,
              expected_previous_id: props.profile.snapshot?.id ?? null,
              content,
            });
        }}
      >
        <CreditFormFields
          {...props}
          draft={draft}
          credits={credits}
          changeCredits={changeCredits}
          valid={content !== null}
        />
      </SubmitWriteForm>
      <WriteFeedback {...mutation} retry={() => void mutation.retry()} />
      <ReloadWrite
        draft={draft}
        mutation={mutation}
        loading={false}
        reload={props.reload}
        label="Reload credit receipts"
      />
    </div>
  );
}
function CreditFormFields(
  props: Props & {
    draft: ReturnType<typeof useWriteDraft>;
    credits: Credit[];
    changeCredits: (rows: Credit[]) => void;
    valid: boolean;
  },
) {
  return (
    <>
      <label>
        Other names
        <textarea
          maxLength={648}
          placeholder="One alias per line · up to 8"
          value={props.draft.fields.aliases}
          onChange={(event) =>
            props.draft.change("aliases", event.target.value)
          }
        />
      </label>
      <CreditFields
        source={props.source}
        versionId={props.version.version_id}
        credits={props.credits}
        change={props.changeCredits}
      />
      {!props.valid && (
        <p role="status">
          Use distinct aliases of up to 80 characters and complete each
          contributor’s name and role.
        </p>
      )}
    </>
  );
}
