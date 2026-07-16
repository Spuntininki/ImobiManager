import api from "@/lib/api";

// --- Renters (per owner) ---

export async function listRentersByOwner(ownerId) {
  const resp = await api.get(`/owners/${ownerId}/renters`);
  return resp.data;
}

export async function createRenter(ownerId, payload) {
  const resp = await api.post(`/owners/${ownerId}/renters`, payload);
  return resp.data;
}

export async function updateRenter(renterId, payload) {
  const resp = await api.put(`/renters/${renterId}`, payload);
  return resp.data;
}

export async function deleteRenter(renterId) {
  await api.delete(`/renters/${renterId}`);
}

// --- Renter documents ---

export async function listRenterDocuments(renterId) {
  const resp = await api.get(`/renters/${renterId}/documents`);
  return resp.data;
}

export async function createRenterDocument(renterId, { document_type, document }) {
  const resp = await api.post(`/renters/${renterId}/documents`, {
    document_type,
    document: document.trim(),
  });
  return resp.data;
}

export async function deleteRenterDocument(renterId, documentId) {
  await api.delete(`/renters/${renterId}/documents/${documentId}`);
}