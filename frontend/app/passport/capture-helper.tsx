import { useRef, useState } from "react";
import type { PersonaPhotoState } from "./persona-photo-state";

type Step = { label: string; selector: string; done: boolean; busy?: boolean };
const fields = [
  ["name", "Persona name", 80],
  ["biography", "Biography", 500],
  ["human_contribution", "Human contribution", 500],
  ["ai_disclosure", "AI disclosure", 500],
] as const;
function captureSteps(
  values: Record<string, string>,
  photo: PersonaPhotoState,
): Step[] {
  return [
    ...fields.map(([key, label, max]) => ({
      label,
      selector: `#creation-${key}`,
      done: !!values[key]?.trim() && [...values[key].trim()].length <= max,
    })),
    {
      label:
        photo.state.phase === "pending"
          ? "Portrait scan in progress"
          : photo.file
            ? "Scan portrait"
            : "Choose portrait",
      selector:
        photo.file && photo.available
          ? "[data-capture-scan]"
          : ".photo-picker input",
      done: photo.change?.action === "attach",
      busy: photo.state.phase === "pending",
    },
    {
      label: "Review and confirm",
      selector: ".prepared-confirm input",
      done: values.confirm === "yes",
    },
  ];
}
type HelperProps = {
  values: Record<string, string>;
  photo: PersonaPhotoState;
  connected: boolean;
};
function useHelper() {
  const [open, setOpen] = useState(false);
  const trigger = useRef<HTMLButtonElement>(null);
  function close() {
    setOpen(false);
    trigger.current?.focus();
  }
  function jump(step: Step) {
    const target = trigger.current
      ?.closest("form")
      ?.querySelector<HTMLElement>(step.selector);
    if (!target) return;
    const disclosure = target.closest("details");
    if (disclosure) disclosure.open = true;
    setOpen(false);
    target.focus();
    target.scrollIntoView?.({ block: "nearest" });
  }
  return {
    open,
    trigger,
    close,
    jump,
    toggle: () => setOpen(!open),
    events: {
      onBlur: (event: React.FocusEvent<HTMLDivElement>) => {
        if (!event.currentTarget.contains(event.relatedTarget)) setOpen(false);
      },
      onKeyDown: (event: React.KeyboardEvent<HTMLDivElement>) => {
        if (event.key === "Escape" && open) {
          event.preventDefault();
          close();
        }
      },
    },
  };
}
export default function CaptureHelper({
  values,
  photo,
  connected,
}: HelperProps) {
  const { open, trigger, close, jump, toggle, events } = useHelper();
  const steps = captureSteps(values, photo);
  const remaining = steps.filter((step) => !step.done).length;
  return (
    <div className="capture-helper" {...events}>
      <button
        ref={trigger}
        type="button"
        className="text-button"
        aria-expanded={open}
        aria-controls="capture-helper-panel"
        onClick={toggle}
      >
        Capture helper{" "}
        <span className="badge">
          {remaining ? `${remaining} steps left` : "Ready"}
        </span>
      </button>
      {open && (
        <HelperPanel
          steps={steps}
          connected={connected}
          jump={jump}
          close={close}
        />
      )}
    </div>
  );
}
function HelperPanel({
  steps,
  connected,
  jump,
  close,
}: {
  steps: Step[];
  connected: boolean;
  jump: (step: Step) => void;
  close: () => void;
}) {
  const next = steps.find((step) => !step.done);
  return (
    <section
      className="capture-helper-panel"
      id="capture-helper-panel"
      aria-label="Capture helper"
    >
      <div className="panel-heading">
        <h3>{next ? "Finish your capture" : "Ready to register"}</h3>
        <button
          type="button"
          className="text-button"
          aria-label="Close capture helper"
          onClick={close}
        >
          Close
        </button>
      </div>
      {next && (
        <button
          type="button"
          className="primary"
          disabled={next.busy}
          onClick={() => jump(next)}
        >
          Next: {next.label}
        </button>
      )}
      <HelperSteps steps={steps} jump={jump} />
      {!connected && (
        <p className="help">
          Saving needs an authorized workspace connection. You can continue
          writing your draft.
        </p>
      )}
      <details>
        <summary>What happens after saving?</summary>
        <p className="help">
          Registration saves the first approved portrait. Continue to Prepare
          recognition for face detection and representation. Biography,
          contributions and rights claims remain yours to supply.
        </p>
      </details>
    </section>
  );
}

function HelperSteps({
  steps,
  jump,
}: {
  steps: Step[];
  jump: (step: Step) => void;
}) {
  return (
    <ul>
      {steps.map((step) => (
        <li key={step.selector}>
          <button
            type="button"
            className="text-button"
            disabled={
              step.busy ||
              (step.done && step.selector === "[data-capture-scan]")
            }
            onClick={() => jump(step)}
          >
            <span aria-hidden="true">{step.done ? "✓" : "○"}</span>
            {step.label}
            <small>{step.done ? "Complete" : "Needed"}</small>
          </button>
        </li>
      ))}
    </ul>
  );
}
