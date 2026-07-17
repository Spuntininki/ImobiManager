import { describe, expect, it } from "vitest";

import { parseContractPdfError } from "@/lib/contractPdf";

function buildAxiosError({
  status,
  body,
}: {
  status: number;
  body: string;
}): unknown {
  return {
    response: {
      status,
      data: new Blob([body], { type: "application/json" }),
    },
  };
}

// --- Happy path: known missing-doc patterns ----------------------------------

describe("parseContractPdfError", () => {
  it("translates owner_cpf + renter_rg into pt-BR labels", async () => {
    const error = buildAxiosError({
      status: 422,
      body: JSON.stringify({
        detail: "Missing required document(s): owner_cpf, renter_rg",
      }),
    });
    const result = await parseContractPdfError(error);
    expect(result).toBe("Faltam: CPF do proprietário, RG do inquilino.");
  });

  it("translates owner_cpf only", async () => {
    const error = buildAxiosError({
      status: 422,
      body: JSON.stringify({
        detail: "Missing required document(s): owner_cpf",
      }),
    });
    const result = await parseContractPdfError(error);
    expect(result).toBe("Faltam: CPF do proprietário.");
  });

  it("translates all four missing docs", async () => {
    const error = buildAxiosError({
      status: 422,
      body: JSON.stringify({
        detail:
          "Missing required document(s): owner_cpf, owner_rg, renter_cpf, renter_rg",
      }),
    });
    const result = await parseContractPdfError(error);
    expect(result).toBe(
      "Faltam: CPF do proprietário, RG do proprietário, CPF do inquilino, RG do inquilino.",
    );
  });

  // --- Recognized shape, non-matching detail -------------------------------

  it("returns null for a 422 with a non-matching detail", async () => {
    const error = buildAxiosError({
      status: 422,
      body: JSON.stringify({
        detail: "No active contract template with code 'standard'",
      }),
    });
    const result = await parseContractPdfError(error);
    expect(result).toBeNull();
  });

  // --- Other HTTP statuses -------------------------------------------------

  it("returns null for a 404 status", async () => {
    const error = buildAxiosError({
      status: 404,
      body: JSON.stringify({ detail: "Contract not found" }),
    });
    const result = await parseContractPdfError(error);
    expect(result).toBeNull();
  });

  it("returns null for a 500 status", async () => {
    const error = buildAxiosError({
      status: 500,
      body: JSON.stringify({ detail: "Internal server error" }),
    });
    const result = await parseContractPdfError(error);
    expect(result).toBeNull();
  });

  // --- Edge cases: missing/invalid Blob content ----------------------------

  it("returns null when there is no response", async () => {
    const error = { message: "Network Error" };
    const result = await parseContractPdfError(error);
    expect(result).toBeNull();
  });

  it("returns null when response.data is not a Blob", async () => {
    const error = { response: { status: 422, data: { detail: "..." } } };
    const result = await parseContractPdfError(error);
    expect(result).toBeNull();
  });

  it("returns null when the Blob contains invalid JSON", async () => {
    const error = buildAxiosError({
      status: 422,
      body: "this is not json",
    });
    const result = await parseContractPdfError(error);
    expect(result).toBeNull();
  });

  it("returns null when the Blob JSON has no detail field", async () => {
    const error = buildAxiosError({
      status: 422,
      body: JSON.stringify({ message: "something went wrong" }),
    });
    const result = await parseContractPdfError(error);
    expect(result).toBeNull();
  });

  it("returns null when detail is not a string", async () => {
    const error = buildAxiosError({
      status: 422,
      body: JSON.stringify({ detail: 42 }),
    });
    const result = await parseContractPdfError(error);
    expect(result).toBeNull();
  });

  it("handles unknown token gracefully (no known labels)", async () => {
    const error = buildAxiosError({
      status: 422,
      body: JSON.stringify({
        detail: "Missing required document(s): some_unknown_token",
      }),
    });
    const result = await parseContractPdfError(error);
    expect(result).toBeNull();
  });

  it("handles mixed known and unknown tokens gracefully", async () => {
    const error = buildAxiosError({
      status: 422,
      body: JSON.stringify({
        detail:
          "Missing required document(s): owner_cpf, some_unknown_token, renter_rg",
      }),
    });
    const result = await parseContractPdfError(error);
    expect(result).toBe("Faltam: CPF do proprietário, RG do inquilino.");
  });
});
