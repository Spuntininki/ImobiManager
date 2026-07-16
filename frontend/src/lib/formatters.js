// Re-export validators for backward compatibility during the refactor.
// Importers should prefer `@/lib/validators` directly; these re-exports
// will be removed once all callers are migrated.
export {
  validateDocument,
  validateEmail,
  validateName,
  validatePassword,
  validatePhone,
  validateRequiredText,
  validateState,
  validateZipCode,
} from "@/lib/validators";

export const PHONE_MAX_DIGITS = 11;
export const CPF_LENGTH = 11;
export const CNPJ_LENGTH = 14;
export const RG_MAX_LENGTH = 20;

export function parsePhone(value) {
  return (value || "").replace(/\D/g, "").slice(0, PHONE_MAX_DIGITS);
}

export function formatPhone(value) {
  const raw = parsePhone(value);
  if (raw.length === 0) return "";
  if (raw.length <= 2) return `(${raw}`;
  if (raw.length <= 6) return `(${raw.slice(0, 2)}) ${raw.slice(2)}`;
  return `(${raw.slice(0, 2)}) ${raw.slice(2, 7)}-${raw.slice(7)}`;
}

export function parseDocument(value) {
  return (value || "").replace(/[^\dA-Za-z]/g, "").toUpperCase();
}

export function formatDocument(type, value) {
  const raw = parseDocument(value);
  if (type === "CPF") {
    if (raw.length <= 3) return raw;
    if (raw.length <= 6) return `${raw.slice(0, 3)}.${raw.slice(3)}`;
    if (raw.length <= 9) {
      return `${raw.slice(0, 3)}.${raw.slice(3, 6)}.${raw.slice(6)}`;
    }
    return `${raw.slice(0, 3)}.${raw.slice(3, 6)}.${raw.slice(6, 9)}-${raw.slice(
      9,
      11
    )}`;
  }
  if (type === "CNPJ") {
    if (raw.length <= 2) return raw;
    if (raw.length <= 5) return `${raw.slice(0, 2)}.${raw.slice(2)}`;
    if (raw.length <= 8) {
      return `${raw.slice(0, 2)}.${raw.slice(2, 5)}.${raw.slice(5)}`;
    }
    if (raw.length <= 12) {
      return `${raw.slice(0, 2)}.${raw.slice(2, 5)}.${raw.slice(
        5,
        8
      )}/${raw.slice(8)}`;
    }
    return `${raw.slice(0, 2)}.${raw.slice(2, 5)}.${raw.slice(
      5,
      8
    )}/${raw.slice(8, 12)}-${raw.slice(12, 14)}`;
  }
  if (type === "RG" && raw.length === 9) {
    return `${raw.slice(0, 2)}.${raw.slice(2, 5)}.${raw.slice(5, 8)}-${raw.slice(
      8
    )}`;
  }
  return raw;
}

export function getDocumentMaxLength(type) {
  if (type === "CPF") return CPF_LENGTH;
  if (type === "CNPJ") return CNPJ_LENGTH;
  return RG_MAX_LENGTH;
}

export function limitRawLength(parseFn, maxLength) {
  return (event) => {
    if (event.inputType === "deleteContentBackward" || !event.data) return;
    const { selectionStart, selectionEnd, value } = event.target;
    const nextValue =
      value.slice(0, selectionStart ?? 0) +
      event.data +
      value.slice(selectionEnd ?? value.length);
    if (parseFn(nextValue).length > maxLength) {
      event.preventDefault();
    }
  };
}

export function parseEmail(value) {
  return (value || "").trim();
}

export function parseName(value) {
  return (value || "").trim();
}