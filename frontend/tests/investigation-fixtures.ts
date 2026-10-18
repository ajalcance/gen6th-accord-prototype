/** Synthetic server packet; no actual Gemini or performer accuracy evidence. */
import type {
  InvestigationCommand,
  InvestigationResult,
} from "../lib/persona-investigation-contracts";
import { command, queryReceipt, similarityPage } from "./similarity-fixtures";
export function investigationCommand(): InvestigationCommand {
  const candidate = similarityPage().items[0];
  return {
    ...command,
    version_id: candidate.version.version_id,
    portrait_id: candidate.portrait_id,
    generation_id: candidate.generation_id,
    source_note: "Supplied frame, context unverified",
    retain_findings: true,
  };
}
export function investigationResult(
  intent = investigationCommand(),
): InvestigationResult {
  const page = similarityPage(),
    receipt = queryReceipt();
  return {
    id: "00000000-0000-4000-8000-000000000090",
    workspace_id: receipt.workspace_id,
    version_id: intent.version_id,
    portrait_id: intent.portrait_id,
    generation_id: intent.generation_id,
    request_id: intent.request_id,
    ordinal: 1,
    actor_ref: "synthetic-human",
    recorded_at: receipt.issued_at,
    source_note: intent.source_note,
    query: { ...receipt, query_id: intent.query_id },
    reference_sha256: "a".repeat(64),
    reference_face: page.items[0].face,
    search: {
      request_id: intent.request_id,
      method: page.method,
      policy_id: page.policy_id,
      evidence_sha256: page.evidence_sha256,
      scope: intent.scope,
      face_index: intent.face_index,
      face_cosine: page.items[0].face_cosine,
      whole_cosine: page.items[0].whole_cosine,
    },
    model: "synthetic-model",
    provider_revision: "fixture-v1",
    recipe: "grounded-comparison-v1",
    findings: {
      state: "observations",
      observations: [
        {
          label: "pose_differs",
          citations: ["query_image", "approved_reference"],
        },
      ],
    },
    gaps: [
      "identity_not_established",
      "rights_not_verified",
      "source_context_unverified",
    ],
  };
}
