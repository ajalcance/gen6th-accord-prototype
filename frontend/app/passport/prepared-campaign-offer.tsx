import { useCallback } from "react";
import type {
  CampaignReceipt,
  PersonaVersion,
} from "../../lib/persona-contracts";
import { requireContract, uuid } from "../../lib/persona-validation";
import type { SavedPersonaSource } from "./saved-source";
import { useGovernanceRead } from "./saved-governance-read";
import { GovernanceRead } from "./governance-common";
import { usePreparedWrite, useWriteDraft } from "./prepared-write-state";
import { ProductionUseFields, productionReady } from "./production-use-fields";
import { productionDraft } from "../../lib/persona-production";
import { ProductionAssets } from "./production-assets";
import {
  writeKey,
  WriteFeedback,
  ReloadWrite,
  SubmitWriteForm,
  TextFields,
  type TextFieldSpec,
  type WriteDraftState,
} from "./prepared-write-common";

type Props = {
  source: SavedPersonaSource;
  version: PersonaVersion;
  denied: () => void;
};
type Assets = CampaignReceipt["assets"];
const initialOffer = {
  name: "",
  recipient: "",
  purpose: "",
  conditions: "",
  starts: "",
  ends: "",
  assets: "",
  confirm: "",
  production: "",
  productionTitle: "",
  episode: "",
  roleName: "",
  adaptation: "",
  references: "",
};
function inventory(
  source: SavedPersonaSource,
  version: PersonaVersion,
): Assets | null {
  try {
    const rows =
      source.assets?.filter((row) => row.version_id === version.version_id) ??
      [];
    requireContract(rows.length === 1);
    const assets = rows[0].assets;
    requireContract(
      assets.length > 0 &&
        assets.length <= 20 &&
        new Set(assets.map((row) => row.id)).size === assets.length,
    );
    for (const row of assets) {
      uuid(row.id);
      requireContract(
        /^[0-9a-f]{64}$/.test(row.digest) &&
          row.label.trim().length > 0 &&
          row.label.length <= 80,
      );
    }
    return assets;
  } catch {
    return null;
  }
}
export default function PreparedCampaignOffer(props: Props) {
  const assets = inventory(props.source, props.version);
  if (!assets)
    return (
      <ProductionAssets {...props}>
        {(assets) => <OfferForm {...props} assets={assets} />}
      </ProductionAssets>
    );
  return <OfferForm {...props} assets={assets} />;
}
function useOfferWrite({
  source,
  version,
  denied,
  assets,
}: Props & { assets: Assets }) {
  const key = writeKey(source, "offer", version.version_id);
  const draft = useWriteDraft(key, initialOffer);
  const mutation = usePreparedWrite(source.writeGateway!, "offer", key, denied);
  const load = useCallback(
    (signal: AbortSignal) =>
      source.gateway.reads.reviewHistory(
        version.version_id,
        { before_ordinal: null, limit: 1 },
        signal,
      ),
    [source.gateway, version.version_id],
  );
  const read = useGovernanceRead(load);
  const ids = (draft.fields.assets ?? "")
    .split(",")
    .filter(Boolean)
    .filter((id) => assets.some((row) => row.id === id));
  const submit = (reviewId: string) =>
    void mutation.submit({
      request_id: crypto.randomUUID(),
      version_id: version.version_id,
      review_id: reviewId,
      scope: {
        name: draft.fields.name,
        recipient_ref: draft.fields.recipient,
        asset_ids: ids,
        purpose: draft.fields.purpose,
        conditions: draft.fields.conditions,
        starts_at: draft.fields.starts,
        ends_at: draft.fields.ends,
        ...(draft.fields.production === "yes"
          ? { production: productionDraft(draft.fields) }
          : {}),
      },
    });
  return { draft, mutation, load, ...read, ids, submit };
}
const fields: TextFieldSpec[] = [
  {
    field: "name",
    label: "Campaign name",
    max: 80,
    multiline: false,
    placeholder: "Name this use or campaign.",
  },
  {
    field: "recipient",
    label: "Named recipient",
    max: 64,
    multiline: false,
    placeholder: "Enter the authorized recipient reference.",
  },
  {
    field: "purpose",
    label: "Campaign purpose",
    placeholder: "Describe how the selected assets may be used.",
  },
  {
    field: "conditions",
    label: "Campaign conditions",
    placeholder: "Set the limits and required conditions for this use.",
  },
  {
    field: "starts",
    label: "Starts at (include timezone)",
    placeholder: "YYYY-MM-DDTHH:mm:ssZ",
    max: 40,
    multiline: false,
  },
  {
    field: "ends",
    label: "Ends at (include timezone)",
    placeholder: "YYYY-MM-DDTHH:mm:ssZ",
    max: 40,
    multiline: false,
  },
];
function OfferForm(props: Props & { assets: Assets }) {
  const action = useOfferWrite(props),
    { draft, mutation, state, query, load } = action;
  return (
    <section aria-label="Offer a scoped campaign">
      <h3>Offer a campaign · version {props.version.revision}</h3>
      <GovernanceRead state={state} query={query}>
        {(page) =>
          page.items[0]?.decision === "approved" ? (
            <OfferEditor
              props={props}
              action={action}
              reviewId={page.items[0].id}
            />
          ) : (
            <p>
              A current independent approval of this exact version is required
              before an offer.
            </p>
          )
        }
      </GovernanceRead>
      <WriteFeedback {...mutation} retry={() => void mutation.retry()} />
      <ReloadWrite
        draft={draft}
        mutation={mutation}
        loading={state.phase === "loading"}
        reload={() => void query.run(load)}
        label="Reload approval before a new offer"
      />
    </section>
  );
}
function OfferEditor({
  props,
  action,
  reviewId,
}: {
  props: Props & { assets: Assets };
  action: ReturnType<typeof useOfferWrite>;
  reviewId: string;
}) {
  const { draft, mutation, ids } = action;
  const ready =
    ids.length > 0 &&
    fields.every((spec) => draft.fields[spec.field]?.trim()) &&
    productionReady(draft.fields);
  return (
    <SubmitWriteForm
      draft={draft}
      mutation={mutation}
      ready={ready}
      label="Record offer"
      confirmation={
        "I authorize only the selected assets for this recipient, purpose, duration and conditions." +
        (draft.fields.production === "yes"
          ? " I share the named production, role and submitted reference IDs with that recipient."
          : "")
      }
      submit={() => action.submit(reviewId)}
    >
      <TextFields specs={fields} draft={draft} />
      <AssetSelection draft={draft} assets={props.assets} ids={ids} />
      <ProductionUseFields
        draft={draft}
        source={props.source}
        versionId={props.version.version_id}
      />
      <OfferSummary
        fields={draft.fields}
        assets={props.assets.filter((asset) => ids.includes(asset.id))}
      />
    </SubmitWriteForm>
  );
}
function OfferSummary({
  fields: values,
  assets,
}: {
  fields: Record<string, string>;
  assets: Assets;
}) {
  return (
    <section className="offer-summary" aria-label="Offer summary">
      <h4>Review this scope</h4>
      <dl className="saved-fields">
        {[
          ["Recipient", values.recipient || "Not entered"],
          ["Purpose", values.purpose || "Not entered"],
          [
            "Duration",
            `${values.starts || "Start needed"} → ${values.ends || "End needed"}`,
          ],
          [
            "Permitted assets",
            assets.map((asset) => asset.label).join(", ") || "None selected",
          ],
          [
            "Production role",
            values.production === "yes"
              ? `${values.productionTitle || "Title needed"} · ${values.roleName || "Role needed"}`
              : "No named production",
          ],
        ].map(([label, value]) => (
          <div key={label}>
            <dt>{label}</dt>
            <dd>{value}</dd>
          </div>
        ))}
      </dl>
    </section>
  );
}
function AssetSelection({
  draft,
  assets,
  ids,
}: {
  draft: WriteDraftState;
  assets: Assets;
  ids: string[];
}) {
  return (
    <fieldset>
      <legend>Permitted assets</legend>
      {assets.map((asset) => (
        <label className="prepared-confirm" key={asset.id}>
          <input
            type="checkbox"
            checked={ids.includes(asset.id)}
            onChange={(event) =>
              draft.change(
                "assets",
                (event.target.checked
                  ? [...ids, asset.id]
                  : ids.filter((id) => id !== asset.id)
                ).join(","),
              )
            }
          />
          {asset.label}
        </label>
      ))}
    </fieldset>
  );
}
