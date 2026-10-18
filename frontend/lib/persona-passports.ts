import { apiClient } from "./api-client";
import type { CampaignReceipt, PersonaVersion } from "./persona-contracts";
import {
  bindExport,
  parsePackage,
  parseReadiness,
  parseVerification,
  type SignedPassport,
  type PassportReadiness,
  type PassportVerification,
} from "./persona-passport-contracts";
import {
  hex,
  list,
  object,
  requireContract,
  text,
  uuid,
} from "./persona-validation";

export type PassportGateway = {
  workspaceId: string;
  readiness(signal: AbortSignal): Promise<PassportReadiness>;
  assets(
    version: string,
    signal: AbortSignal,
  ): Promise<CampaignReceipt["assets"]>;
  export(
    version: PersonaVersion,
    offer: CampaignReceipt,
    signal: AbortSignal,
  ): Promise<SignedPassport>;
  verify(
    campaign: string,
    package_: SignedPassport,
    signal: AbortSignal,
  ): Promise<PassportVerification>;
};
export function passportGateway(workspace: string): PassportGateway {
  const workspaceId = uuid(workspace);
  const post = passportPost(workspaceId);
  return passportActions(workspaceId, post);
}
type Post = (
  route: string,
  body: unknown,
  signal: AbortSignal,
) => Promise<unknown>;
function passportPost(workspaceId: string): Post {
  const post = async (route: string, body: unknown, signal: AbortSignal) => {
    requireContract(!signal.aborted);
    const result = await apiClient.post<unknown>(
      `/api/workspaces/${workspaceId}/personas/passports/${route}`,
      body,
      {
        signal,
        credentials: "same-origin",
        mode: "same-origin",
        cache: "no-store",
        redirect: "error",
        retries: 0,
        timeoutMs: 30000,
      },
    );
    requireContract(!signal.aborted);
    return result;
  };
  return post;
}
function passportActions(workspaceId: string, post: Post): PassportGateway {
  return {
    workspaceId,
    async readiness(signal) {
      return parseReadiness(await post("readiness", {}, signal), workspaceId);
    },
    async assets(version, signal) {
      return parseAssets(
        await post("assets", { version_id: uuid(version) }, signal),
        workspaceId,
        version,
      );
    },
    async export(version, offer, signal) {
      requireContract(
        version.workspace_id === workspaceId &&
          offer.workspace_id === workspaceId &&
          offer.version_id === version.version_id,
      );
      const package_ = parsePackage(
        await post("export", { campaign_id: uuid(offer.id) }, signal),
      );
      bindExport(package_, version, offer);
      return package_;
    },
    async verify(campaign, package_, signal) {
      return parseVerification(
        await post(
          "verify",
          { campaign_id: uuid(campaign), package: parsePackage(package_) },
          signal,
        ),
        workspaceId,
        campaign,
      );
    },
  };
}
function parseAssets(
  value: unknown,
  workspace: string,
  version: string,
): CampaignReceipt["assets"] {
  const row = object(value, ["workspace_id", "version_id", "assets"]);
  requireContract(
    uuid(row.workspace_id) === workspace && uuid(row.version_id) === version,
  );
  const assets = list(
    row.assets,
    (value) => {
      const item = object(value, ["id", "digest", "label"]);
      return {
        id: uuid(item.id),
        digest: hex(item.digest, 64),
        label: text(item.label, 80),
      };
    },
    20,
  );
  requireContract(
    new Set(assets.map((item) => item.id)).size === assets.length,
  );
  return assets;
}
