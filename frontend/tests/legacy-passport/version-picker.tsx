import { EXAMPLE_VERSIONS } from "./governance-fixtures";

export function VersionPicker({
  label,
  revision,
  change,
}: {
  label: string;
  revision: number;
  change: (revision: number) => void;
}) {
  return (
    <label>
      {label}
      <select
        value={revision}
        onChange={(event) => change(Number(event.target.value))}
      >
        {EXAMPLE_VERSIONS.map((version) => (
          <option key={version.revision} value={version.revision}>
            Version {version.revision}
            {version.revision === 3 ? " · latest example" : " · historical"}
          </option>
        ))}
      </select>
    </label>
  );
}
