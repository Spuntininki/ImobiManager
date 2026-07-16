import api from "@/lib/api";

// --- Contracts (per owner) ---

export async function listContractsByOwner(ownerId) {
  const resp = await api.get(`/owners/${ownerId}/contracts`);
  return resp.data;
}

export async function createContract(ownerId, payload) {
  const resp = await api.post(`/owners/${ownerId}/contracts`, payload);
  return resp.data;
}

// NOTE: contracts use PATCH (not PUT) for updates.
export async function updateContract(contractId, payload) {
  const resp = await api.patch(`/contracts/${contractId}`, payload);
  return resp.data;
}

export async function deleteContract(contractId) {
  await api.delete(`/contracts/${contractId}`);
}

export async function downloadContractPdf(contractId) {
  const resp = await api.get(`/contracts/${contractId}/pdf`, {
    responseType: "blob",
  });
  return resp.data;
}