import { useState, useSyncExternalStore } from "react";
import { passportQr } from "../../lib/passport-qr";

const subscribe = () => () => {};

export default function PassportShare({ path }: { path: string }) {
  const origin = useSyncExternalStore(
    subscribe,
    () => window.location.origin,
    () => "",
  );
  const url = origin ? new URL(path, origin).href : "";
  const [copied, setCopied] = useState(false);
  let modules: boolean[][] | null = null;
  try {
    if (url) modules = passportQr(url);
  } catch {
    modules = null;
  }
  return (
    <section aria-label="Public passport share link">
      <a href={path} target="_blank" rel="noopener noreferrer">
        Open approved public passport
      </a>
      <p>{url || path}</p>
      {modules && (
        <svg
          role="img"
          aria-label="QR code for approved public passport"
          viewBox="0 0 57 57"
          width="228"
          height="228"
          shapeRendering="crispEdges"
        >
          <rect width="57" height="57" fill="white" />
          <path
            fill="black"
            d={modules
              .flatMap((row, y) =>
                row.flatMap((dark, x) =>
                  dark ? [`M${x + 4},${y + 4}h1v1h-1z`] : [],
                ),
              )
              .join("")}
          />
        </svg>
      )}
      <button
        disabled={!url}
        onClick={() => {
          void navigator.clipboard
            .writeText(url)
            .then(() => setCopied(true))
            .catch(() => setCopied(false));
        }}
      >
        Copy share link
      </button>
      {copied && <p role="status">Share link copied</p>}
    </section>
  );
}
