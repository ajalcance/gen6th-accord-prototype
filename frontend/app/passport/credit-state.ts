import { useContext, useMemo } from "react";
import { PersonaMutation } from "../../lib/persona-mutation";
import {
  parseConfirmCredit,
  parseSaveCredits,
  type CreditGateway,
} from "../../lib/persona-credits";
import { requireContract } from "../../lib/persona-validation";
import {
  WriteDraftContext,
  useWriteLifecycle,
  type WriteCommand,
} from "./prepared-write-state";

export function useCreditMutation(
  gateway: CreditGateway,
  key: string,
  denied: () => void,
  expectedActor?: string | null,
) {
  const store = useContext(WriteDraftContext);
  const mutation = useMemo(
    () =>
      new PersonaMutation<WriteCommand, unknown>(
        async (command, signal) => {
          if ("profile_id" in command) {
            const result = await gateway.confirm(
              parseConfirmCredit(command),
              signal,
            );
            requireContract(result.actor_ref === expectedActor);
            return result;
          }
          return gateway.save(parseSaveCredits(command), signal);
        },
        store?.get(key)?.checkpoint ?? undefined,
        (command) =>
          "profile_id" in command
            ? parseConfirmCredit(command)
            : parseSaveCredits(command),
      ),
    [gateway, key, store, expectedActor],
  );
  return useWriteLifecycle(mutation, store, key, denied);
}
