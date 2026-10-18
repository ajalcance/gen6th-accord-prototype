export type Draft = {
  name: string;
  bio: string;
  contribution: string;
  disclosure: string;
};

export function isDraftReady(draft: Draft): boolean {
  return [draft.name, draft.bio, draft.contribution, draft.disclosure].every(
    (value) => value.trim().length > 0,
  );
}

export function readDraft(): Draft | null {
  const saved: unknown = JSON.parse(
    localStorage.getItem("accord-h1-draft") ?? "null",
  );
  if (
    !saved ||
    typeof saved !== "object" ||
    !("name" in saved) ||
    !("bio" in saved) ||
    !("contribution" in saved)
  )
    return null;
  if (
    typeof saved.name !== "string" ||
    typeof saved.bio !== "string" ||
    typeof saved.contribution !== "string"
  )
    return null;
  return {
    name: saved.name.slice(0, 80),
    bio: saved.bio.slice(0, 500),
    contribution: saved.contribution.slice(0, 500),
    disclosure:
      "Fictional synthetic character concept. No real person or generation log.",
  };
}
