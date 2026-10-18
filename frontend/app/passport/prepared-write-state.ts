import {
  createContext,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";
import type {
  DecisionCommand,
  OfferCommand,
  ReviewCommand,
  SaveCommand,
} from "../../lib/persona-contracts";
import {
  PersonaMutation,
  type MutationCheckpoint,
  type MutationState,
} from "../../lib/persona-mutation";
import {
  PersonaDisconnectedError,
  type PersonaGateway,
} from "../../lib/persona-gateway";
import {
  parseDecisionCommand,
  parseOffer,
  parseReviewCommand,
  parseSave,
} from "../../lib/persona-commands";
import type { FaceCommand } from "../../lib/persona-faces";
import type { JobUpdate } from "../../lib/persona-job-contracts";
import type { SaveCredits, ConfirmCredit } from "../../lib/persona-credits";
import type { AppendLifecycle } from "../../lib/persona-lifecycle-contracts";

export type WriteKind = "save" | "review" | "offer" | "decide";
export type WriteCommand =
  | SaveCommand
  | ReviewCommand
  | OfferCommand
  | DecisionCommand
  | FaceCommand
  | JobUpdate
  | SaveCredits
  | ConfirmCredit
  | AppendLifecycle;
type Entry = {
  fields: Record<string, string>;
  checkpoint: MutationCheckpoint<WriteCommand> | null;
};
/** User-entered drafts/intents only, in memory. Never store fetched records or receipts. */
export type WriteDraftStore = Map<string, Entry>;
export const WriteDraftContext = createContext<WriteDraftStore | null>(null);

export function useWriteDraft(key: string, initial: Record<string, string>) {
  const store = useContext(WriteDraftContext);
  const [fields, setFields] = useState<Record<string, string>>(() => ({
    ...(store?.get(key)?.fields ?? initial),
    confirm: "",
  }));
  function change(field: string, value: string) {
    const next = {
      ...fields,
      [field]: value,
      ...(field === "confirm" ? {} : { confirm: "" }),
    };
    setFields(next);
    store?.set(key, {
      fields: next,
      checkpoint: store.get(key)?.checkpoint ?? null,
    });
  }
  function changeFields(values: Record<string, string>) {
    const next = { ...fields, ...values, confirm: "" };
    setFields(next);
    store?.set(key, {
      fields: next,
      checkpoint: store.get(key)?.checkpoint ?? null,
    });
  }
  return { fields, change, changeFields, store };
}

function send(
  gateway: PersonaGateway | null,
  kind: WriteKind,
  command: WriteCommand,
  signal: AbortSignal,
) {
  if (!gateway) throw new PersonaDisconnectedError();
  switch (kind) {
    case "save":
      return gateway.save(parseSave(command), signal);
    case "review":
      return gateway.review(parseReviewCommand(command), signal);
    case "offer":
      return gateway.offer(parseOffer(command), signal);
    case "decide":
      return gateway.decide(parseDecisionCommand(command), signal);
  }
}

function normalize(kind: WriteKind, command: WriteCommand): WriteCommand {
  switch (kind) {
    case "save":
      return parseSave(command);
    case "review":
      return parseReviewCommand(command);
    case "offer":
      return parseOffer(command);
    case "decide":
      return parseDecisionCommand(command);
  }
}

export function usePreparedWrite(
  gateway: PersonaGateway | null,
  kind: WriteKind,
  key: string,
  denied: () => void,
) {
  const store = useContext(WriteDraftContext);
  const mutation = useMemo(
    () =>
      new PersonaMutation<WriteCommand, unknown>(
        (command, signal) => send(gateway, kind, command, signal),
        store?.get(key)?.checkpoint ?? undefined,
        (command) => normalize(kind, command),
      ),
    [gateway, kind, key, store],
  );
  return useWriteLifecycle(mutation, store, key, denied);
}

function useWritePublication(mutation: PersonaMutation<WriteCommand, unknown>) {
  const [snapshot, setSnapshot] = useState({
    owner: mutation,
    value: mutation.snapshot,
  });
  const state =
    snapshot.owner === mutation ? snapshot.value : mutation.snapshot;
  const publish = (value: MutationState<unknown>) =>
    setSnapshot({ owner: mutation, value });
  return { state, publish };
}

export function useWriteLifecycle(
  mutation: PersonaMutation<WriteCommand, unknown>,
  store: WriteDraftStore | null,
  key: string,
  denied: () => void,
) {
  const { state, publish } = useWritePublication(mutation);
  const alive = useRef(false),
    turn = useRef(0);
  useEffect(() => {
    alive.current = true;
    return () => {
      alive.current = false;
      turn.current += 1;
      mutation.cancel();
      remember(store, key, mutation);
    };
  }, [mutation, store, key]);
  async function run(start: () => Promise<MutationState<unknown>>) {
    const current = ++turn.current,
      promise = start();
    publish(mutation.snapshot);
    remember(store, key, mutation);
    const result = await promise;
    if (!alive.current || current !== turn.current) return;
    remember(store, key, mutation);
    publish(result);
    if (result.phase === "denied") denied();
    return result;
  }
  function update(action: () => void) {
    action();
    remember(store, key, mutation);
    publish(mutation.snapshot);
  }
  return {
    state,
    requiresResolution: mutation.requiresResolution,
    mayRetry: mutation.canRetry,
    intent: mutation.intent,
    submit: (command: WriteCommand) => run(() => mutation.submit(command)),
    retry: () => run(() => mutation.retry()),
    cancel: () => update(() => mutation.cancel()),
    prepare: () => update(() => mutation.reset()),
  };
}

function remember(
  store: WriteDraftStore | null,
  key: string,
  mutation: PersonaMutation<WriteCommand, unknown>,
) {
  let checkpoint = mutation.checkpoint;
  if (mutation.snapshot.phase === "pending" && mutation.intent) {
    checkpoint = {
      intent: mutation.intent,
      uncertain: true,
      state: {
        phase: "cancelled",
        message:
          "The outcome is uncertain. Restore access and retry the same intent before submitting another action.",
      },
    };
  }
  store?.set(key, { fields: store.get(key)?.fields ?? {}, checkpoint });
}
