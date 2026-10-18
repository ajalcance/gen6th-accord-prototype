"use client";

import { useEffect, useState } from "react";
import { apiClient } from "../../lib/api-client";
import { personaGateway } from "../../lib/persona-gateway";
import { personaPreparedReadTransport } from "../../lib/persona-prepared-read-transport";
import { personaPreparedWriteTransport } from "../../lib/persona-prepared-write-transport";
import { uuid } from "../../lib/persona-validation";
import { photoGateway } from "../../lib/persona-photos";
import { portraitSearchGateway } from "../../lib/persona-portrait-search";
import { captureGateway } from "../../lib/persona-captures";
import { faceGateway } from "../../lib/persona-faces";
import { similarityGateway } from "../../lib/persona-similarity";
import { investigationGateway } from "../../lib/persona-investigations";
import { passportGateway } from "../../lib/persona-passports";
import { runtimeGateway } from "../../lib/persona-runtime";
import { evidenceGateway } from "../../lib/persona-evidence";
import { assetRegistry } from "../../lib/persona-assets";
import { publicationGateway } from "../../lib/persona-publications";
import { creditGateway } from "../../lib/persona-credits";
import { lifecycleGateway } from "../../lib/persona-lifecycle";
import { assistantGateway } from "../../lib/persona-assistant";
import type { SavedPersonaSource } from "./saved-source";
import PassportStudio from "./studio";

export function sessionSource(raw: unknown): SavedPersonaSource {
  if (!raw || typeof raw !== "object")
    throw new Error("Invalid workspace session");
  const data = raw as Record<string, unknown>;
  if (
    Object.keys(data).sort().join() !==
      "session_key,workspace_id,workspace_label" ||
    typeof data.session_key !== "string" ||
    !data.session_key ||
    data.session_key.length > 64 ||
    typeof data.workspace_label !== "string" ||
    !data.workspace_label ||
    data.workspace_label.length > 80
  )
    throw new Error("Invalid workspace session");
  const workspaceId = uuid(data.workspace_id);
  return {
    workspaceId,
    workspaceLabel: data.workspace_label,
    sessionKey: data.session_key,
    gateway: personaGateway(workspaceId, personaPreparedReadTransport()),
    writeGateway: personaGateway(workspaceId, personaPreparedWriteTransport()),
    photos: photoGateway(workspaceId),
    portraitSearch: portraitSearchGateway(workspaceId),
    captures: captureGateway(workspaceId),
    faces: faceGateway(workspaceId),
    similarity: similarityGateway(workspaceId),
    investigations: investigationGateway(workspaceId),
    passports: passportGateway(workspaceId),
    runtime: runtimeGateway(workspaceId),
    evidence: evidenceGateway(workspaceId),
    assetRegistry: assetRegistry(workspaceId),
    publications: publicationGateway(workspaceId),
    credits: creditGateway(workspaceId),
    lifecycle: lifecycleGateway(workspaceId),
    assistant: assistantGateway(workspaceId),
  };
}

function useConnectedSource(enabled: boolean) {
  const [source, setSource] = useState<SavedPersonaSource | null>(null);
  useEffect(() => {
    if (!enabled) return;
    const controller = new AbortController();
    apiClient
      .get<unknown>("/api/auth/session", {
        signal: controller.signal,
        credentials: "same-origin",
        mode: "same-origin",
        cache: "no-store",
        redirect: "error",
        retries: 0,
      })
      .then((data) => {
        if (!controller.signal.aborted) setSource(sessionSource(data));
      })
      .catch(() => {
        if (!controller.signal.aborted) setSource(null);
      });
    return () => controller.abort();
  }, [enabled]);
  return [source, setSource] as const;
}

async function signOut(clear: () => void, setError: (message: string) => void) {
  clear();
  try {
    await apiClient.post(
      "/api/auth/logout",
      {},
      {
        credentials: "same-origin",
        mode: "same-origin",
        cache: "no-store",
        redirect: "error",
        retries: 0,
      },
    );
    setError("");
  } catch {
    setError("Server sign-out could not be confirmed. Retry sign-out.");
  }
}

function signIn() {
  // OIDC uses a backend redirect and a full-document navigation on the current origin.
  window.location.assign(
    new URL("/api/auth/login", window.location.origin).href,
  );
}

export default function ConnectedWorkspace({ enabled }: { enabled: boolean }) {
  const [source, setSource] = useConnectedSource(enabled);
  const [error, setError] = useState("");
  return (
    <>
      <PassportStudio
        savedSource={source}
        sessionAction={
          enabled
            ? {
                label: source || error ? "Sign out" : "Sign in",
                run:
                  source || error
                    ? () => {
                        void signOut(() => setSource(null), setError);
                      }
                    : signIn,
              }
            : undefined
        }
      />
      {error && <p role="alert">{error}</p>}
    </>
  );
}
