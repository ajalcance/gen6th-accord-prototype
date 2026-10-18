import Image from "next/image";
import {
  bookletMachineLine,
  bookletReference,
  type BookletSignature,
} from "../../lib/passport-booklet";
import type {
  CampaignReceipt,
  PersonaVersion,
} from "../../lib/persona-contracts";
import { BookletFooter, BookletRule } from "./booklet-ornaments";

type Props = {
  version: PersonaVersion;
  offer: CampaignReceipt | null;
  portrait: string | null;
  portraitMessage: string;
  signature: BookletSignature | null;
  issued: boolean;
};
export default function BookletIdentity(props: Props) {
  const { version, offer, portrait, portraitMessage, signature, issued } =
    props;
  return (
    <section
      className="booklet-page identity-page"
      aria-label="Performer record page"
    >
      {portrait && (
        <Image
          unoptimized
          className="portrait-watermark"
          src={portrait}
          width={512}
          height={700}
          alt=""
          aria-hidden="true"
        />
      )}
      <IdentityHeading issued={issued} />
      <div className="identity-layout">
        <div className="booklet-portrait">
          {portrait ? (
            <Image
              unoptimized
              src={portrait}
              width={512}
              height={700}
              alt={`Approved reference for ${version.content.name}`}
            />
          ) : (
            <div className="empty-portrait">
              <span aria-hidden="true">◇</span>
              <p>{portraitMessage}</p>
            </div>
          )}
        </div>
        <IdentityFields version={version} offer={offer} signature={signature} />
      </div>
      <div className="machine-line" aria-hidden="true">
        {bookletMachineLine(version, offer)}
      </div>
      <BookletFooter
        page="01"
        message="Accord record, not a government document"
      />
    </section>
  );
}
function IdentityFields({
  version,
  offer,
  signature,
}: Pick<Props, "version" | "offer" | "signature">) {
  const fields = [
    ["Persona name", version.content.name, ""],
    [
      "Passport reference",
      bookletReference(offer),
      offer
        ? "Derived from production offer; not a registry number"
        : "No production offer",
    ],
    ["Signing key version", signature?.key ?? "Not signed", ""],
    [
      "Date of issue",
      signature ? new Date(signature.issued).toISOString() : "Not issued",
      signature ? "Signed package issue time (UTC)" : "",
    ],
    ["Issuing authority", "Gen6th Accord", ""],
  ];
  return (
    <dl className="identity-fields">
      {fields.map(([label, value, note]) => (
        <div key={label}>
          <dt>{label}</dt>
          <dd>{value}</dd>
          {note && <dd className="field-note">{note}</dd>}
        </div>
      ))}
    </dl>
  );
}

function IdentityHeading({ issued }: { issued: boolean }) {
  return (
    <header className="identity-heading">
      <p className="authority-kicker">
        <span />
        GEN6TH ACCORD
        <span />
      </p>
      <h3>Persona Passport</h3>
      <p className="identity-state">
        {issued ? "REGISTERED IDENTITY" : "REGISTERED PREVIEW"}
      </p>
      <BookletRule />
    </header>
  );
}
