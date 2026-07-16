import api from "@/lib/api";

import type { Document, Renter } from "@/types/domain";

// --- Renters (per owner) ---

export async function listRentersByOwner(
  ownerId: number,
): Promise<Renter[]> {
  const resp = await api.get(`/owners/${ownerId}/renters`);
  return resp.data;
}

export async function createRenter(
  ownerId: number,
  payload: Record<string, unknown>,
): Promise<Renter> {
  const resp = await api.post(`/owners/${ownerId}/renters`, payload);
  return resp.data;
}

export async function updateRenter(
  renterId: number,
  payload: Record<string, unknown>,
): Promise<Renter> {
  const resp = await api.put(`/renters/${renterId}`, payload);
  return resp.data;
}

export async function deleteRenter(renterId: number): Promise<void> {
  await api.delete(`/renters/${renterId}`);
}

// --- Renter documents ---

export async function listRenterDocuments(
  renterId: number,
): Promise<Document[]> {
  const resp = await api.get(`/renters/${renterId}/documents`);
  return resp.data;
}

export async function createRenterDocument(
  renterId: number,
  {
    document_type,
    document,
  }: { document_type: string; document: string },
): Promise<Document> {
  const resp = await api.post(`/renters/${renterId}/documents`, {
    document_type,
    document: document.trim(),
  });
  return resp.data;
}

export async function deleteRenterDocument(
  renterId: number,
  documentId: number,
): Promise<void> {
  await api.delete(`/renters/${renterId}/documents/${documentId}`);
}
