/** Prepared same-origin read transport. Never used until a session-bound source is injected. */
import { apiClient } from "./api-client";
import {
  PersonaDisconnectedError,
  type PersonaTransport,
} from "./persona-gateway";
import { uuid } from "./persona-validation";

export function personaReadTransport(): PersonaTransport {
  return async (operation, workspace, command, signal) => {
    const id = uuid(workspace);
    const paths = {
      gallery: `/api/workspaces/${id}/personas/query`,
      load: `/api/workspaces/${id}/personas/versions/query`,
    };
    if (operation !== "gallery" && operation !== "load")
      throw new PersonaDisconnectedError();
    return apiClient.post<unknown>(paths[operation], command, {
      signal,
      credentials: "same-origin",
      mode: "same-origin",
      cache: "no-store",
      redirect: "error",
      retries: 0,
    });
  };
}
