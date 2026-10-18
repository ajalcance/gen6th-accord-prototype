import { useState } from "react";
import type { FaceResult } from "../../lib/persona-faces";
import type { FaceInspectionProps } from "./face-inspection";
import type { FaceMutation } from "./face-state";
import ReferencePhoto from "./reference-photo";

type Props = FaceInspectionProps & {
  result: FaceResult;
  mutation: FaceMutation;
  disabled: boolean;
};
export default function FaceSelection(props: Props) {
  const [selected, setSelected] = useState<number | null>(null),
    [confirmed, setConfirmed] = useState(false);
  const { result, mutation, version, capture, disabled } = props;
  const selectable = result.state === "selection_required";
  function submit() {
    if (selected === null || !confirmed || !selectable) return;
    void mutation.submit({
      version_id: version.version_id,
      portrait_id: capture.portrait_id,
      request_id: crypto.randomUUID(),
      generation_id: result.generation_id,
      face_index: selected,
    });
  }
  return (
    <fieldset disabled={disabled || !selectable}>
      <legend>Choose the performer face</legend>
      <ReferencePhoto
        gateway={props.source.captures!}
        version={version.version_id}
        portrait={capture.portrait_id}
        denied={props.denied}
        faces={result}
      />
      <FaceChoices
        result={result}
        selected={selected}
        choose={(index) => {
          setSelected(index);
          setConfirmed(false);
        }}
      />
      {selectable && (
        <FaceConfirmation
          selected={selected}
          confirmed={confirmed}
          confirm={setConfirmed}
          submit={submit}
        />
      )}
    </fieldset>
  );
}
function FaceChoices({
  result,
  selected,
  choose,
}: {
  result: FaceResult;
  selected: number | null;
  choose: (index: number) => void;
}) {
  return (
    <>
      {result.faces.map((face) => (
        <label key={face.index}>
          <input
            type="radio"
            name={"face-" + result.portrait_id}
            checked={selected === face.index}
            onChange={() => choose(face.index)}
          />
          Face {face.index + 1} · {face.width} × {face.height} px · detection{" "}
          {Math.round(face.confidence * 100)}%
        </label>
      ))}
    </>
  );
}
function FaceConfirmation({
  selected,
  confirmed,
  confirm,
  submit,
}: {
  selected: number | null;
  confirmed: boolean;
  confirm: (value: boolean) => void;
  submit: () => void;
}) {
  return (
    <>
      <label>
        <input
          type="checkbox"
          checked={confirmed && selected !== null}
          onChange={(e) => confirm(e.target.checked)}
          disabled={selected === null}
        />
        I confirm this is the performer face for this approved reference.
      </label>
      <button
        type="button"
        disabled={selected === null || !confirmed}
        onClick={submit}
      >
        Create face and image representations
      </button>
    </>
  );
}
