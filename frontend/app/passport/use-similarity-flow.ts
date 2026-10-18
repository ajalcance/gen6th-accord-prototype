import { useCallback, useEffect, useRef, useState } from "react";
import {
  preparePhoto,
  type PhotoUploadCommand,
} from "../../lib/persona-photos";
import type {
  QueryReceipt,
  SimilarityPage,
  SimilarityReadiness,
  SearchCommand,
} from "../../lib/persona-similarity-contracts";
import type { SimilarityGateway } from "../../lib/persona-similarity";
import type { SavedPersonaSource } from "./saved-source";
import { usePersonaQuery } from "./use-persona-query";

function useQueryCleanup(gateway: SimilarityGateway | undefined) {
  const identities = useRef(new Set<string>());
  const [status, setStatus] = useState("");
  const clear = useCallback(async () => {
    if (!gateway || !identities.current.size) return;
    setStatus("Clearing server query…");
    let failed = false;
    for (const id of Array.from(identities.current)) {
      try {
        await gateway.clear(id, new AbortController().signal);
        identities.current.delete(id);
      } catch {
        failed = true;
      }
    }
    setStatus(
      failed
        ? "Server clearing is unconfirmed. Retry clearing; encrypted queries expire within ten minutes."
        : "Server query cleared.",
    );
  }, [gateway]);
  useEffect(
    () => () => {
      if (gateway)
        for (const id of identities.current)
          void gateway
            .clear(id, new AbortController().signal)
            .catch(() => undefined);
    },
    [gateway],
  );
  return { identities, clear, status };
}

export function useSimilarityFlow(source: SavedPersonaSource) {
  const gateway =
    source.similarity?.workspaceId === source.workspaceId
      ? source.similarity
      : undefined;
  const readiness = usePersonaQuery<SimilarityReadiness>();
  const preparation = usePersonaQuery<QueryReceipt>();
  const results = usePersonaQuery<SimilarityPage>();
  const cleanup = useQueryCleanup(gateway);
  const inputs = useQueryInputs();
  const { file, setMessage, reset } = inputs;
  const closeQueries = cleanup.clear;
  const clear = useCallback(() => {
    preparation.query.clear();
    results.query.clear();
    reset();
    void closeQueries();
  }, [preparation.query, results.query, closeQueries, reset]);
  const receipt =
    preparation.state.phase === "ready" ? preparation.state.value : null;
  const invalidate = useInvalidate(clear, readiness.query, setMessage);
  useQueryExpiry(receipt, clear, setMessage);
  useAccessLoss(
    [readiness.state.phase, preparation.state.phase, results.state.phase],
    invalidate,
    setMessage,
  );
  const prepare = usePrepareQuery(
    gateway,
    file,
    preparation.query,
    cleanup.identities,
  );
  const search = () => runSearch(gateway, receipt, inputs, results.query);
  return {
    gateway,
    readiness,
    preparation,
    results,
    ...inputs,
    clear,
    invalidate,
    prepare,
    search,
    receipt,
    cleanup,
  };
}

function useInvalidate(
  clear: () => void,
  readiness: import("../../lib/persona-query").PersonaQuery<SimilarityReadiness>,
  message: (value: string) => void,
) {
  return useCallback(() => {
    clear();
    readiness.clear();
    message(
      "Query access expired or is no longer available. Restore studio access and prepare a fresh query.",
    );
  }, [clear, readiness, message]);
}

function runSearch(
  gateway: SimilarityGateway | undefined,
  receipt: QueryReceipt | null,
  inputs: ReturnType<typeof useQueryInputs>,
  query: import("../../lib/persona-query").PersonaQuery<SimilarityPage>,
) {
  const { face, scope, confirmed, previewReady } = inputs;
  if (!gateway || !receipt || face === null || !confirmed || !previewReady)
    return;
  const command = {
    query_id: receipt.query_id,
    request_id: crypto.randomUUID(),
    face_index: face,
    scope,
  };
  void query.run((signal) => gateway.search(command, signal));
}

function useQueryInputs() {
  const [file, setFile] = useState<File | null>(null);
  const [scope, setScope] = useState<SearchCommand["scope"]>("current");
  const [face, setFace] = useState<number | null>(null);
  const [confirmed, setConfirmed] = useState(false);
  const [previewReady, setPreviewReady] = useState(false);
  const [message, setMessage] = useState("");
  const reset = useCallback(() => {
    setFile(null);
    setFace(null);
    setConfirmed(false);
    setPreviewReady(false);
  }, []);
  return {
    file,
    setFile,
    scope,
    setScope,
    face,
    setFace,
    confirmed,
    setConfirmed,
    previewReady,
    setPreviewReady,
    message,
    setMessage,
    reset,
  };
}

function usePrepareQuery(
  gateway: SimilarityGateway | undefined,
  file: File | null,
  query: import("../../lib/persona-query").PersonaQuery<QueryReceipt>,
  ids: React.RefObject<Set<string>>,
) {
  return () => {
    if (!gateway || !file) return;
    let command: PhotoUploadCommand | null = null;
    void query.run(async (signal) => {
      command ??= await preparePhoto(file);
      if (signal.aborted) throw new DOMException("Cancelled", "AbortError");
      ids.current.add(command.request_id);
      return gateway.prepare(command, signal);
    });
  };
}

function useQueryExpiry(
  receipt: QueryReceipt | null,
  clear: () => void,
  message: (value: string) => void,
) {
  useEffect(() => {
    if (!receipt) return;
    const timer = setTimeout(
      () => {
        clear();
        message("Query expired. Prepare a new image query.");
      },
      Math.max(0, Date.parse(receipt.expires_at) - Date.now()),
    );
    return () => clearTimeout(timer);
  }, [receipt, clear, message]);
}

function useAccessLoss(
  phases: string[],
  clear: () => void,
  message: (value: string) => void,
) {
  const denied = phases.includes("denied"),
    expired = phases.includes("expired");
  useEffect(() => {
    if (denied || expired) {
      clear();
      message(
        denied
          ? "Workspace access was lost. Query images and results were cleared."
          : "Query expired or was cleared. Prepare a new image query.",
      );
    }
  }, [denied, expired, clear, message]);
}

export type SimilarityFlow = ReturnType<typeof useSimilarityFlow>;
