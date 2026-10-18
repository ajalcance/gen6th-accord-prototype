import { useState } from "react";
import type { SavedPersonaSource } from "./saved-source";
import PortraitSearch from "./portrait-search";
import SimilaritySearch from "./similarity-search";

export default function RecordImageSearch({
  source,
  close,
}: {
  source: SavedPersonaSource;
  close: () => void;
}) {
  const [method, setMethod] = useState("Identical file");
  return (
    <section
      className="record-image-search"
      aria-label="Search by image"
      id="record-image-search"
    >
      <div className="section-bar">
        <h2>Search this workspace</h2>
        <button className="secondary" onClick={close}>
          Return to all records
        </button>
      </div>
      <div
        className="workspace-tabs"
        role="group"
        aria-label="Image search method"
      >
        {["Identical file", "Similar face"].map((item) => (
          <button
            key={item}
            className="secondary"
            aria-pressed={method === item}
            onClick={() => setMethod(item)}
          >
            {item}
          </button>
        ))}
      </div>
      {method === "Identical file" ? (
        <PortraitSearch source={source} expanded />
      ) : (
        <SimilaritySearch source={source} expanded />
      )}
    </section>
  );
}
