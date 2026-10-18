import { useEffect, useRef } from "react";
import Icon from "../../app/passport/icons";
import type { StudioState } from "./use-studio";
import {
  AssistantContent,
  OperationsContent,
  RecordContent,
} from "./drawer-content";
import { CommandContent } from "./command-content";
import GovernanceWorkspace from "./governance-workspace";

const TITLES = {
  assistant: "Demo guide",
  records: "Activity & versions",
  operations: "Connection & readiness",
  commands: "Quick actions",
  governance: "Evidence & decisions",
};

export default function ConsoleDrawer(props: StudioState) {
  const dialog = useDialogFocus(props);
  if (props.drawer === null) return null;
  return (
    <div className="drawer-overlay" onClick={() => props.setDrawer(null)}>
      <div
        ref={dialog}
        className={`console-drawer ${props.drawer === "commands" ? "command-drawer" : ""} ${props.drawer === "governance" ? "governance-drawer" : ""}`}
        role="dialog"
        aria-modal="true"
        aria-labelledby="drawer-title"
        onClick={(event) => event.stopPropagation()}
      >
        <header className="drawer-header">
          <div>
            <p className="eyebrow">
              {props.drawer === "governance"
                ? "FICTIONAL GOVERNANCE EXAMPLES"
                : "NORTH STUDIO / FICTIONAL WORKSPACE"}
            </p>
            <h2 id="drawer-title">{TITLES[props.drawer]}</h2>
          </div>
          <button
            className="icon-button"
            aria-label="Close panel"
            onClick={() => props.setDrawer(null)}
          >
            <Icon name="close" />
          </button>
        </header>
        {props.drawer === "assistant" && <AssistantContent {...props} />}
        {props.drawer === "records" && <RecordContent {...props} />}
        {props.drawer === "operations" && <OperationsContent {...props} />}
        {props.drawer === "commands" && <CommandContent {...props} />}
        {props.drawer === "governance" && (
          <GovernanceWorkspace
            draft={props.draft}
            close={() => props.setDrawer(null)}
            connection={() => props.setDrawer("operations")}
            creation={() => {
              props.setStep(1);
              props.setDrawer(null);
            }}
          />
        )}
      </div>
    </div>
  );
}

function useDialogFocus(props: StudioState) {
  const dialog = useRef<HTMLDivElement>(null);
  const dispatch = props.dispatch;
  useEffect(() => {
    const trigger = document.activeElement;
    const overflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    (
      dialog.current?.querySelector<HTMLElement>("input[type='search']") ??
      dialog.current?.querySelector<HTMLElement>("button")
    )?.focus();
    function keyboard(event: KeyboardEvent) {
      if (event.key === "Escape") {
        event.preventDefault();
        dispatch({ type: "drawer", value: null });
      }
      if (event.key !== "Tab") return;
      const targets = dialogTargets(dialog.current);
      const first = targets[0];
      const last = targets.at(-1);
      if (event.shiftKey && document.activeElement === first) {
        event.preventDefault();
        last?.focus();
      } else if (!event.shiftKey && document.activeElement === last) {
        event.preventDefault();
        first?.focus();
      }
    }
    document.addEventListener("keydown", keyboard);
    return () => {
      document.removeEventListener("keydown", keyboard);
      document.body.style.overflow = overflow;
      if (trigger instanceof HTMLElement && trigger.isConnected)
        trigger.focus();
    };
  }, [dispatch]);

  useEffect(() => {
    (
      dialog.current?.querySelector<HTMLElement>("input[type='search']") ??
      dialog.current?.querySelector<HTMLElement>("button")
    )?.focus();
  }, [props.drawer]);

  return dialog;
}

function dialogTargets(dialog: HTMLDivElement | null): HTMLElement[] {
  return Array.from(
    dialog?.querySelectorAll<HTMLElement>(
      "button:not(:disabled), input:not(:disabled), a[href], textarea:not(:disabled), select:not(:disabled), summary, [tabindex='0']",
    ) ?? [],
  ).filter((element) => {
    const closed = element.closest("details:not([open])");
    return !closed || closed.querySelector("summary") === element;
  });
}
