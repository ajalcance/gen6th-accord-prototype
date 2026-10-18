import { useEffect, useState } from "react";
import type { SavedPersonaSource } from "./saved-source";
import type { PhotoGateway } from "../../lib/persona-photos";

type PortraitState = {
  owner: string;
  phase: "present" | "missing" | "unavailable";
  url: string | null;
  provider?: PhotoGateway;
};
const initial: PortraitState = { owner: "", phase: "unavailable", url: null };

export function useSavedPortrait(
  source: SavedPersonaSource | null,
  versionId: string,
) {
  const owner = source
    ? `${source.workspaceId}:${source.sessionKey}:${versionId}`
    : "";
  const photos = source?.photos;
  const available = !!photos && photos.workspaceId === source?.workspaceId;
  const [state, setState] = useState<PortraitState>(initial);
  useEffect(() => {
    if (!available || !photos) return;
    const controller = new AbortController();
    let url: string | null = null;
    void photos
      .thumbnail(versionId, controller.signal)
      .then((blob) => {
        if (controller.signal.aborted) return;
        url = blob ? URL.createObjectURL(blob) : null;
        setState({
          owner,
          url,
          provider: photos,
          phase: blob ? "present" : "missing",
        });
      })
      .catch(() => {
        if (!controller.signal.aborted)
          setState({
            owner,
            url: null,
            provider: photos,
            phase: "unavailable",
          });
      });
    return () => {
      controller.abort();
      if (url) URL.revokeObjectURL(url);
    };
  }, [available, photos, versionId, owner]);
  return available && state.owner === owner && state.provider === photos
    ? state
    : {
        owner,
        url: null,
        phase: available ? ("loading" as const) : ("unavailable" as const),
      };
}
