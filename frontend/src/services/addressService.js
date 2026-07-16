import api from "@/lib/api";

// --- Addresses / Properties (per owner) ---

export async function listAddressesByOwner(ownerId) {
  const resp = await api.get(`/owners/${ownerId}/addresses`);
  return resp.data;
}

export async function createAddress(ownerId, payload) {
  const resp = await api.post(`/owners/${ownerId}/addresses`, payload);
  return resp.data;
}

export async function updateAddress(addressId, payload) {
  const resp = await api.put(`/addresses/${addressId}`, payload);
  return resp.data;
}

export async function deleteAddress(addressId) {
  await api.delete(`/addresses/${addressId}`);
}