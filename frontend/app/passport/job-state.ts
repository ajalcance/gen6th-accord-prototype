import { useContext, useMemo } from "react";
import { PersonaMutation } from "../../lib/persona-mutation";
import {
  parseFaceCommand,
  parseJobUpdate,
} from "../../lib/persona-job-contracts";
import type { RuntimeGateway } from "../../lib/persona-runtime";
import type { FaceSubject } from "../../lib/persona-faces";
import {
  WriteDraftContext,
  useWriteLifecycle,
  type WriteCommand,
} from "./prepared-write-state";

export function useJobMutation(
  gateway: RuntimeGateway,
  key: string,
  subject: FaceSubject,
  denied: () => void,
  update = false,
) {
  const store = useContext(WriteDraftContext);
  const mutation = useMemo(
    () =>
      new PersonaMutation<WriteCommand, unknown>(
        (command, signal) =>
          update
            ? gateway.update(parseJobUpdate(command), subject, signal)
            : gateway.enqueue(parseFaceCommand(command), signal),
        store?.get(key)?.checkpoint ?? undefined,
        (command) =>
          update ? parseJobUpdate(command) : parseFaceCommand(command),
      ),
    [gateway, key, store, subject, update],
  );
  return useWriteLifecycle(mutation, store, key, denied);
}
