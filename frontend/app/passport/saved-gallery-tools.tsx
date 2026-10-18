import Icon from "./icons";
import GalleryDisplay, { type GalleryDisplayProps } from "./gallery-display";

type Props = GalleryDisplayProps & {
  count?: number;
  paged?: boolean;
  search: string;
  change: (value: string) => void;
  submit: () => void;
  refresh: () => void;
  pending: boolean;
  connected: boolean;
  image: boolean;
  toggleImage: () => void;
  create?: () => void;
};

export default function SavedGalleryTools(props: Props) {
  return (
    <div
      className="workspace-record-toolbar"
      role="group"
      aria-label="Record tools"
    >
      <div className="record-heading">
        <h1 tabIndex={-1}>Records</h1>
        {props.count !== undefined && !props.image && (
          <span className="record-count" role="status">
            {props.count} {props.count === 1 ? "record" : "records"}
            {props.paged ? " on this page" : ""}
          </span>
        )}
      </div>
      <NameSearch {...props} />
      <button
        className="secondary record-image-trigger"
        disabled={!props.connected}
        aria-expanded={props.image}
        aria-controls="record-image-search"
        onClick={props.toggleImage}
      >
        <Icon name="scan" size={16} />
        Search by image
      </button>
      <GalleryDisplay view={props.view} setView={props.setView} />
      <button
        className="icon-button"
        disabled={!props.connected || props.pending}
        aria-label="Refresh records"
        title="Refresh records"
        onClick={props.refresh}
      >
        <Icon name="refresh" size={16} />
      </button>
      {props.create && (
        <button className="primary record-create" onClick={props.create}>
          <Icon name="create" size={16} />
          New capture
        </button>
      )}
    </div>
  );
}

function NameSearch(props: Props) {
  return (
    <form
      className="saved-search"
      role="search"
      aria-label="Search saved records"
      onSubmit={(event) => {
        event.preventDefault();
        props.submit();
      }}
    >
      <div className="search-field">
        <input
          type="search"
          aria-label="Search saved persona names"
          placeholder="Search by name…"
          maxLength={80}
          value={props.search}
          disabled={!props.connected}
          onChange={(event) => props.change(event.target.value)}
        />
        <button
          className="search-submit"
          disabled={!props.connected || props.pending}
          type="submit"
          aria-label="Search records"
          title="Search records"
        >
          <Icon name="search" size={16} />
        </button>
      </div>
    </form>
  );
}

export function GalleryPager({
  previous,
  next,
  first,
  busy,
  position,
}: {
  previous?: () => void;
  next?: () => void;
  first: () => void;
  busy: boolean;
  position: "top" | "bottom";
}) {
  if (!previous && !next) return null;
  return (
    <nav className="gallery-pager" aria-label={`Record pages ${position}`}>
      {previous && (
        <button className="secondary" disabled={busy} onClick={first}>
          First page
        </button>
      )}
      <button
        className="secondary"
        disabled={busy || !previous}
        onClick={previous}
      >
        Previous page
      </button>
      <button className="secondary" disabled={busy || !next} onClick={next}>
        Next page
        <Icon name="arrow" size={14} />
      </button>
    </nav>
  );
}
