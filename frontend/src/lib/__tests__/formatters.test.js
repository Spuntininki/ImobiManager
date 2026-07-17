import { describe, expect, it } from "vitest";

import {
  getDocumentMaxLength,
  limitRawLength,
  parseDocument,
  parseEmail,
  parseName,
  parsePhone,
  formatPhone,
  formatDocument,
} from "@/lib/formatters";

// --- parsePhone / formatPhone ----------------------------------------------

describe("parsePhone", () => {
  it("strips non-digits and caps at PHONE_MAX_DIGITS (11)", () => {
    expect(parsePhone("(11) 99999-9999")).toBe("11999999999");
    expect(parsePhone("abc")).toBe("");
    expect(parsePhone("12345678901234")).toBe("12345678901");
  });

  it("treats null/undefined as empty", () => {
    expect(parsePhone(null)).toBe("");
    expect(parsePhone(undefined)).toBe("");
  });
});

describe("formatPhone", () => {
  // formatPhone is mobile-centric: it always splits as (99) 99999-9999
  // (5 digits before the dash), so a 10-digit value renders with 5+3.
  it("masks full 10-digit number (mobile-centric split)", () => {
    expect(formatPhone("1199999999")).toBe("(11) 99999-999");
  });

  it("masks full 11-digit (mobile) number", () => {
    expect(formatPhone("11999999999")).toBe("(11) 99999-9999");
  });

  it("returns empty string for empty input", () => {
    expect(formatPhone("")).toBe("");
  });

  it("formats partial inputs at each boundary", () => {
    expect(formatPhone("1")).toBe("(1");
    expect(formatPhone("11")).toBe("(11");
    expect(formatPhone("119")).toBe("(11) 9");
    expect(formatPhone("11999")).toBe("(11) 999");
    // At exactly 7 chars the dash is already emitted.
    expect(formatPhone("1199999")).toBe("(11) 99999-");
  });
});

// --- parseDocument / formatDocument -----------------------------------------

describe("parseDocument", () => {
  it("strips non-alphanumerics and uppercases", () => {
    expect(parseDocument("123.456-789")).toBe("123456789");
    expect(parseDocument("ab.c-def")).toBe("ABCDEF");
  });

  it("treats null/undefined as empty", () => {
    expect(parseDocument(null)).toBe("");
    expect(parseDocument(undefined)).toBe("");
  });
});

describe("formatDocument", () => {
  it("formats CPF progressively", () => {
    expect(formatDocument("CPF", "12345678909")).toBe("123.456.789-09");
    expect(formatDocument("CPF", "123")).toBe("123");
    expect(formatDocument("CPF", "123456")).toBe("123.456");
    expect(formatDocument("CPF", "123456789")).toBe("123.456.789");
  });

  it("formats CNPJ", () => {
    expect(formatDocument("CNPJ", "11222333000181")).toBe(
      "11.222.333/0001-81"
    );
    expect(formatDocument("CNPJ", "11")).toBe("11");
    expect(formatDocument("CNPJ", "11222")).toBe("11.222");
    expect(formatDocument("CNPJ", "11222333")).toBe("11.222.333");
    expect(formatDocument("CNPJ", "112223330001")).toBe("11.222.333/0001");
  });

  it("formats 9-digit RG with mask", () => {
    expect(formatDocument("RG", "123456789")).toBe("12.345.678-9");
    expect(formatDocument("RG", "1234")).toBe("1234");
  });

  it("returns raw for unknown type", () => {
    expect(formatDocument("OTHER", "12.34")).toBe("1234");
  });
});

// --- getDocumentMaxLength --------------------------------------------------

describe("getDocumentMaxLength", () => {
  it("returns CPF / CNPJ / RG lengths", () => {
    expect(getDocumentMaxLength("CPF")).toBe(11);
    expect(getDocumentMaxLength("CNPJ")).toBe(14);
    expect(getDocumentMaxLength("RG")).toBe(20);
    expect(getDocumentMaxLength("OTHER")).toBe(20);
  });
});

// --- parseEmail / parseName -------------------------------------------------

describe("parseEmail / parseName", () => {
  it("trims surrounding whitespace", () => {
    expect(parseEmail("  a@b.com  ")).toBe("a@b.com");
    expect(parseName("  Maria  ")).toBe("Maria");
  });

  it("treats null/undefined as empty", () => {
    expect(parseEmail(null)).toBe("");
    expect(parseName(undefined)).toBe("");
  });
});

// --- limitRawLength --------------------------------------------------------

function makeEvent(partial) {
  return {
    inputType: "insertText",
    data: "9",
    preventDefault: () => {},
    target: { value: "", selectionStart: 0, selectionEnd: 0 },
    ...partial,
  };
}

describe("limitRawLength", () => {
  it("prevents default when the parsed next value exceeds max", () => {
    let prevented = false;
    // Use parseDocument (no internal cap) so the limiter actually fires.
    const handler = limitRawLength(parseDocument, 4);
    handler(
      makeEvent({
        data: "9",
        target: { value: "1234", selectionStart: 4, selectionEnd: 4 },
        preventDefault: () => {
          prevented = true;
        },
      })
    );
    expect(prevented).toBe(true);
  });

  // NOTE: limitRawLength(parsePhone, 11) is effectively inert because
  // parsePhone caps to 11 before the length check — see validators.test.js.
  it("does NOT prevent when the parser caps the value (parsePhone)", () => {
    let prevented = false;
    const handler = limitRawLength(parsePhone, 11);
    handler(
      makeEvent({
        data: "9",
        target: { value: "11999999999", selectionStart: 11, selectionEnd: 11 },
        preventDefault: () => {
          prevented = true;
        },
      })
    );
    expect(prevented).toBe(false);
  });

  it("does nothing when input data is null (e.g. enter key)", () => {
    let prevented = false;
    const handler = limitRawLength(parsePhone, 11);
    handler(
      makeEvent({
        data: null,
        preventDefault: () => {
          prevented = true;
        },
      })
    );
    expect(prevented).toBe(false);
  });

  it("allows deletion without preventing", () => {
    let prevented = false;
    const handler = limitRawLength(parsePhone, 11);
    handler(
      makeEvent({
        inputType: "deleteContentBackward",
        preventDefault: () => {
          prevented = true;
        },
      })
    );
    expect(prevented).toBe(false);
  });

  it("does not prevent when within the limit", () => {
    let prevented = false;
    const handler = limitRawLength(parsePhone, 11);
    handler(
      makeEvent({
        data: "9",
        target: { value: "119999999", selectionStart: 9, selectionEnd: 9 },
        preventDefault: () => {
          prevented = true;
        },
      })
    );
    expect(prevented).toBe(false);
  });
});