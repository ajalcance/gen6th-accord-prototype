import { creditRoles, type Credit } from "../../lib/persona-credits";
import type { SavedPersonaSource } from "./saved-source";
import CreditEvidencePicker from "./credit-evidence-picker";

type Props = {
  source: SavedPersonaSource;
  versionId: string;
  credits: Credit[];
  change: (rows: Credit[]) => void;
};
export default function CreditFields(props: Props) {
  const { credits, change } = props;
  function update(index: number, changes: Partial<Credit>) {
    change(
      credits.map((row, i) => (i === index ? { ...row, ...changes } : row)),
    );
  }
  return (
    <section
      className="credit-fields"
      aria-label="Structured contributor declarations"
    >
      {credits.map((credit, index) => (
        <CreditRow
          key={index}
          {...props}
          credit={credit}
          index={index}
          update={(changes) => update(index, changes)}
          remove={() => change(credits.filter((_, i) => i !== index))}
        />
      ))}
      <button
        type="button"
        className="secondary"
        disabled={credits.length >= 12}
        onClick={() =>
          change([
            ...credits,
            {
              name: "",
              kind: "human",
              role: "design",
              actor_ref: null,
              evidence_id: null,
            },
          ])
        }
      >
        Add contributor
      </button>
    </section>
  );
}
function CreditRow({
  credit,
  index,
  update,
  remove,
  source,
  versionId,
}: Props & {
  credit: Credit;
  index: number;
  update: (changes: Partial<Credit>) => void;
  remove: () => void;
}) {
  return (
    <fieldset className="credit-row">
      <legend>Contributor {index + 1}</legend>
      <CreditBasics credit={credit} update={update} />
      {credit.kind === "human" && (
        <CreditAccount credit={credit} update={update} />
      )}
      <CreditEvidencePicker
        source={source}
        versionId={versionId}
        selected={credit.evidence_id}
        change={(evidence_id) => update({ evidence_id })}
      />
      <button
        type="button"
        className="text-button"
        aria-label={`Remove contributor ${index + 1}`}
        onClick={remove}
      >
        Remove contributor
      </button>
    </fieldset>
  );
}
type EntryProps = {
  credit: Credit;
  update: (changes: Partial<Credit>) => void;
};
function CreditBasics({ credit, update }: EntryProps) {
  return (
    <>
      <label>
        Name
        <input
          required
          maxLength={80}
          placeholder="Person or organization"
          value={credit.name}
          onChange={(event) => update({ name: event.target.value })}
        />
      </label>
      <label>
        Contributor type
        <select
          value={credit.kind}
          onChange={(event) =>
            update({
              kind: event.target.value as Credit["kind"],
              actor_ref: null,
            })
          }
        >
          <option value="human">Person</option>
          <option value="organization">Organization</option>
        </select>
      </label>
      <label>
        Contribution role
        <select
          value={credit.role}
          onChange={(event) =>
            update({ role: event.target.value as Credit["role"] })
          }
        >
          {creditRoles.map((role) => (
            <option key={role} value={role}>
              {role.replaceAll("_", " ")}
            </option>
          ))}
        </select>
      </label>
    </>
  );
}
function CreditAccount({ credit, update }: EntryProps) {
  return (
    <details>
      <summary>Link an existing contributor account</summary>
      <label>
        Workspace account reference
        <input
          maxLength={64}
          placeholder="Optional · existing member’s account reference"
          value={credit.actor_ref ?? ""}
          onChange={(event) =>
            update({ actor_ref: event.target.value || null })
          }
        />
      </label>
      <p className="help">
        An entered reference remains unconfirmed. The named account must sign in
        and accept this credit. This does not invite or grant access.
      </p>
    </details>
  );
}
