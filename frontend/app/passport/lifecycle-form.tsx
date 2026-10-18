import type { ReactNode } from "react";
import type { LifecycleGateway } from "../../lib/persona-lifecycle";
import {
  parseAppendLifecycle,
  type LifecycleContent,
} from "../../lib/persona-lifecycle-contracts";
import type { RecordWorkspaceProps } from "./record-journey";
import { useWriteDraft } from "./prepared-write-state";
import { useLifecycleMutation } from "./lifecycle-state";
import {
  ReloadWrite,
  SubmitWriteForm,
  WriteFeedback,
  type WriteDraftState,
} from "./prepared-write-common";

export type LifecycleFormProps = RecordWorkspaceProps & {
  gateway: LifecycleGateway;
  reload: () => void;
};
type Props = LifecycleFormProps & {
  actionKey: string;
  previous: string | null;
  initial: Record<string, string>;
  content: (fields: Record<string, string>) => LifecycleContent;
  label: string;
  confirmation: string;
  children: (draft: WriteDraftState) => ReactNode;
};
function useFormIntent(props: Props) {
  const key = `${props.source.workspaceId}:${props.source.sessionKey}:${props.version.version_id}:lifecycle:${props.actionKey}`;
  const draft = useWriteDraft(key, props.initial),
    mutation = useLifecycleMutation(props.gateway, key, props.denied);
  let content: LifecycleContent | null = null;
  try {
    content = parseAppendLifecycle({
      version_id: props.version.version_id,
      request_id: "00000000-0000-4000-8000-000000000001",
      expected_previous_id: props.previous,
      content: props.content(draft.fields),
    }).content;
  } catch {
    /* Keep incomplete draft editable. */
  }
  return { draft, mutation, content };
}
export default function LifecycleForm(props: Props) {
  const { draft, mutation, content } = useFormIntent(props);
  return (
    <div className="workflow-stack">
      <SubmitWriteForm
        draft={draft}
        mutation={mutation}
        ready={content !== null}
        label={props.label}
        confirmation={props.confirmation}
        submit={() => {
          if (content)
            void mutation.submit({
              version_id: props.version.version_id,
              request_id: crypto.randomUUID(),
              expected_previous_id: props.previous,
              content,
            });
        }}
      >
        {props.children(draft)}
        {!content && (
          <p className="help">
            Complete the required fields and include a timezone in dates.
          </p>
        )}
      </SubmitWriteForm>
      <WriteFeedback {...mutation} retry={() => void mutation.retry()} />
      <ReloadWrite
        draft={draft}
        mutation={mutation}
        loading={false}
        reload={props.reload}
        label="Reload lifecycle records"
      />
    </div>
  );
}
