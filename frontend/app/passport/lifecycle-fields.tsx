import {
  TextFields,
  type WriteDraftState,
  type TextFieldSpec,
} from "./prepared-write-common";

export default function LifecycleFields({
  draft,
  field,
  label,
  options,
  specs,
}: {
  draft: WriteDraftState;
  field: string;
  label: string;
  options: { value: string; label: string; disabled?: boolean }[];
  specs: TextFieldSpec[];
}) {
  return (
    <>
      <label>
        {label}
        <select
          value={draft.fields[field]}
          onChange={(e) => draft.change(field, e.target.value)}
        >
          {options.map((option) => (
            <option
              key={option.value}
              value={option.value}
              disabled={option.disabled}
            >
              {option.label}
            </option>
          ))}
        </select>
      </label>
      <TextFields draft={draft} specs={specs} />
    </>
  );
}
