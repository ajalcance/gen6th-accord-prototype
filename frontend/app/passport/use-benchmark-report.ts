import { useEffect, useRef, useState } from "react";
import {
  parseBenchmarkReport,
  type BenchmarkReport,
} from "../../lib/persona-benchmark";

export function useBenchmarkReport() {
  const [report, setReport] = useState<BenchmarkReport | null>(null);
  const [error, setError] = useState(false);
  const [busy, setBusy] = useState(false);
  const generation = useRef(0);
  useEffect(
    () => () => {
      generation.current += 1;
    },
    [],
  );
  async function inspect(file?: File) {
    const attempt = ++generation.current;
    setReport(null);
    setError(false);
    setBusy(false);
    if (!file) return;
    setBusy(true);
    try {
      if (file.size < 1 || file.size > 16 * 1024 * 1024)
        throw new Error("size");
      const result = parseBenchmarkReport(JSON.parse(await file.text()));
      if (generation.current === attempt) setReport(result);
    } catch {
      if (generation.current === attempt) setError(true);
    } finally {
      if (generation.current === attempt) setBusy(false);
    }
  }
  return { report, error, busy, inspect };
}
