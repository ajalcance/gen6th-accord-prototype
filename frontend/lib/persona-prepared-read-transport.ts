/** Unactivated governance reads. Only a trusted bootstrap may inject this transport. */
import { apiClient } from "./api-client";
import {
  PersonaDisconnectedError,
  type PersonaOperation,
  type PersonaTransport,
} from "./persona-gateway";
import { uuid } from "./persona-validation";

const paths: Partial<Record<PersonaOperation, string>> = {
  gallery: "/query",
  load: "/versions/query",
  versionHistory: "/versions/history/query",
  reviewHistory: "/reviews/history/query",
  campaignOffers: "/campaigns/query",
  campaignHistory: "/campaigns/history/query",
  campaignStatus: "/campaigns/status/query",
  evidenceList: "/evidence/query",
  evidenceStatus: "/evidence/status/query",
  workflowEvidence: "/workflow/evidence/query",
};
export function personaPreparedReadTransport(): PersonaTransport {
  return async (operation, workspace, command, signal) => {
    const id = uuid(workspace),
      path = paths[operation];
    if (!path) throw new PersonaDisconnectedError();
    return apiClient.post<unknown>(
      `/api/workspaces/${id}/personas${path}`,
      command,
      {
        signal,
        credentials: "same-origin",
        mode: "same-origin",
        cache: "no-store",
        redirect: "error",
        retries: 0,
      },
    );
  };
}
