import { useEffect, useRef, useState } from "react";
import {
  PACKAGE_LIMIT,
  parsePackage,
  type SignedPassport,
} from "../../lib/persona-passport-contracts";

export function usePassportInput(clear: () => void) {
  const [value, setValue] = useState(""),
    [error, setError] = useState("");
  const generation = useRef(0);
  useEffect(
    () => () => {
      generation.current++;
    },
    [],
  );
  const change = (next: string) => {
    generation.current++;
    clear();
    setError("");
    setValue(next);
  };
  async function select(file: File | undefined) {
    const turn = ++generation.current;
    clear();
    setValue("");
    setError("");
    if (!file) return;
    if (file.size > PACKAGE_LIMIT) {
      setError("Use a JSON passport within 64 KiB.");
      return;
    }
    try {
      const content = await file.text();
      if (turn !== generation.current) return;
      parsePackage(JSON.parse(content));
      setValue(content);
    } catch {
      if (turn === generation.current)
        setError("This file is not a bounded passport package.");
    }
  }
  const prepare = (): SignedPassport | null => {
    try {
      return parsePackage(JSON.parse(value));
    } catch {
      setError("Use a valid bounded JSON package.");
      return null;
    }
  };
  return { value, error, change, select, prepare };
}
export function PassportPackageInput({
  input,
  disabled,
}: {
  input: ReturnType<typeof usePassportInput>;
  disabled: boolean;
}) {
  return (
    <fieldset disabled={disabled}>
      <legend>Package to verify</legend>
      <label>
        Choose passport JSON
        <input
          type="file"
          accept="application/json,.json"
          onChange={(event) => {
            void input.select(event.target.files?.[0]);
            event.target.value = "";
          }}
        />
      </label>
      <label>
        Passport JSON
        <textarea
          rows={6}
          placeholder="Paste a signed passport package, or choose its JSON file above."
          value={input.value}
          maxLength={PACKAGE_LIMIT}
          onChange={(event) => input.change(event.target.value)}
        />
      </label>
      {input.error && <p role="alert">{input.error}</p>}
    </fieldset>
  );
}
