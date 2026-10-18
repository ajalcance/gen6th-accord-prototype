import Icon from "./icons";

export type GalleryDisplayProps = {
  view: "grid" | "list";
  setView: (view: "grid" | "list") => void;
};

export default function GalleryDisplay({ view, setView }: GalleryDisplayProps) {
  return (
    <div
      className="segmented-control gallery-display"
      role="group"
      aria-label="Record display"
    >
      <button
        type="button"
        aria-label="Grid view"
        title="Grid view"
        aria-pressed={view === "grid"}
        onClick={() => setView("grid")}
      >
        <Icon name="grid" size={15} />
      </button>
      <button
        type="button"
        aria-label="List view"
        title="List view"
        aria-pressed={view === "list"}
        onClick={() => setView("list")}
      >
        <Icon name="menu" size={15} />
      </button>
    </div>
  );
}
