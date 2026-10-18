import Image from "next/image";
import type {
  CampaignReceipt,
  PersonaVersion,
} from "../../lib/persona-contracts";
import type { BookletRead } from "./booklet-read";
import {
  BookletFooter,
  BookletQr,
  BookletRule,
  BookletSeal,
} from "./booklet-ornaments";
import type { bookletShare } from "../../lib/passport-booklet";

type Props = {
  version: PersonaVersion;
  offer: CampaignReceipt | null;
  data: BookletRead | null;
  share: ReturnType<typeof bookletShare>;
};
export default function BookletRecords({ version, offer, data, share }: Props) {
  const issued = !!data?.signature && !!share;
  return (
    <section
      className="booklet-page record-page"
      aria-label="Evidence and permissions page"
    >
      <RecordHeading issued={issued} />
      <RecordEntries version={version} offer={offer} data={data} />
      <SignaturePanel issued={issued} share={share} />
      <PermissionNote data={data} offer={offer} />
      <BookletFooter
        page="02"
        message={
          issued
            ? "Creator statements are not independently verified"
            : "Registration record, not yet signed"
        }
      />
    </section>
  );
}
function RecordSection({
  number,
  title,
  summary,
  detail,
}: {
  number: string;
  title: string;
  summary: string;
  detail: string;
}) {
  return (
    <li>
      <span className="record-number">{number}</span>
      <div>
        <h4>{title}</h4>
        <p className="section-summary">{summary}</p>
        <p className="record-detail">{detail}</p>
      </div>
      <span className="number-rosette" aria-hidden="true">
        {number}
      </span>
    </li>
  );
}
function permissionDetail(offer: CampaignReceipt): string {
  const { scope } = offer;
  return `Recorded offer: ${scope.name}. Assets: ${offer.assets.map((asset) => asset.label).join(", ")}. Recipient: ${scope.recipient_ref}. Purpose: ${scope.purpose}. Conditions: ${scope.conditions}. Dates: ${scope.starts_at} – ${scope.ends_at}.`;
}
function PermissionNote({ data, offer }: Pick<Props, "data" | "offer">) {
  return (
    <div className="permission-note">
      <p>Current permission is checked separately.</p>
      <p>
        {data?.status
          ? `${data.status.eligible_for_use ? "Eligible" : "Blocked"} at ${data.status.evaluated_at}. Refresh before use.`
          : offer
            ? "Current permission unavailable. Refresh before use."
            : "No production offer — no permission is inferred."}
      </p>
      {data?.publication && (
        <p>
          Share approval loaded from private history. Public availability is
          checked when the link is opened.
        </p>
      )}
    </div>
  );
}

function RecordHeading({ issued }: { issued: boolean }) {
  return (
    <header className="record-heading">
      <Image
        unoptimized
        className="accord-logo"
        src="/passport-booklet/accord-logo.svg"
        width={660}
        height={150}
        alt="Gen6th Accord"
      />
      <h3>
        {issued ? "Passport issued" : "Registration record"} by Gen6th Accord
      </h3>
      <BookletRule />
    </header>
  );
}
function RecordEntries({
  version,
  offer,
  data,
}: Pick<Props, "version" | "offer" | "data">) {
  const count = data?.signature?.references ?? data?.profile?.references.length;
  return (
    <ol className="record-sections">
      <RecordSection
        number="01"
        title="Approved references"
        summary={
          count === undefined
            ? "Approved references unavailable"
            : count
              ? `${count} approved portrait reference${count === 1 ? "" : "s"}`
              : "No approved portrait reference"
        }
        detail={
          data?.signature
            ? "Reference count from the signed package. Reference approval does not establish identity or ownership."
            : "Reference approval does not establish identity or ownership."
        }
      />
      <RecordSection
        number="02"
        title="Creation evidence"
        summary="Human contribution + AI disclosure"
        detail={`Creator statements:\nHuman contribution: ${version.content.human_contribution}\nAI disclosure: ${version.content.ai_disclosure}`}
      />
      <RecordSection
        number="03"
        title="Recorded permissions"
        summary={
          offer
            ? "Assets · recipient · purpose · dates"
            : "No production offer selected"
        }
        detail={
          offer
            ? permissionDetail(offer)
            : "No recipient, assets, purpose or dates are inferred."
        }
      />
    </ol>
  );
}
function SignaturePanel({
  issued,
  share,
}: Pick<Props, "share"> & { issued: boolean }) {
  return issued && share ? (
    <div className="signed-panel">
      <BookletSeal />
      <div className="signature-caption">
        <strong>
          Digitally signed
          <br />
          record
        </strong>
        <BookletRule />
        <a href={share.url} target="_blank" rel="noopener noreferrer">
          Open approved public passport
        </a>
      </div>
      <BookletQr modules={share.modules} />
    </div>
  ) : (
    <div className="unsigned-panel">
      <strong>Registration record, not yet signed</strong>
      <p>
        A verified signed package and an approved public share link are required
        for this issued display.
      </p>
    </div>
  );
}
