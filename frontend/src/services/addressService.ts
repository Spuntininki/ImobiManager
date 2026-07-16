import api from "@/lib/api";

import type { Address } from "@/types/domain";

// --- Addresses / Properties (per owner) ---

export async function listAddressesByOwner(
  ownerId: number,
): Promise<Address[]> {
  const resp = await api.get(`/owners/${ownerId}/addresses`);
  return resp.data;
}

export async function createAddress(
  ownerId: number,
  payload: Record<string, unknown>,
): Promise<Address> {
  const resp = await api.post(`/owners/${ownerId}/addresses`, payload);
  return resp.data;
}

export async function updateAddress(
  addressId: number,
  payload: Record<string, unknown>,
): Promise<Address> {
  const resp = await api.put(`/addresses/${addressId}`, payload);
  return resp.data;
}

export async function deleteAddress(addressId: number): Promise<void> {
  await api.delete(`/addresses/${addressId}`);
}
