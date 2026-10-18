import { useState } from "react";
import Portrait from "./portrait";
import Icon from "../../app/passport/icons";
import type { StudioState } from "./use-studio";
import { FIXTURES, campaignBlocks } from "./console-fixtures";
import type { ConsoleRecord } from "./console-types";
import SavedGallery from "../../app/passport/saved-gallery";

function needsReview(record: ConsoleRecord): boolean {
  return (
    !record.reviewed && (record.analysis === "ready" || record.id === "nova")
  );
}
export type GallerySourceControls = {
  saved: boolean;
  setSaved: (saved: boolean) => void;
};
export default function Gallery(props: StudioState & GallerySourceControls) {
  return (
    <>
      <div className="gallery-source" role="group" aria-label="Record source">
        <button
          className="secondary"
          aria-pressed={!props.saved}
          onClick={() => props.setSaved(false)}
        >
          Browser fixtures
        </button>
        <button
          className="secondary"
          aria-pressed={props.saved}
          onClick={() => props.setSaved(true)}
        >
          Saved records
        </button>
      </div>
      {props.saved ? <SavedGallery /> : <FixtureGallery {...props} />}
    </>
  );
}
function FixtureGallery(props: StudioState) {
  const [view, setView] = useState<"grid" | "list">("grid");
  return (
    <>
      <GalleryOverview {...props} />
      <GalleryToolbar {...props} />
      <div className="gallery-view-bar">
        <p className="help">Select a record to continue its next step.</p>
        <div className="segmented-control" aria-label="Record display">
          <button
            aria-pressed={view === "grid"}
            onClick={() => setView("grid")}
          >
            Grid
          </button>
          <button
            aria-pressed={view === "list"}
            onClick={() => setView("list")}
          >
            List
          </button>
        </div>
      </div>
      <PersonaCards {...props} view={view} />
      <div className="gallery-support">
        <ReviewNotice {...props} />
        <PassportNotice {...props} />
      </div>
    </>
  );
}
function ReviewNotice(props: StudioState) {
  const count = props.records.filter(needsReview).length;
  return (
    <section className="gallery-support-item">
      <Icon name="scan" size={18} />
      <div>
        <h2>Pending review</h2>
        <p>
          {count
            ? `${count} fictional ${count === 1 ? "record needs" : "records need"} an independent review.`
            : "No fixture reviews pending."}
        </p>
        <button
          className="text-button"
          disabled={count === 0}
          onClick={() => {
            const next = props.records.findIndex(needsReview);
            props.setSelected(next < 0 ? props.selected : next);
            props.setStep(2);
          }}
        >
          Open review workspace <Icon name="arrow" size={14} />
        </button>
      </div>
    </section>
  );
}
function PassportNotice(props: StudioState) {
  return (
    <details className="gallery-support-item passport-context">
      <summary>What does a passport record?</summary>
      <p>
        Records claims and evidence; does not establish legal ownership or
        worldwide originality.
      </p>
      <button className="text-button" onClick={() => props.setStep(4)}>
        Explore a passport <Icon name="arrow" size={14} />
      </button>
    </details>
  );
}

function GalleryOverview(props: StudioState) {
  return (
    <div className="summary-strip">
      <button
        className="summary-metric"
        onClick={() => props.setFilter("All personas")}
      >
        <span>FICTIONAL PERSONAS</span>
        <strong>
          {String(props.records.length).padStart(2, "0")}
          <small>In this browser</small>
        </strong>
      </button>
      <button
        className="summary-metric"
        onClick={() => props.setFilter("Needs review")}
      >
        <span>NEEDS REVIEW</span>
        <strong>
          {String(props.records.filter(needsReview).length).padStart(2, "0")}
          <small>Human decisions</small>
        </strong>
      </button>
      <button
        className="summary-metric"
        onClick={() => props.setFilter("Reviewed")}
      >
        <span>DEMO REVIEWS</span>
        <strong>
          {String(
            props.records.filter((record) => record.reviewed).length,
          ).padStart(2, "0")}
          <small>Recorded in this tab</small>
        </strong>
      </button>
      <button
        className="summary-action"
        onClick={() => props.setDrawer("operations")}
      >
        <Icon name="pulse" />
        <span>
          Connection & readiness
          <small>Inspect capabilities & connection state</small>
        </span>
        <Icon name="arrow" />
      </button>
    </div>
  );
}
function PersonaCards(props: StudioState & { view: "grid" | "list" }) {
  const visible = props.records
    .map((record, index) => ({ record, index }))
    .filter(({ record }) => {
      const matchesFilter =
        props.filter === "All personas" ||
        (props.filter === "Needs review"
          ? needsReview(record)
          : props.filter === "Reviewed"
            ? record.reviewed
            : !record.reviewed && !needsReview(record));
      return (
        matchesFilter &&
        record.draft.name.toLowerCase().includes(props.search.toLowerCase())
      );
    });
  if (!visible.length)
    return (
      <div className="empty-state" role="status">
        <Icon name="search" size={28} />
        <h2>No matching personas</h2>
        <p>Try another search or show all fictional records.</p>
        <button
          className="secondary"
          onClick={() => {
            props.setSearch("");
            props.setFilter("All personas");
          }}
        >
          Clear filters
        </button>
      </div>
    );
  return (
    <div
      className={`gallery ${props.view === "list" ? "gallery-list" : ""}`}
      aria-label={`${props.view} of fictional personas`}
    >
      {visible.map(({ record, index }) => (
        <PersonaCard {...props} key={record.id} record={record} index={index} />
      ))}
    </div>
  );
}

function GalleryToolbar(props: StudioState) {
  return (
    <div className="section-bar gallery-toolbar">
      <div className="tabs" aria-label="Persona filters">
        {["All personas", "Needs review", "Drafts", "Reviewed"].map((label) => (
          <button
            key={label}
            className={props.filter === label ? "selected" : ""}
            aria-pressed={props.filter === label}
            onClick={() => props.setFilter(label)}
          >
            {label}
          </button>
        ))}
      </div>
      <label className="search-field gallery-search">
        <Icon name="search" />
        <input
          type="search"
          aria-label="Search personas"
          placeholder="Search personas…"
          value={props.search}
          onChange={(event) => props.setSearch(event.target.value)}
        />
      </label>
    </div>
  );
}

function PersonaCard(
  props: StudioState & { record: ConsoleRecord; index: number },
) {
  const { record, index } = props;
  return (
    <button
      className="persona-card"
      onClick={() => {
        props.setSelected(index);
        props.setStep(record.reviewed ? 3 : needsReview(record) ? 2 : 1);
      }}
    >
      <div className="portrait-wrap">
        <Portrait variant={record.variant} />
      </div>
      <div className="card-info">
        <div>
          <h2>{record.draft.name || "Untitled fixture"}</h2>
          <p>{FIXTURES[record.variant].category}</p>
        </div>
        <span className={record.reviewed ? "card-state success" : "card-state"}>
          {record.reviewed
            ? "Demo reviewed"
            : needsReview(record)
              ? "Review scenario"
              : "Draft fixture"}
        </span>
      </div>
      <div className="card-footer">
        <span>fixture-v{record.revision} · local</span>
        <span className="list-permission">
          {campaignBlocks(record).length
            ? "Campaign use blocked"
            : "Eligible in demo window"}
        </span>
        <span className="card-open">
          {record.reviewed
            ? "Open campaign"
            : needsReview(record)
              ? "Open review"
              : "Continue draft"}{" "}
          <Icon name="arrow" size={14} />
        </span>
      </div>
    </button>
  );
}
