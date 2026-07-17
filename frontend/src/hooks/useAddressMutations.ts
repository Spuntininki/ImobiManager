import { useMutation, useQueryClient } from "@tanstack/react-query";

import {
  createAddress,
  deleteAddress,
  updateAddress,
} from "@/services/addressService";
import { queryKeys } from "@/hooks/queryKeys";

import type { Address } from "@/types/domain";

export function useCreateAddress() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({
      ownerId,
      payload,
    }: {
      ownerId: number;
      payload: Record<string, unknown>;
    }) => createAddress(ownerId, payload),
    onSuccess: (newAddress: Address, variables) => {
      qc.setQueryData(
        queryKeys.addresses(variables.ownerId),
        (prev: Address[] | undefined) => [...(prev ?? []), newAddress],
      );
    },
  });
}

export function useUpdateAddress() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({
      addressId,
      payload,
      ownerId,
    }: {
      addressId: number;
      payload: Record<string, unknown>;
      ownerId: number;
    }) => updateAddress(addressId, payload),
    onSuccess: (updatedAddress: Address, variables) => {
      qc.setQueryData(
        queryKeys.addresses(variables.ownerId),
        (prev: Address[] | undefined) =>
          (prev ?? []).map((a: Address) =>
            a.id === updatedAddress.id ? updatedAddress : a,
          ),
      );
    },
  });
}

export function useDeleteAddress() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({
      addressId,
      ownerId,
    }: {
      addressId: number;
      ownerId: number;
    }) => deleteAddress(addressId),
    onSuccess: (_data: void, variables) => {
      qc.setQueryData(
        queryKeys.addresses(variables.ownerId),
        (prev: Address[] | undefined) =>
          (prev ?? []).filter((a: Address) => a.id !== variables.addressId),
      );
    },
  });
}
