import { useRef, useState } from "react";
import type { GalleryDisplayProps } from "./gallery-display";
import { useSavedSource, type SavedPersonaSource } from "./saved-source";
import SavedRecord, { ReadFeedback } from "./saved-record";
import SavedPersonaCard from "./saved-persona-card";
import SignedOutWelcome from "./signed-out-welcome";
import SavedGalleryTools, { GalleryPager } from "./saved-gallery-tools";
import RecordImageSearch from "./record-image-search";
import { useSavedGallery } from "./use-saved-gallery";
import type { RecordNavigation, RecordTarget } from "./workspace-pages";

type Props = {
  create?: () => void;
  signIn?: () => void;
  initialPersonaId?: string | null;
  active?: boolean;
  target?: RecordTarget | null;
  navigation?: RecordNavigation;
  closeRecord?: () => void;
  view?: "grid" | "list";
  setView?: (view: "grid" | "list") => void;
};
export default function SavedGallery(props: Props) {
  const source = useSavedSource();
  const [view, setView] = useState<"grid" | "list">("grid");
  const display = {
    view: props.view ?? view,
    setView: props.setView ?? setView,
  };
  if (!source)
    return (
      <DisconnectedGallery
        {...display}
        create={props.create}
        signIn={props.signIn}
      />
    );
  if (source.workspaceId !== source.gateway.workspaceId)
    return <p role="alert">The workspace connection could not be validated.</p>;
  return (
    <ConnectedGallery
      key={`${source.workspaceId}:${source.sessionKey}`}
      {...props}
      {...display}
      source={source}
    />
  );
}

function ConnectedGallery({
  source,
  active = true,
  ...props
}: Props & GalleryDisplayProps & { source: SavedPersonaSource }) {
  const gallery = useSavedGallery(source, active);
  const [local, setLocal] = useState<string | null>(
    props.initialPersonaId ?? null,
  );
  const selected = props.navigation ? props.target?.id : local;
  const [image, setImage] = useState(false);
  const container = useRef<HTMLDivElement>(null);
  function closeImage() {
    setImage(false);
    container.current
      ?.querySelector<HTMLButtonElement>(".record-image-trigger")
      ?.focus();
  }
  if (!active) return null;
  if (selected)
    return (
      <SavedRecord
        key={`${selected}:${props.target?.revision}`}
        source={source}
        personaId={selected}
        revision={props.target?.revision}
        initialSection={props.target?.section}
        navigation={props.navigation}
        close={() => {
          setLocal(null);
          props.closeRecord?.();
          void gallery.query.retry();
        }}
      />
    );
  return (
    <GalleryBrowsing
      {...props}
      source={source}
      gallery={gallery}
      image={image}
      setImage={setImage}
      closeImage={closeImage}
      container={container}
      select={(id) => {
        if (props.navigation) props.navigation.open(id);
        else setLocal(id);
      }}
    />
  );
}

function GalleryResults({
  gallery,
  view,
  select,
}: {
  gallery: ReturnType<typeof useSavedGallery>;
  view: "grid" | "list";
  select: (id: string) => void;
}) {
  const { state, query } = gallery;
  const pager = {
    previous: gallery.cursors.length ? gallery.previous : undefined,
    next:
      state.phase === "ready" && state.value.next_after_persona_id
        ? gallery.next
        : undefined,
    first: () => gallery.first(),
    busy: state.phase === "loading",
  };
  return (
    <section
      aria-label="Saved workspace records"
      aria-busy={state.phase === "loading"}
    >
      <ReadFeedback
        state={state}
        retry={() => void query.retry()}
        cancel={() => query.cancel()}
      />
      <GalleryPager {...pager} position="top" />
      {state.phase === "ready" &&
        (state.value.items.length ? (
          <ul
            className={`saved-grid ${view === "list" ? "saved-list" : ""}`}
            aria-label={`${view} of workspace personas`}
          >
            {state.value.items.map((item) => (
              <li key={item.persona_id}>
                <SavedPersonaCard
                  version={item}
                  open={() => select(item.persona_id)}
                />
              </li>
            ))}
          </ul>
        ) : (
          <div className="empty-state" role="status">
            <h2>No saved personas found</h2>
            <p>Try a different name or refresh the workspace.</p>
          </div>
        ))}
      <GalleryPager {...pager} position="bottom" />
    </section>
  );
}

function DisconnectedGallery(
  props: GalleryDisplayProps & Pick<Props, "create" | "signIn">,
) {
  return (
    <>
      <SavedGalleryTools
        {...props}
        search=""
        change={() => {}}
        submit={() => {}}
        refresh={() => {}}
        pending={false}
        connected={false}
        image={false}
        toggleImage={() => {}}
      />
      <SignedOutWelcome signIn={props.signIn} />
    </>
  );
}

function GalleryBrowsing(
  props: Props &
    GalleryDisplayProps & {
      source: SavedPersonaSource;
      gallery: ReturnType<typeof useSavedGallery>;
      image: boolean;
      setImage: (value: boolean) => void;
      closeImage: () => void;
      container: React.RefObject<HTMLDivElement | null>;
      select: (id: string) => void;
    },
) {
  const { source, gallery, image, setImage, closeImage, container } = props;
  return (
    <div ref={container}>
      <SavedGalleryTools
        {...props}
        count={
          gallery.state.phase === "ready"
            ? gallery.state.value.items.length
            : undefined
        }
        paged={
          !!gallery.intent.after_persona_id ||
          (gallery.state.phase === "ready" &&
            !!gallery.state.value.next_after_persona_id)
        }
        connected
        pending={gallery.state.phase === "loading"}
        search={gallery.search}
        change={gallery.setSearch}
        image={image}
        toggleImage={() => setImage(!image)}
        refresh={() => gallery.first()}
        submit={() => {
          setImage(false);
          gallery.first(gallery.search.trim());
        }}
      />
      {image ? (
        <RecordImageSearch source={source} close={closeImage} />
      ) : (
        <GalleryResults
          gallery={gallery}
          view={props.view}
          select={(id) => {
            props.select(id);
          }}
        />
      )}
    </div>
  );
}
