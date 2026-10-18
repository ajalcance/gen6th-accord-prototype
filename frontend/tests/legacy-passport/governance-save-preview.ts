/** Isolated save simulation; no server or browser record is written. */
import { ApiError } from "../../lib/api-client";
import type { SaveCommand } from "../../lib/persona-contracts";
import {
  personaGateway,
  PersonaDisconnectedError,
} from "../../lib/persona-gateway";
import { parseSave } from "../../lib/persona-commands";
import { requireContract } from "../../lib/persona-validation";
import {
  EXAMPLE_CLOCK,
  EXAMPLE_PERSONA,
  EXAMPLE_VERSIONS,
  EXAMPLE_WORKSPACE,
  exampleId,
} from "./governance-fixtures";

export type RecoveryScenario = "conflict" | "unavailable" | "denied";

function waitForExample(signal?: AbortSignal): Promise<void> {
  return new Promise((resolve, reject) => {
    if (signal?.aborted) {
      reject(new DOMException("Cancelled", "AbortError"));
      return;
    }
    const abort = () => {
      clearTimeout(timer);
      reject(new DOMException("Cancelled", "AbortError"));
    };
    const timer = setTimeout(() => {
      signal?.removeEventListener("abort", abort);
      resolve();
    }, 150);
    signal?.addEventListener("abort", abort, { once: true });
  });
}

export function saveRecoveryPreview(scenario: RecoveryScenario) {
  let attempts = 0;
  return personaGateway(
    EXAMPLE_WORKSPACE,
    async (operation, workspace, raw, signal) => {
      requireContract(workspace === EXAMPLE_WORKSPACE);
      if (operation !== "save") throw new PersonaDisconnectedError();
      const command: SaveCommand = parseSave(raw);
      requireContract(
        command.persona_id === EXAMPLE_PERSONA &&
          command.expected_revision === 2,
      );
      attempts += 1;
      await waitForExample(signal);
      if (scenario === "conflict")
        throw new ApiError("Example version conflict", 409);
      if (scenario === "denied")
        throw new ApiError("Example permission loss", 403);
      if (attempts === 1) throw new ApiError("Example uncertain outcome", 503);
      return {
        ...EXAMPLE_VERSIONS[0],
        version_id: exampleId(300),
        recorded_at: EXAMPLE_CLOCK,
        content: command.content,
      };
    },
  );
}
