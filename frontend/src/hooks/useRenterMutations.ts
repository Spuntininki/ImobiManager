import { useMutation, useQueryClient } from "@tanstack/react-query";

import {
  createRenter,
  deleteRenter,
  updateRenter,
} from "@/services/renterService";
import { queryKeys } from "@/hooks/queryKeys";

import type { Renter } from "@/types/domain";

export function useCreateRenter() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({
      ownerId,
      payload,
    }: {
      ownerId: number;
      payload: Record<string, unknown>;
    }) => createRenter(ownerId, payload),
    onSuccess: (newRenter: Renter, variables) => {
      qc.setQueryData(
        queryKeys.renters(variables.ownerId),
        (prev: Renter[] | undefined) => [...(prev ?? []), newRenter],
      );
    },
  });
}

export function useUpdateRenter() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({
      renterId,
      payload,
      ownerId,
    }: {
      renterId: number;
      payload: Record<string, unknown>;
      ownerId: number;
    }) => updateRenter(renterId, payload),
    onSuccess: (updatedRenter: Renter, variables) => {
      qc.setQueryData(
        queryKeys.renters(variables.ownerId),
        (prev: Renter[] | undefined) =>
          (prev ?? []).map((r: Renter) =>
            r.id === updatedRenter.id ? updatedRenter : r,
          ),
      );
    },
  });
}

export function useDeleteRenter() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({
      renterId,
      ownerId,
    }: {
      renterId: number;
      ownerId: number;
    }) => deleteRenter(renterId),
    onSuccess: (_data: void, variables) => {
      qc.setQueryData(
        queryKeys.renters(variables.ownerId),
        (prev: Renter[] | undefined) =>
          (prev ?? []).filter((r: Renter) => r.id !== variables.renterId),
      );
    },
  });
}
