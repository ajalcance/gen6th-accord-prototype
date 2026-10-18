"use client";
import { useEffect, useMemo, useSyncExternalStore } from "react";
import { PersonaQuery } from "../../lib/persona-query";

export function usePersonaQuery<Result>() {
  const query = useMemo(() => new PersonaQuery<Result>(), []);
  const state = useSyncExternalStore(
    query.subscribe,
    query.snapshot,
    query.snapshot,
  );
  useEffect(() => () => query.stop(), [query]);
  return { query, state };
}
