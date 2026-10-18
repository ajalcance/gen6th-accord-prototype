import { useSavedGallery } from "./use-saved-gallery";
import type { SavedPersonaSource } from "./saved-source";
import { ReadFeedback } from "./saved-record";
import { GalleryPager } from "./saved-gallery-tools";
import Icon from "./icons";
import type { PersonaVersion } from "../../lib/persona-contracts";
import { journeyEntries, type JourneyPage } from "./workspace-pages";

export default function PersonaPicker({
  source,
  select,
  journey,
}: {
  source: SavedPersonaSource;
  select: (id: string) => void;
  journey: JourneyPage;
}) {
  const gallery = useSavedGallery(source, true);
  return (
    <section className="persona-picker" aria-label="Choose a performer">
      <h2>Choose a performer</h2>
      <p className="help">
        Your performer and version selection carries across workflow pages.
      </p>
      <PerformerSearch gallery={gallery} />
      <ReadFeedback
        state={gallery.state}
        resource="Saved performers"
        retry={() => void gallery.query.retry()}
        cancel={() => gallery.query.cancel()}
      />
      {gallery.state.phase === "ready" && (
        <PerformerChoices
          items={gallery.state.value.items}
          select={select}
          action={journeyEntries[journey].action}
        />
      )}
      <GalleryPager
        previous={gallery.cursors.length ? gallery.previous : undefined}
        next={
          gallery.state.phase === "ready" &&
          gallery.state.value.next_after_persona_id
            ? gallery.next
            : undefined
        }
        first={() => gallery.first()}
        busy={gallery.state.phase === "loading"}
        position="bottom"
      />
    </section>
  );
}

function PerformerSearch({
  gallery,
}: {
  gallery: ReturnType<typeof useSavedGallery>;
}) {
  return (
    <form
      className="performer-search"
      role="search"
      aria-label="Find a saved performer"
      onSubmit={(event) => {
        event.preventDefault();
        gallery.first(gallery.search.trim());
      }}
    >
      <label className="search-field">
        <span className="visually-hidden">Performer name</span>
        <Icon name="search" size={16} />
        <input
          type="search"
          placeholder="Search by performer name…"
          maxLength={80}
          value={gallery.search}
          onChange={(event) => gallery.setSearch(event.target.value)}
        />
      </label>
      <button
        className="secondary"
        disabled={gallery.state.phase === "loading"}
      >
        Find performer
      </button>
    </form>
  );
}

function PerformerChoices({
  items,
  select,
  action,
}: {
  items: PersonaVersion[];
  select: (id: string) => void;
  action: string;
}) {
  return (
    <>
      <p className="performer-results-count" role="status">
        {items.length} {items.length === 1 ? "performer" : "performers"} on this
        page
      </p>
      <ul className="performer-choices" aria-label="Saved performers">
        {items.map((item) => (
          <li key={item.persona_id}>
            <button
              type="button"
              className="performer-choice"
              aria-label={`${action} for ${item.content.name}, version ${item.revision}`}
              onClick={() => select(item.persona_id)}
            >
              <span className="performer-choice-icon">
                <Icon name="portrait" size={20} />
              </span>
              <span className="performer-choice-identity">
                <span className="performer-choice-name">
                  {item.content.name}
                </span>
                <span className="performer-choice-version">
                  Version {item.revision}
                </span>
              </span>
              <span className="performer-choice-action" aria-hidden="true">
                {action} <Icon name="arrow" size={16} />
              </span>
            </button>
          </li>
        ))}
        {items.length === 0 && (
          <li className="performer-empty">
            No matching saved performers. Try another name.
          </li>
        )}
      </ul>
    </>
  );
}
