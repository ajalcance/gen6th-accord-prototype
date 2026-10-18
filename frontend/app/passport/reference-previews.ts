import { useEffect, useRef, useState } from "react";

/** Local authored selections only, scoped to this mounted editor; never cached receipts. */
export function useReferencePreviews() {
  const urls = useRef(new Map<string, string>());
  const [previews, setPreviews] = useState(new Map<string, string>());
  useEffect(
    () => () => {
      for (const url of urls.current.values()) URL.revokeObjectURL(url);
      urls.current.clear();
    },
    [],
  );
  function add(id: string, file: File | null) {
    if (!file || urls.current.has(id)) return;
    urls.current.set(id, URL.createObjectURL(file));
    setPreviews(new Map(urls.current));
  }
  function retain(ids: string[]) {
    for (const [id, url] of urls.current) {
      if (!ids.includes(id)) {
        URL.revokeObjectURL(url);
        urls.current.delete(id);
      }
    }
    setPreviews(new Map(urls.current));
  }
  return { previews, add, retain };
}
