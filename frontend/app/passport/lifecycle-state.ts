import { useContext, useMemo } from "react";
import { PersonaMutation } from "../../lib/persona-mutation";
import { parseAppendLifecycle } from "../../lib/persona-lifecycle-contracts";
import type { LifecycleGateway } from "../../lib/persona-lifecycle";
import {
  WriteDraftContext,
  useWriteLifecycle,
  type WriteCommand,
} from "./prepared-write-state";

export function useLifecycleMutation(
  gateway: LifecycleGateway,
  key: string,
  denied: () => void,
) {
  const store = useContext(WriteDraftContext);
  const mutation = useMemo(
    () =>
      new PersonaMutation<WriteCommand, unknown>(
        (command, signal) =>
          gateway.append(parseAppendLifecycle(command), signal),
        store?.get(key)?.checkpoint ?? undefined,
        parseAppendLifecycle,
      ),
    [gateway, key, store],
  );
  return useWriteLifecycle(mutation, store, key, denied);
}
