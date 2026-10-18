import { useEffect, useState } from "react";
import type {
  GalleryPage,
  GalleryQuery,
} from "../../lib/persona-read-contracts";
import { usePersonaQuery } from "./use-persona-query";
import type { SavedPersonaSource } from "./saved-source";

export function useSavedGallery(source: SavedPersonaSource, active: boolean) {
  const { query, state } = usePersonaQuery<GalleryPage>();
  const [search, setSearch] = useState("");
  const [cursors, setCursors] = useState<(string | null)[]>([]);
  const [intent, setIntent] = useState<GalleryQuery>({
    after_persona_id: null,
    limit: 20,
    search: "",
  });
  useEffect(() => {
    if (!active) return;
    void query.run((signal) => source.gateway.reads.gallery(intent, signal));
    return () => query.stop();
  }, [active, intent, query, source.gateway]);
  function first(name = intent.search) {
    setCursors([]);
    setIntent({ after_persona_id: null, limit: 20, search: name });
  }
  function next() {
    if (state.phase !== "ready" || !state.value.next_after_persona_id) return;
    setCursors((value) => [...value, intent.after_persona_id]);
    setIntent({
      ...intent,
      after_persona_id: state.value.next_after_persona_id,
    });
  }
  function previous() {
    if (!cursors.length) return;
    setIntent({ ...intent, after_persona_id: cursors.at(-1) ?? null });
    setCursors((value) => value.slice(0, -1));
  }
  return {
    query,
    state,
    search,
    setSearch,
    intent,
    first,
    next,
    previous,
    cursors,
  };
}
