import { useState, type KeyboardEvent } from "react";
import Icon from "../../app/passport/icons";
import type { StudioState } from "./use-studio";
import { STEPS } from "./console-shell";

const CONSOLE_COMMANDS = [
  { name: "Evidence & decisions", drawer: "governance" },
  { name: "Connection & readiness", drawer: "operations" },
  { name: "Activity & versions", drawer: "records" },
  { name: "Demo guide", drawer: "assistant" },
] as const;

function moveCommandFocus(event: KeyboardEvent<HTMLDivElement>) {
  if (event.key !== "ArrowDown" && event.key !== "ArrowUp") return;
  const buttons = Array.from(
    event.currentTarget.querySelectorAll<HTMLButtonElement>("button"),
  );
  if (!buttons.length) return;
  event.preventDefault();
  const index = buttons.indexOf(document.activeElement as HTMLButtonElement);
  const next =
    index < 0
      ? event.key === "ArrowDown"
        ? 0
        : buttons.length - 1
      : (index + (event.key === "ArrowDown" ? 1 : -1) + buttons.length) %
        buttons.length;
  buttons[next]?.focus();
}

export function CommandContent(props: StudioState) {
  const [query, setQuery] = useState("");
  const screens = STEPS.map((name, step) => ({ name, step })).filter((item) =>
    item.name.toLowerCase().includes(query.toLowerCase()),
  );
  const personas = matchingPersonas(props, query);
  return (
    <div className="drawer-body" onKeyDown={moveCommandFocus}>
      <label className="search-field">
        <Icon name="search" />
        <input
          type="search"
          aria-label="Find a screen or persona"
          placeholder="Find a screen or persona…"
          value={query}
          onChange={(event) => setQuery(event.target.value.slice(0, 80))}
        />
      </label>
      <p className="eyebrow">GO TO</p>
      <div className="command-list">
        {screens.map((item) => (
          <button
            key={item.step}
            onClick={() => {
              props.setStep(item.step);
              props.setDrawer(null);
            }}
          >
            <span>{item.name}</span>
            <Icon name="arrow" />
          </button>
        ))}
      </div>
      <PersonaCommands {...props} query={query} />
      <ConsoleCommands {...props} query={query} />
      {screens.length + personas.length === 0 &&
        !CONSOLE_COMMANDS.some((item) =>
          item.name.toLowerCase().includes(query.toLowerCase()),
        ) && (
          <p role="status" className="empty-state">
            No matching screens or personas. Try a different search.
          </p>
        )}
    </div>
  );
}

function ConsoleCommands(props: StudioState & { query: string }) {
  return (
    <div className="command-list">
      {CONSOLE_COMMANDS.filter((item) =>
        item.name.toLowerCase().includes(props.query.toLowerCase()),
      ).map((item) => (
        <button key={item.drawer} onClick={() => props.setDrawer(item.drawer)}>
          {item.name}
          <Icon name="arrow" />
        </button>
      ))}
    </div>
  );
}

function matchingPersonas(props: StudioState, query: string) {
  return props.records
    .map((record, index) => ({
      name: record.draft.name || "Untitled fixture",
      index,
    }))
    .filter((item) => item.name.toLowerCase().includes(query.toLowerCase()));
}
function PersonaCommands(props: StudioState & { query: string }) {
  const personas = matchingPersonas(props, props.query);
  return (
    <>
      <p className="eyebrow">PERSONAS</p>
      <div className="command-list">
        {personas.map((item) => (
          <button
            key={item.index}
            onClick={() => props.setSelected(item.index)}
          >
            <span>{item.name}</span>
            <span className="muted">Fixture</span>
          </button>
        ))}
      </div>
    </>
  );
}
