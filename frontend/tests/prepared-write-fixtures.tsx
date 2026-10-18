import { render } from "@testing-library/react";
import { vi } from "vitest";
import type { ReactNode } from "react";
import {
  personaGateway,
  type PersonaOperation,
  type PersonaTransport,
} from "../lib/persona-gateway";
import {
  parseVersion,
  parseReview,
  parseDecision,
} from "../lib/persona-receipts";
import { parseCampaign } from "../lib/persona-campaign-receipts";
import {
  parseSave,
  parseReviewCommand,
  parseOffer,
  parseDecisionCommand,
} from "../lib/persona-commands";
import PreparedWriteWorkspace from "../app/passport/prepared-write-workspace";
import {
  WriteDraftContext,
  type WriteDraftStore,
} from "../app/passport/prepared-write-state";
import type { SavedPersonaSource } from "../app/passport/saved-source";
import wire from "./fixtures/persona-wire.json";

export const version = parseVersion(wire.version),
  campaign = parseCampaign(wire.campaign);
export function receipt(operation: PersonaOperation, body: unknown) {
  switch (operation) {
    case "save": {
      const command = parseSave(body);
      return {
        ...version,
        revision: command.expected_revision + 1,
        content: command.content,
      };
    }
    case "review": {
      const command = parseReviewCommand(body);
      return {
        ...parseReview(wire.review),
        id: "00000000-0000-4000-8000-000000000041",
        ordinal: command.expected_previous_id === null ? 1 : 2,
        decision: command.decision,
        statement: command.statement,
      };
    }
    case "offer": {
      const command = parseOffer(body);
      return { ...campaign, scope: command.scope };
    }
    case "decide": {
      const command = parseDecisionCommand(body);
      return {
        ...parseDecision(wire.decision),
        id: "00000000-0000-4000-8000-000000000042",
        ordinal: command.expected_previous_id === null ? 1 : 2,
        decision: command.decision,
        statement: command.statement,
      };
    }
    default:
      throw new Error("Unexpected synthetic write operation");
  }
}
export function preparedSource(write?: PersonaTransport): SavedPersonaSource {
  const read = vi.fn<PersonaTransport>(async (operation) => {
    switch (operation) {
      case "load":
        return wire.version;
      case "gallery":
        return wire.gallery;
      case "reviewHistory":
        return wire.reviewHistory;
      case "campaignOffers":
        return { items: [wire.campaign], next_after_id: null };
      case "campaignStatus":
        return wire.status;
      default:
        throw new Error("Unexpected synthetic read operation");
    }
  });
  return {
    workspaceId: version.workspace_id,
    workspaceLabel: "Synthetic workspace",
    sessionKey: "synthetic-session",
    gateway: personaGateway(version.workspace_id, read),
    writeGateway: personaGateway(
      version.workspace_id,
      write ??
        (async (operation, _workspace, body) => receipt(operation, body)),
    ),
    assets: [{ version_id: version.version_id, assets: campaign.assets }],
  };
}
export function draftProvider(store: WriteDraftStore, children: ReactNode) {
  return (
    <WriteDraftContext.Provider value={store}>
      {children}
    </WriteDraftContext.Provider>
  );
}
export function mountPrepared(
  source: SavedPersonaSource,
  store: WriteDraftStore = new Map(),
  denied = vi.fn(),
) {
  const element = (value: SavedPersonaSource) =>
    draftProvider(
      store,
      <PreparedWriteWorkspace
        key={value.sessionKey}
        source={value}
        version={version}
        denied={denied}
      />,
    );
  const mounted = render(element(source));
  return { ...mounted, store, denied, element };
}
