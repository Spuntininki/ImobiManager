import api from "@/lib/api";

// --- Owners ---

export async function listOwners() {
  const resp = await api.get("/owners");
  return resp.data;
}

export async function createOwner({ name }) {
  const resp = await api.post("/owners", { name });
  return resp.data;
}

export async function updateOwner(ownerId, { name }) {
  const resp = await api.put(`/owners/${ownerId}`, { name });
  return resp.data;
}

export async function deleteOwner(ownerId) {
  await api.delete(`/owners/${ownerId}`);
}

// --- Owner documents ---

export async function listOwnerDocuments(ownerId) {
  const resp = await api.get(`/owners/${ownerId}/documents`);
  return resp.data;
}

export async function createOwnerDocument(ownerId, { document_type, document }) {
  const resp = await api.post(`/owners/${ownerId}/documents`, {
    document_type,
    document: document.trim(),
  });
  return resp.data;
}

export async function deleteOwnerDocument(ownerId, documentId) {
  await api.delete(`/owners/${ownerId}/documents/${documentId}`);
}

// --- Owner revenue (Dashboard) ---

export async function getRevenueTimeline(ownerId, { start_date, end_date }) {
  const resp = await api.get(`/owners/${ownerId}/revenue-timeline`, {
    params: { start_date, end_date },
  });
  return resp.data;
}

export async function getRevenueSummary(ownerId, { start_date, end_date }) {
  const resp = await api.get(`/owners/${ownerId}/revenue-timeline/summary`, {
    params: { start_date, end_date },
  });
  return resp.data;
}