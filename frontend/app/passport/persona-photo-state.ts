import { useEffect, useRef, useState } from "react";
import type { PhotoChange } from "../../lib/persona-contracts";
import {
  preparePhoto,
  parsePhotoReceipt,
  type PhotoUploadCommand,
  type PhotoGateway,
} from "../../lib/persona-photos";
import { ApiError } from "../../lib/api-client";
import { requireContract } from "../../lib/persona-validation";

/** File bytes and inspection receipts live only on this mounted, session-keyed screen. */
export function usePersonaPhoto(
  photos: PhotoGateway | undefined,
  changed: () => void,
  denied?: () => void,
) {
  const [file, setFile] = useState<File | null>(null);
  const [removed, setRemoved] = useState(false);
  const [preview, setPreview] = useState<string | null>(null);
  const previewUrl = useRef<string | null>(null);
  const [state, setState] = useState<{
    phase: string;
    message: string;
    id?: string;
    sha256?: string;
  }>({
    phase: "idle",
    message: "",
  });
  const intent = useRef<PhotoUploadCommand | null>(null);
  const current = useRef(0),
    controller = useRef<AbortController | null>(null);
  useEffect(
    () => () => {
      current.current++;
      controller.current?.abort();
      if (previewUrl.current) URL.revokeObjectURL(previewUrl.current);
    },
    [photos],
  );
  function choose(value: File | null) {
    current.current++;
    controller.current?.abort();
    intent.current = null;
    changed();
    if (previewUrl.current) URL.revokeObjectURL(previewUrl.current);
    previewUrl.current = null;
    setPreview(null);
    if (
      value &&
      (!["image/png", "image/jpeg"].includes(value.type) ||
        value.size < 1 ||
        value.size > 10485760)
    ) {
      setState({
        phase: "failed",
        message: "Choose a PNG or JPEG up to 10 MB.",
      });
      setFile(null);
      return;
    }
    setFile(value);
    if (value) {
      previewUrl.current = URL.createObjectURL(value);
      setPreview(previewUrl.current);
    }
    setRemoved(false);
    setState({ phase: "idle", message: "" });
  }
  async function check() {
    if (!photos || !file || state.phase === "pending") return;
    const turn = ++current.current,
      abort = new AbortController();
    controller.current = abort;
    setState({
      phase: "pending",
      message: "Uploading photo and scanning for safety…",
    });
    try {
      const command = intent.current ?? (await preparePhoto(file));
      if (turn !== current.current) return;
      intent.current = command;
      const receipt = parsePhotoReceipt(
        await photos.upload(command, abort.signal),
      );
      requireContract(
        receipt.workspace_id === photos.workspaceId &&
          receipt.request_id === command.request_id &&
          receipt.sha256 === command.sha256,
      );
      if (turn !== current.current || abort.signal.aborted) return;
      setState({
        phase: "checked",
        id: receipt.id,
        sha256: receipt.sha256,
        message:
          "Scan complete. Save the persona to attach the photo to this version.",
      });
    } catch (error) {
      if (turn !== current.current) return;
      const accessDenied =
        error instanceof ApiError &&
        (error.status === 401 || error.status === 403);
      setState({
        phase: "failed",
        message: accessDenied
          ? "Photo access denied. Restore your session before scanning this photo."
          : "Photo scan could not be confirmed. Your text is retained. Retry the scan for this photo, or discard this selection.",
      });
      if (accessDenied) denied?.();
    }
  }
  function cancel() {
    current.current++;
    controller.current?.abort();
    setState({
      phase: "failed",
      message:
        "Stopped waiting. Retry the scan for this photo to confirm the upload.",
    });
  }
  function remove() {
    choose(null);
    setRemoved(true);
    setState({
      phase: "idle",
      message: "Photo removal will be saved in a new version.",
    });
  }
  const change: PhotoChange | undefined = removed
    ? { action: "remove", upload_id: null }
    : state.phase === "checked" && state.id
      ? { action: "attach", upload_id: state.id }
      : undefined;
  return {
    file,
    preview,
    state,
    choose,
    check,
    cancel,
    remove,
    change,
    ready: !file || state.phase === "checked",
    available: !!photos,
  };
}
export type PersonaPhotoState = ReturnType<typeof usePersonaPhoto>;
