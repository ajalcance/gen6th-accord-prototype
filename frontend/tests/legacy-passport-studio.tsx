"use client";
import { useEffect, useRef, useState } from "react";
import { useStudio } from "./legacy-passport/use-studio";
import {
  ConsoleHeader,
  JourneyHeading,
  JourneySidebar,
} from "./legacy-passport/console-shell";
import Gallery from "./legacy-passport/gallery";
import Creation from "./legacy-passport/creation";
import Review from "./legacy-passport/review";
import Campaign from "./legacy-passport/campaign";
import PublicPassport from "./legacy-passport/publicpassport";
import ConsoleDrawer from "./legacy-passport/console-drawer";
import ConsoleFooter from "../app/passport/console-footer";
import {
  SavedSourceContext,
  type SavedPersonaSource,
} from "../app/passport/saved-source";
import type { StudioState } from "./legacy-passport/use-studio";
import type { ConsoleState } from "./legacy-passport/console-types";
import {
  WriteDraftContext,
  type WriteDraftStore,
} from "../app/passport/prepared-write-state";

export default function PassportStudio({
  savedSource = null,
  initialState,
}: {
  savedSource?: SavedPersonaSource | null;
  initialState?: ConsoleState;
  sessionAction?: { label: string; run: () => void };
}) {
  const [writeDrafts] = useState<WriteDraftStore>(() => new Map());
  return (
    <SavedSourceContext.Provider value={savedSource}>
      <WriteDraftContext.Provider value={writeDrafts}>
        {initialState && <StudioWorkspace initialState={initialState} />}
      </WriteDraftContext.Provider>
    </SavedSourceContext.Provider>
  );
}

function useWorkspaceNavigation(props: StudioState) {
  const { dispatch } = props;
  const mainRef = useRef<HTMLElement>(null);
  const previousStep = useRef(props.step);
  useEffect(() => {
    if (previousStep.current !== props.step)
      mainRef.current?.querySelector("h1")?.focus();
    previousStep.current = props.step;
  }, [props.step]);
  useEffect(() => {
    function shortcuts(event: KeyboardEvent) {
      if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === "k") {
        event.preventDefault();
        dispatch({ type: "drawer", value: "commands" });
      }
    }
    document.addEventListener("keydown", shortcuts);
    return () => document.removeEventListener("keydown", shortcuts);
  }, [dispatch]);
  return mainRef;
}

function StudioWorkspace({ initialState }: { initialState: ConsoleState }) {
  const props = useStudio(initialState);
  const mainRef = useWorkspaceNavigation(props);
  const [saved, setSaved] = useState(false);
  return (
    <div className="console-root">
      <a
        href="#workspace-main"
        className="skip-link"
        inert={props.drawer !== null}
      >
        Skip to workspace
      </a>
      <div className="studio" inert={props.drawer !== null}>
        <JourneySidebar {...props} />
        <div className="main-shell">
          <ConsoleHeader {...props} />
          <main ref={mainRef} id="workspace-main">
            <JourneyHeading {...props} saved={saved} />
            {props.step === 0 && (
              <Gallery {...props} saved={saved} setSaved={setSaved} />
            )}
            {props.step === 1 && <Creation {...props} />}
            {props.step === 2 && <Review {...props} />}
            {props.step === 3 && <Campaign {...props} />}
            {props.step === 4 && <PublicPassport {...props} />}
          </main>
          <ConsoleFooter {...props} />
        </div>
      </div>
      {props.drawer !== null && <ConsoleDrawer {...props} />}
    </div>
  );
}
