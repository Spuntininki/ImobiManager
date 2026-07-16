import api from "@/lib/api";

import type { Contract } from "@/types/domain";

// --- Contracts (per owner) ---

export async function listContractsByOwner(
  ownerId: number,
): Promise<Contract[]> {
  const resp = await api.get(`/owners/${ownerId}/contracts`);
  return resp.data;
}

export async function createContract(
  ownerId: number,
  payload: Record<string, unknown>,
): Promise<Contract> {
  const resp = await api.post(`/owners/${ownerId}/contracts`, payload);
  return resp.data;
}

// NOTE: contracts use PATCH (not PUT) for updates.
export async function updateContract(
  contractId: number,
  payload: Record<string, unknown>,
): Promise<Contract> {
  const resp = await api.patch(`/contracts/${contractId}`, payload);
  return resp.data;
}

export async function deleteContract(contractId: number): Promise<void> {
  await api.delete(`/contracts/${contractId}`);
}

export async function downloadContractPdf(
  contractId: number,
): Promise<{ blob: Blob; disposition: string | undefined }> {
  const resp = await api.get(`/contracts/${contractId}/pdf`, {
    responseType: "blob",
  });
  return {
    blob: resp.data,
    disposition: resp.headers["content-disposition"],
  };
}
