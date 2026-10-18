import {
  useCallback,
  useEffect,
  useRef,
  useState,
  useSyncExternalStore,
} from "react";
import type { BookletRead, BookletScope } from "./booklet-read";
import { readBooklet } from "./booklet-read";
import { bookletShare } from "../../lib/passport-booklet";
import { useGovernanceRead } from "./saved-governance-read";
import BookletIdentity from "./booklet-identity";
import BookletRecords from "./booklet-records";

const subscribe = () => () => {};
export default function PassportBooklet({
  disabled = false,
  ...scope
}: BookletScope & { disabled?: boolean }) {
  const [open, setOpen] = useState(false);
  const [opener, setOpener] = useState<HTMLButtonElement | null>(null);
  return (
    <div className="booklet-access">
      <button
        className="secondary"
        disabled={disabled}
        onClick={(event) => {
          setOpener(event.currentTarget);
          setOpen(true);
        }}
      >
        View passport
      </button>
      {open && (
        <BookletDialog
          {...scope}
          opener={opener}
          close={() => setOpen(false)}
        />
      )}
    </div>
  );
}
function BookletDialog({
  close,
  opener,
  ...scope
}: BookletScope & { close: () => void; opener: HTMLButtonElement | null }) {
  const dialog = useRef<HTMLDialogElement>(null);
  useEffect(() => {
    const element = dialog.current;
    element?.showModal();
    return () => {
      element?.close();
      if (opener instanceof HTMLElement && opener.isConnected) opener.focus();
    };
  }, [opener]);
  return (
    <dialog
      ref={dialog}
      className="booklet-dialog"
      aria-label="Persona passport booklet"
      onCancel={close}
    >
      <header className="booklet-toolbar">
        <h2>Persona passport</h2>
        <button autoFocus onClick={close}>
          Close passport
        </button>
      </header>
      <BookletContent {...scope} />
    </dialog>
  );
}
function BookletContent(scope: BookletScope) {
  const { source, version, offer, packet } = scope;
  const load = useCallback(
    (signal: AbortSignal) =>
      readBooklet({ source, version, offer, packet }, signal),
    [source, version, offer, packet],
  );
  const { state, query } = useGovernanceRead(load);
  const origin = useSyncExternalStore(
    subscribe,
    () => window.location.origin,
    () => "",
  );
  const data = state.phase === "ready" ? state.value : null;
  const portrait = useBlobUrl(data?.portrait ?? null);
  const share = bookletShare(data?.publication?.path ?? null, origin);
  if (state.phase === "denied")
    return (
      <p role="alert">
        Workspace access is unavailable. Saved records were cleared.
      </p>
    );
  return (
    <>
      <div className="booklet-status">
        <p role="status">
          {state.phase === "loading"
            ? "Checking saved passport records…"
            : state.phase === "ready"
              ? "Saved records loaded. Refresh permission before use."
              : "Additional passport records unavailable. Registered preview only."}
        </p>
        <button
          onClick={() => void query.run(load)}
          disabled={state.phase === "loading"}
        >
          Refresh passport records
        </button>
      </div>
      <BookletPages
        version={version}
        offer={offer}
        data={data}
        portrait={portrait}
        share={share}
      />
      <BookletExplanation />
    </>
  );
}
function BookletExplanation() {
  return (
    <p className="booklet-explanation">
      Prepare a package and approve selected fields using the existing controls.
      After a reload, prepare the package again to enable the issued display.
      This view checks at most 200 share history records per refresh.
    </p>
  );
}
function useBlobUrl(blob: Blob | null): string | null {
  const [value, setValue] = useState<{ blob: Blob; url: string } | null>(null);
  useEffect(() => {
    if (!blob) return;
    let active = true,
      url: string | null = null;
    void Promise.resolve().then(() => {
      if (!active) return;
      url = URL.createObjectURL(blob);
      setValue({ blob, url });
    });
    return () => {
      active = false;
      if (url) URL.revokeObjectURL(url);
    };
  }, [blob]);
  return value?.blob === blob ? value.url : null;
}

function BookletPages({
  version,
  offer,
  data,
  portrait,
  share,
}: Pick<BookletScope, "version" | "offer"> & {
  data: BookletRead | null;
  portrait: string | null;
  share: ReturnType<typeof bookletShare>;
}) {
  const issued = !!data?.signature && !!share;
  return (
    <article
      className="passport-booklet"
      data-state={issued ? "issued" : "registered"}
      aria-label={
        issued ? "Issued persona passport" : "Registered passport preview"
      }
    >
      <BookletIdentity
        version={version}
        offer={offer}
        portrait={portrait}
        portraitMessage={
          data?.profile
            ? "Portrait not approved"
            : "Approved portrait unavailable"
        }
        signature={data?.signature ?? null}
        issued={issued}
      />
      <BookletRecords
        version={version}
        offer={offer}
        data={data}
        share={share}
      />
    </article>
  );
}
