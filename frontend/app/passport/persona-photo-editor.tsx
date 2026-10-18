import Image from "next/image";
import type { PersonaPhotoState } from "./persona-photo-state";
import Icon from "./icons";
import { StagedCaptureStatus } from "./capture-status";

export default function PersonaPhotoEditor({
  photo,
  editing = false,
  prominent = false,
  referenceOnly = false,
}: {
  photo: PersonaPhotoState;
  editing?: boolean;
  prominent?: boolean;
  referenceOnly?: boolean;
}) {
  return (
    <section
      className={`persona-photo-editor${prominent ? " creation-portrait" : ""}`}
      aria-label="Persona photo"
    >
      <PhotoHeading
        editing={editing}
        prominent={prominent}
        referenceOnly={referenceOnly}
      />
      {photo.preview ? (
        <SelectedPhoto url={photo.preview} />
      ) : (
        prominent && <PortraitPlaceholder />
      )}
      <PhotoPicker photo={photo} editing={editing} />
      {photo.file && (
        <p className="help">
          Select Scan to begin ingestion: upload this photo and run safety
          checks.
        </p>
      )}
      {!photo.available && (
        <p className="help">
          You can preview a photo here. Uploads require a connected photo
          service. Registration requires a successful scan.
        </p>
      )}
      <PhotoControls photo={photo} editing={editing && !referenceOnly} />
      {photo.state.id && (
        <StagedCaptureStatus id={photo.state.id} digest={photo.state.sha256} />
      )}
      <PhotoGuidance editing={editing} referenceOnly={referenceOnly} />
    </section>
  );
}

function PhotoControls({
  photo,
  editing,
}: {
  photo: PersonaPhotoState;
  editing: boolean;
}) {
  return (
    <>
      {photo.file && <UploadActions photo={photo} />}
      {editing && (
        <button type="button" className="secondary" onClick={photo.remove}>
          Remove saved photo
        </button>
      )}
      {photo.state.message && (
        <p role={photo.state.phase === "failed" ? "alert" : "status"}>
          {photo.state.message}
        </p>
      )}
    </>
  );
}

function UploadActions({ photo }: { photo: PersonaPhotoState }) {
  return (
    <div className="photo-actions">
      <button
        type="button"
        className="primary"
        data-capture-scan
        disabled={
          !photo.available || ["pending", "checked"].includes(photo.state.phase)
        }
        onClick={() => void photo.check()}
      >
        {photo.state.phase === "failed"
          ? "Retry scan"
          : photo.state.phase === "pending"
            ? "Scanning…"
            : photo.state.phase === "checked"
              ? "Scan complete"
              : "Scan"}
      </button>
      {photo.state.phase === "pending" && (
        <button type="button" className="secondary" onClick={photo.cancel}>
          Stop waiting
        </button>
      )}
      <button
        type="button"
        className="secondary"
        onClick={() => photo.choose(null)}
      >
        Discard selection
      </button>
    </div>
  );
}

function PhotoPicker({
  photo,
  editing,
}: {
  photo: PersonaPhotoState;
  editing: boolean;
}) {
  return (
    <div className="photo-selection">
      <label className="photo-picker">
        <Icon name="create" />
        <span>{editing ? "Add or replace photo" : "Choose photo"}</span>
        <input
          type="file"
          accept="image/png,image/jpeg"
          disabled={photo.state.phase === "pending"}
          onChange={(event) => {
            photo.choose(event.target.files?.[0] ?? null);
            event.target.value = "";
          }}
        />
      </label>
      <p className="help">PNG or JPEG · up to 10 MB</p>
      {photo.file && (
        <p className="photo-filename">
          {photo.file.name} · {(photo.file.size / 1024).toFixed(1)} KiB · local
          selection
        </p>
      )}
    </div>
  );
}

function PortraitPlaceholder() {
  return (
    <div className="portrait-placeholder">
      <Icon name="portrait" size={64} />
      <strong>A face for your persona</strong>
      <p className="help">
        Choose a portrait or an image that represents this persona.
      </p>
    </div>
  );
}

function SelectedPhoto({ url }: { url: string }) {
  return (
    <figure className="photo-preview">
      <Image
        src={url}
        alt="Unsaved photo selection"
        width={160}
        height={160}
        unoptimized
      />
      <figcaption>Unsaved selection</figcaption>
    </figure>
  );
}

function PhotoHeading({
  editing,
  prominent,
  referenceOnly,
}: {
  editing: boolean;
  prominent: boolean;
  referenceOnly: boolean;
}) {
  return (
    <div>
      <h3>
        {prominent ? "Persona portrait" : "Photo"}{" "}
        <span className="help">
          {referenceOnly
            ? "reference portrait"
            : editing
              ? "version image"
              : "required"}
        </span>
      </h3>
      {!prominent && (
        <p className="help">
          {referenceOnly
            ? "Scan a portrait, then explicitly add it to this reference set."
            : "A photo change creates a new version."}
        </p>
      )}
    </div>
  );
}

function PhotoGuidance({
  editing,
  referenceOnly,
}: {
  editing: boolean;
  referenceOnly: boolean;
}) {
  return (
    <details className="photo-guidance">
      <summary>How scanning and registration work</summary>
      <p className="help">
        {referenceOnly ? (
          "Choosing and scanning a photo does not approve it. Add the checked reference and save the reference version."
        ) : (
          <>
            Choosing a photo only previews it here. Scan uploads it for safety
            checks; saving attaches it to the persona. Your text draft stays in
            this tab.
            {!editing &&
              " Registering approves the prepared portrait as the first reference for this persona."}
          </>
        )}
      </p>
    </details>
  );
}
