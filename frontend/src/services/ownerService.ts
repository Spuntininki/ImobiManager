import api from "@/lib/api";

import type { Document, Owner } from "@/types/domain";

// --- Owners ---

export async function listOwners(): Promise<Owner[]> {
  const resp = await api.get("/owners");
  return resp.data;
}

export async function createOwner({
  name,
}: {
  name: string;
}): Promise<Owner> {
  const resp = await api.post("/owners", { name });
  return resp.data;
}

export async function updateOwner(
  ownerId: number,
  { name }: { name: string },
): Promise<Owner> {
  const resp = await api.put(`/owners/${ownerId}`, { name });
  return resp.data;
}

export async function deleteOwner(ownerId: number): Promise<void> {
  await api.delete(`/owners/${ownerId}`);
}

// --- Owner documents ---

export async function listOwnerDocuments(
  ownerId: number,
): Promise<Document[]> {
  const resp = await api.get(`/owners/${ownerId}/documents`);
  return resp.data;
}

export async function createOwnerDocument(
  ownerId: number,
  {
    document_type,
    document,
  }: { document_type: string; document: string },
): Promise<Document> {
  const resp = await api.post(`/owners/${ownerId}/documents`, {
    document_type,
    document: document.trim(),
  });
  return resp.data;
}

export async function deleteOwnerDocument(
  ownerId: number,
  documentId: number,
): Promise<void> {
  await api.delete(`/owners/${ownerId}/documents/${documentId}`);
}

// --- Owner revenue (Dashboard) ---

export async function getRevenueTimeline(
  ownerId: number,
  { start_date, end_date }: { start_date: string; end_date: string },
): Promise<unknown> {
  const resp = await api.get(`/owners/${ownerId}/revenue-timeline`, {
    params: { start_date, end_date },
  });
  return resp.data;
}

export async function getRevenueSummary(
  ownerId: number,
  { start_date, end_date }: { start_date: string; end_date: string },
): Promise<unknown> {
  const resp = await api.get(`/owners/${ownerId}/revenue-timeline/summary`, {
    params: { start_date, end_date },
  });
  return resp.data;
}
