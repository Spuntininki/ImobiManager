/**
 * Parse a contract PDF download error into a user-friendly pt-BR message.
 *
 * When the endpoint returns 422 with `responseType: "blob"`, axios leaves
 * the JSON body as an unparsed Blob.  This helper reads the Blob, extracts
 * the `detail` string, and — when it matches the known
 * "Missing required document(s): ..." pattern — translates the internal
 * token names into readable pt-BR labels for the user.
 *
 * Returns `null` for any unrecognised error shape, so the caller can fall
 * back to its generic toast message without leaking English internals.
 */

import type { AxiosError } from "axios";

// Matches the ValueError raised by contract_pdf_service._fetch_contract_data.
const MISSING_DOCS_RE = /^Missing required document\(s\): (.+)$/;

// Maps internal document tokens to pt-BR labels shown to the end user.
const DOC_LABELS: Record<string, string> = {
  owner_cpf: "CPF do proprietário",
  owner_rg: "RG do proprietário",
  renter_cpf: "CPF do inquilino",
  renter_rg: "RG do inquilino",
};

function translateMissingDocs(missingTokens: string[]): string | null {
  const labels = missingTokens
    .map((t) => DOC_LABELS[t.trim()])
    .filter(Boolean);
  return labels.length > 0 ? `Faltam: ${labels.join(", ")}.` : null;
}

export async function parseContractPdfError(
  error: unknown,
): Promise<string | null> {
  const axiosErr = error as AxiosError;
  if (!axiosErr.response || axiosErr.response.status !== 422) {
    return null;
  }

  const data = axiosErr.response.data;
  if (!data || typeof data !== "object" || !(data instanceof Blob)) {
    return null;
  }

  let body: string;
  try {
    body = await data.text();
  } catch {
    return null;
  }

  let detail: string;
  try {
    const parsed = JSON.parse(body) as Record<string, unknown>;
    detail = typeof parsed.detail === "string" ? parsed.detail : "";
  } catch {
    return null;
  }

  const match = detail.match(MISSING_DOCS_RE);
  if (!match) {
    return null;
  }

  const tokens = match[1]!.split(",").map((t) => t.trim());
  return translateMissingDocs(tokens);
}
