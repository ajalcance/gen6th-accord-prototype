import type { ReactNode } from "react";
import Image from "next/image";
import type { SavedPersonaSource } from "./saved-source";
import Icon from "./icons";
import { useSavedPortrait } from "./use-saved-portrait";

export default function SavedPhoto({
  source,
  versionId,
  name,
  children,
}: {
  source: SavedPersonaSource | null;
  versionId: string;
  name: string;
  children?: ReactNode;
}) {
  const state = useSavedPortrait(source, versionId);
  return (
    <span className="saved-portrait">
      <span className="saved-portrait-heading">
        <span className="saved-photo">
          {state.url ? (
            <Image
              src={state.url}
              alt={`Saved photo of ${name}`}
              width={96}
              height={96}
              unoptimized
            />
          ) : (
            <Icon name="passport" size={22} />
          )}
        </span>
        {children}
      </span>
      {state.phase !== "present" && (
        <span className="portrait-status" role="status">
          {state.phase === "missing"
            ? "Incomplete — portrait required"
            : state.phase === "loading"
              ? "Checking portrait…"
              : "Portrait status unavailable"}
        </span>
      )}
    </span>
  );
}
