import { useMutation, useQueryClient } from "@tanstack/react-query";

import {
  createAddress,
  deleteAddress,
  updateAddress,
} from "@/services/addressService";
import { queryKeys } from "@/hooks/queryKeys";

export function useCreateAddress() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ ownerId, payload }) => createAddress(ownerId, payload),
    onSuccess: (newAddress, { ownerId }) => {
      qc.setQueryData(queryKeys.addresses(ownerId), (prev) => [
        ...(prev ?? []),
        newAddress,
      ]);
    },
  });
}

export function useUpdateAddress() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ addressId, payload }) => updateAddress(addressId, payload),
    onSuccess: (updatedAddress, { ownerId }) => {
      qc.setQueryData(queryKeys.addresses(ownerId), (prev) =>
        (prev ?? []).map((a) =>
          a.id === updatedAddress.id ? updatedAddress : a
        )
      );
    },
  });
}

export function useDeleteAddress() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ addressId }) => deleteAddress(addressId),
    onSuccess: (_, { addressId, ownerId }) => {
      qc.setQueryData(queryKeys.addresses(ownerId), (prev) =>
        (prev ?? []).filter((a) => a.id !== addressId)
      );
    },
  });
}