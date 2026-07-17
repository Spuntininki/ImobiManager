import { useMutation, useQueryClient } from "@tanstack/react-query";

import {
  createOwner,
  deleteOwner,
  updateOwner,
} from "@/services/ownerService";
import { queryKeys } from "@/hooks/queryKeys";

import type { Owner } from "@/types/domain";

export function useCreateOwner() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ name }: { name: string }) => createOwner({ name }),
    onSuccess: (newOwner: Owner) => {
      qc.setQueryData(queryKeys.owners, (prev: Owner[] | undefined) => [
        ...(prev ?? []),
        newOwner,
      ]);
    },
  });
}

export function useUpdateOwner() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({
      ownerId,
      name,
    }: {
      ownerId: number;
      name: string;
    }) => updateOwner(ownerId, { name }),
    onSuccess: (updatedOwner: Owner, variables) => {
      qc.setQueryData(queryKeys.owners, (prev: Owner[] | undefined) =>
        (prev ?? []).map((o: Owner) =>
          o.id === variables.ownerId ? updatedOwner : o,
        ),
      );
    },
  });
}

export function useDeleteOwner() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ ownerId }: { ownerId: number }) => deleteOwner(ownerId),
    onSuccess: (_data: void, variables) => {
      qc.setQueryData(queryKeys.owners, (prev: Owner[] | undefined) =>
        (prev ?? []).filter((o: Owner) => o.id !== variables.ownerId),
      );
    },
  });
}
