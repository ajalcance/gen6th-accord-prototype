/** Unactivated record writes. A reviewed bootstrap must explicitly inject this transport. */
import { apiClient } from "./api-client";
import {
  PersonaDisconnectedError,
  type PersonaOperation,
  type PersonaTransport,
} from "./persona-gateway";
import { uuid } from "./persona-validation";

const paths: Partial<Record<PersonaOperation, string>> = {
  save: "/versions/save",
  review: "/reviews/record",
  offer: "/campaigns/offer",
  decide: "/campaigns/decide",
};
export function personaPreparedWriteTransport(): PersonaTransport {
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
