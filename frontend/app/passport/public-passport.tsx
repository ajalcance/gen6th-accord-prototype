"use client";

import { useCallback, useEffect, useState } from "react";
import Image from "next/image";
import { apiClient } from "../../lib/api-client";
import { parsePublicPage } from "../../lib/persona-publications";
import { uuid } from "../../lib/persona-validation";
import { usePersonaQuery } from "./use-persona-query";
import { GovernanceRead } from "./governance-common";
import { PassportDownload } from "./passport-package-result";
import {
  PassportPackageInput,
  usePassportInput,
} from "./passport-package-input";

type PageResult = ReturnType<typeof parsePublicPage>;
export default function PublicPassport({
  workspace,
  publication,
}: {
  workspace: string;
  publication: string;
}) {
  const { query, state } = usePersonaQuery<PageResult>();
  const verification = usePersonaQuery<PageResult>();
  const [verified, setVerified] = useState<PageResult | null>(null);
  const input = usePassportInput(() => setVerified(null));
  const load = useCallback(
    async (signal: AbortSignal) => {
      const raw = await apiClient.get(
        `/api/public/passports/${uuid(workspace)}/${uuid(publication)}`,
        {
          signal,
          credentials: "omit",
          cache: "no-store",
          mode: "same-origin",
          redirect: "error",
          retries: 0,
        },
      );
      return parsePublicPage(raw, publication);
    },
    [workspace, publication],
  );
  useEffect(() => {
    void query.run(load);
    return () => query.stop();
  }, [query, load]);
  return (
    <main
      className="panel public-passport"
      aria-label="Public persona passport"
    >
      <Image
        unoptimized
        className="public-logo"
        src="/brand/gen6th-accord-dark.svg"
        width={1580}
        height={360}
        alt="Gen6th Accord"
      />
      <h1>AI Persona Passport</h1>
      <p>
        Only owner-approved disclosures appear here. A signature records
        integrity; production permission is checked separately. Recorded
        eligibility applies to the named recipient and scope; viewing this page
        grants no reuse rights.
      </p>
      <GovernanceRead state={state} query={query}>
        {(page) => (
          <>
            <h2>{page.projection.values.name}</h2>
            {page.projection.values.portrait_sha256 && (
              <Image
                unoptimized
                src={`/api/public/passports/${workspace}/${publication}/portrait`}
                width={320}
                height={320}
                alt={`Approved synthetic persona ${page.projection.values.name}`}
              />
            )}
            <dl>
              {Object.entries(page.projection.values)
                .filter(([key]) => key !== "portrait_sha256")
                .map(([key, value]) => (
                  <div key={key}>
                    <dt>{key.replaceAll("_", " ")}</dt>
                    <dd>{value}</dd>
                  </div>
                ))}
            </dl>
            <p>
              Version {page.projection.revision} · approved{" "}
              {page.projection.approved}
            </p>
            <p>
              Recorded scope: {page.projection.from} to {page.projection.until}
            </p>
            <p role="status">
              Signature: {page.integrity}. Current production use:{" "}
              {page.currentUse}. Checked {page.evaluated}.
            </p>
            <button
              onClick={() => {
                setVerified(null);
                void query.run(load);
              }}
            >
              Refresh current permission
            </button>
            <PassportDownload package_={page.packet} />
            <PassportPackageInput
              input={input}
              disabled={verification.state.phase === "loading"}
            />
            <button
              disabled={!input.value || verification.state.phase === "loading"}
              onClick={() => {
                const packet = input.prepare();
                if (packet)
                  void verification.query.run(async (signal) => {
                    const raw = await apiClient.post(
                      `/api/public/passports/${uuid(workspace)}/${uuid(publication)}/verify`,
                      packet,
                      {
                        signal,
                        credentials: "omit",
                        cache: "no-store",
                        mode: "same-origin",
                        redirect: "error",
                        retries: 0,
                      },
                    );
                    const result = parsePublicPage(raw, publication);
                    if (!signal.aborted) setVerified(result);
                    return result;
                  });
              }}
            >
              Verify downloaded public package
            </button>
            <GovernanceRead
              state={verification.state}
              query={verification.query}
            >
              {() => null}
            </GovernanceRead>
            {verified && (
              <p role="status">
                Uploaded package: {verified.integrity}. Current use:{" "}
                {verified.currentUse}.
              </p>
            )}
          </>
        )}
      </GovernanceRead>
    </main>
  );
}
