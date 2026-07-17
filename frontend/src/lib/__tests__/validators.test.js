import { describe, expect, it } from "vitest";

import {
  validateDocument,
  validateEmail,
  validateName,
  validatePassword,
  validatePhone,
  validateRequiredText,
  validateState,
  validateZipCode,
} from "@/lib/validators";

// --- validatePhone ----------------------------------------------------------

describe("validatePhone", () => {
  it("accepts 10-digit landline", () => {
    expect(validatePhone("1199999999")).toBe(null);
  });
  it("accepts 11-digit mobile", () => {
    expect(validatePhone("11999999999")).toBe(null);
  });
  it("rejects empty when required", () => {
    expect(validatePhone("")).toBe("Telefone é obrigatório.");
  });
  it("accepts empty when optional", () => {
    expect(validatePhone("", { required: false })).toBe(null);
  });
  it("rejects too-short input", () => {
    expect(validatePhone("999")).toBe("Telefone deve ter 10 ou 11 dígitos.");
  });

  // NOTE: validatePhone cannot reject over-long input because parsePhone
  // truncates to 11 before the length check; this is pre-existing behavior.
  // In the UI, formatPhone re-slices on every change so users never type >11.
  it("accepts over-long input (parsePhone truncates to 11)", () => {
    expect(validatePhone("119999999999")).toBe(null);
  });
});

// --- validateDocument: CPF --------------------------------------------------

describe("validateDocument (CPF)", () => {
  it("accepts a valid check-digit CPF", () => {
    expect(validateDocument("CPF", "52998224725")).toBe(null);
  });
  it("accepts a valid CPF with mask", () => {
    expect(validateDocument("CPF", "529.982.247-25")).toBe(null);
  });
  it("rejects repeated digits as invalid", () => {
    expect(validateDocument("CPF", "11111111111")).toBe("CPF inválido.");
  });
  it("rejects wrong check digits", () => {
    expect(validateDocument("CPF", "52998224700")).toBe("CPF inválido.");
  });
  it("rejects wrong length", () => {
    expect(validateDocument("CPF", "529982247")).toBe("CPF deve ter 11 dígitos.");
  });
  it("rejects empty", () => {
    expect(validateDocument("CPF", "")).toBe("Documento é obrigatório.");
  });
});

// --- validateDocument: CNPJ -------------------------------------------------

describe("validateDocument (CNPJ)", () => {
  it("accepts a valid numeric CNPJ", () => {
    expect(validateDocument("CNPJ", "11222333000181")).toBe(null);
  });
  it("accepts a valid masked numeric CNPJ", () => {
    expect(validateDocument("CNPJ", "11.222.333/0001-81")).toBe(null);
  });
  it("accepts a valid alphanumeric CNPJ (RFB 2.229/2024)", () => {
    expect(validateDocument("CNPJ", "12A3456B780196")).toBe(null);
  });
  it("rejects repeated characters", () => {
    expect(validateDocument("CNPJ", "11111111111111")).toBe("CNPJ inválido.");
  });
  it("rejects wrong check digits", () => {
    expect(validateDocument("CNPJ", "11222333000100")).toBe("CNPJ inválido.");
  });
  it("rejects wrong length", () => {
    expect(validateDocument("CNPJ", "11222333")).toBe("CNPJ deve ter 14 caracteres.");
  });
});

// --- validateDocument: RG ---------------------------------------------------

describe("validateDocument (RG)", () => {
  it("accepts a valid length RG", () => {
    expect(validateDocument("RG", "123456789")).toBe(null);
  });
  it("rejects too-short RG", () => {
    expect(validateDocument("RG", "123")).toBe("RG muito curto.");
  });
  it("rejects too-long RG", () => {
    expect(validateDocument("RG", "123456789012345678901")).toBe("RG muito longo.");
  });
});

// --- validateEmail ----------------------------------------------------------

describe("validateEmail", () => {
  it("accepts empty (optional)", () => {
    expect(validateEmail("")).toBe(null);
  });
  it("accepts a well-formed email", () => {
    expect(validateEmail("maria@email.com")).toBe(null);
  });
  it("rejects missing @", () => {
    expect(validateEmail("mariaemail.com")).toBe("E-mail inválido.");
  });
  it("rejects invalid format", () => {
    expect(validateEmail("maria@com")).toBe("E-mail inválido.");
  });
  it("rejects over-length email", () => {
    expect(validateEmail("a".repeat(250) + "@b.com")).toBe("E-mail muito longo.");
  });
});

// --- validateName -----------------------------------------------------------

describe("validateName", () => {
  it("accepts a non-empty name", () => {
    expect(validateName("Maria Souza")).toBe(null);
  });
  it("rejects empty", () => {
    expect(validateName("")).toBe("Nome é obrigatório.");
  });
  it("rejects whitespace-only", () => {
    expect(validateName("   ")).toBe("Nome é obrigatório.");
  });
  it("rejects over-length name", () => {
    expect(validateName("a".repeat(256))).toBe(
      "Nome deve ter no máximo 255 caracteres."
    );
  });
});

// --- validateState ----------------------------------------------------------

describe("validateState", () => {
  it("accepts a 2-letter uppercase sigla", () => {
    expect(validateState("SP")).toBe(null);
  });
  it("accepts lowercase by normalizing", () => {
    expect(validateState("sp")).toBe(null);
  });
  it("rejects empty", () => {
    expect(validateState("")).toBe("Estado é obrigatório.");
  });
  it("rejects wrong length", () => {
    expect(validateState("SAO")).toBe("Estado deve ter 2 letras (ex: SP).");
  });
  it("rejects non-letters", () => {
    expect(validateState("S1")).toBe(
      "Estado deve ser a sigla com 2 letras (ex: SP, RJ)."
    );
  });
});

// --- validateZipCode --------------------------------------------------------

describe("validateZipCode", () => {
  it("accepts hyphenated form", () => {
    expect(validateZipCode("01310-000")).toBe(null);
  });
  it("accepts non-hyphenated form", () => {
    expect(validateZipCode("01310000")).toBe(null);
  });
  it("rejects empty", () => {
    expect(validateZipCode("")).toBe("CEP é obrigatório.");
  });
  it("rejects invalid format", () => {
    expect(validateZipCode("01310")).toBe("CEP deve estar no formato 00000-000.");
    expect(validateZipCode("0131A-000")).toBe("CEP deve estar no formato 00000-000.");
  });
});

// --- validateRequiredText ---------------------------------------------------

describe("validateRequiredText", () => {
  it("accepts a non-empty value within length", () => {
    expect(validateRequiredText("Rua A", "Logradouro")).toBe(null);
  });
  it("rejects empty with the given label", () => {
    expect(validateRequiredText("", "Logradouro")).toBe("Logradouro é obrigatório.");
  });
  it("rejects over-length with custom max", () => {
    expect(validateRequiredText("a".repeat(11), "Campo", 10)).toBe(
      "Campo deve ter no máximo 10 caracteres."
    );
  });
});

// --- validatePassword -------------------------------------------------------

describe("validatePassword", () => {
  it("accepts a 6+ char password", () => {
    expect(validatePassword("123456")).toBe(null);
  });
  it("rejects empty", () => {
    expect(validatePassword("")).toBe("Senha é obrigatória.");
  });
  it("rejects shorter than 6", () => {
    expect(validatePassword("12345")).toBe("Senha deve ter no mínimo 6 caracteres.");
  });
});