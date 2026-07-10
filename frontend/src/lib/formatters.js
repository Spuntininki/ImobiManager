export const PHONE_MAX_DIGITS = 11;
export const CPF_LENGTH = 11;
export const CNPJ_LENGTH = 14;
const RG_MIN_LENGTH = 4;
export const RG_MAX_LENGTH = 20;
const NAME_MAX_LENGTH = 255;
const EMAIL_MAX_LENGTH = 254;

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

export function validatePhone(value, { required = true } = {}) {
  const raw = parsePhone(value);
  if (raw.length === 0) {
    return required ? "Telefone é obrigatório." : null;
  }
  if (![10, 11].includes(raw.length)) {
    return "Telefone deve ter 10 ou 11 dígitos.";
  }
  return null;
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

function isValidCPF(cpf) {
  if (cpf.length !== CPF_LENGTH || /^(\d)\1{10}$/.test(cpf)) return false;

  let sum = 0;
  for (let i = 0; i < 9; i++) {
    sum += parseInt(cpf[i], 10) * (10 - i);
  }
  let firstDigit = (sum * 10) % 11;
  if (firstDigit === 10) firstDigit = 0;
  if (firstDigit !== parseInt(cpf[9], 10)) return false;

  sum = 0;
  for (let i = 0; i < 10; i++) {
    sum += parseInt(cpf[i], 10) * (11 - i);
  }
  let secondDigit = (sum * 10) % 11;
  if (secondDigit === 10) secondDigit = 0;
  return secondDigit === parseInt(cpf[10], 10);
}

/** Convert a base-32 char (0-9, A-Z) to its numeric value (IN RFB 2212/2024). */
function cnpjCharValue(c) {
  const code = c.charCodeAt(0);
  if (code >= 48 && code <= 57) return code - 48;   // 0-9 → 0-9
  if (code >= 65 && code <= 90) return code - 55;    // A-Z → 10-35
  return NaN;
}

function isValidCNPJ(cnpj) {
  if (cnpj.length !== CNPJ_LENGTH) return false;
  // Reject repeated characters (e.g. 14 identical chars).
  if (/^(.)\1{13}$/.test(cnpj)) return false;

  const weightsFirst = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2];
  const weightsSecond = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2];

  let sum = 0;
  for (let i = 0; i < 12; i++) {
    const val = cnpjCharValue(cnpj[i]);
    if (isNaN(val)) return false;
    sum += val * weightsFirst[i];
  }
  const firstCheck = cnpjCharValue(cnpj[12]);
  if (isNaN(firstCheck)) return false;
  let firstDigit = sum % 11 < 2 ? 0 : 11 - (sum % 11);
  if (firstDigit !== firstCheck) return false;

  sum = 0;
  for (let i = 0; i < 13; i++) {
    const val = cnpjCharValue(cnpj[i]);
    if (isNaN(val)) return false;
    sum += val * weightsSecond[i];
  }
  const secondCheck = cnpjCharValue(cnpj[13]);
  if (isNaN(secondCheck)) return false;
  let secondDigit = sum % 11 < 2 ? 0 : 11 - (sum % 11);
  return secondDigit === secondCheck;
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

export function validateDocument(type, value) {
  const raw = parseDocument(value);
  if (raw.length === 0) return "Documento é obrigatório.";

  if (type === "CPF") {
    if (raw.length !== CPF_LENGTH) {
      return `CPF deve ter ${CPF_LENGTH} dígitos.`;
    }
    if (!isValidCPF(raw)) return "CPF inválido.";
  } else if (type === "CNPJ") {
    if (raw.length !== CNPJ_LENGTH) {
      return `CNPJ deve ter ${CNPJ_LENGTH} caracteres.`;
    }
    if (!isValidCNPJ(raw)) return "CNPJ inválido.";
  } else if (type === "RG") {
    if (raw.length < RG_MIN_LENGTH) return "RG muito curto.";
    if (raw.length > RG_MAX_LENGTH) return "RG muito longo.";
  }

  return null;
}

export function parseEmail(value) {
  return (value || "").trim();
}

export function validateEmail(value) {
  const email = parseEmail(value);
  if (!email) return null;
  if (email.length > EMAIL_MAX_LENGTH) return "E-mail muito longo.";
  if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) return "E-mail inválido.";
  return null;
}

export function parseName(value) {
  return (value || "").trim();
}

export function validateName(value) {
  const name = parseName(value);
  if (!name) return "Nome é obrigatório.";
  if (name.length > NAME_MAX_LENGTH) {
    return `Nome deve ter no máximo ${NAME_MAX_LENGTH} caracteres.`;
  }
  return null;
}

export function validateState(value) {
  const raw = (value || "").trim();
  if (!raw) return "Estado é obrigatório.";
  if (raw.length !== 2) return "Estado deve ter 2 letras (ex: SP).";
  if (!/^[A-Z]{2}$/.test(raw.toUpperCase())) {
    return "Estado deve ser a sigla com 2 letras (ex: SP, RJ).";
  }
  return null;
}

export function validateZipCode(value) {
  const raw = (value || "").trim();
  if (!raw) return "CEP é obrigatório.";
  if (!/^\d{5}-?\d{3}$/.test(raw)) {
    return "CEP deve estar no formato 00000-000.";
  }
  return null;
}

export function validateRequiredText(value, label, maxLength = 255) {
  const raw = (value || "").trim();
  if (!raw) return `${label} é obrigatório.`;
  if (raw.length > maxLength) {
    return `${label} deve ter no máximo ${maxLength} caracteres.`;
  }
  return null;
}

export function validatePassword(value) {
  const raw = (value || "").trim();
  if (!raw) return "Senha é obrigatória.";
  if (raw.length < 6) return "Senha deve ter no mínimo 6 caracteres.";
  return null;
}
