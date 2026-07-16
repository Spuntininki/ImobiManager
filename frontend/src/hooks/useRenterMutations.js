import { useMutation, useQueryClient } from "@tanstack/react-query";

import {
  createRenter,
  deleteRenter,
  updateRenter,
  createRenterDocument,
  deleteRenterDocument,
} from "@/services/renterService";
import { queryKeys } from "@/hooks/queryKeys";

export function useCreateRenter() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ ownerId, payload }) => createRenter(ownerId, payload),
    onSuccess: (newRenter, { ownerId }) => {
      qc.setQueryData(queryKeys.renters(ownerId), (prev) => [
        ...(prev ?? []),
        newRenter,
      ]);
    },
  });
}

export function useUpdateRenter() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ renterId, payload }) => updateRenter(renterId, payload),
    onSuccess: (updatedRenter, { ownerId }) => {
      qc.setQueryData(queryKeys.renters(ownerId), (prev) =>
        (prev ?? []).map((r) =>
          r.id === updatedRenter.id ? updatedRenter : r
        )
      );
    },
  });
}

export function useDeleteRenter() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ renterId }) => deleteRenter(renterId),
    onSuccess: (_, { renterId, ownerId }) => {
      qc.setQueryData(queryKeys.renters(ownerId), (prev) =>
        (prev ?? []).filter((r) => r.id !== renterId)
      );
    },
  });
}

export function useCreateRenterDocument() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ renterId, document_type, document }) =>
      createRenterDocument(renterId, { document_type, document }),
    onSuccess: (_, { renterId }) => {
      qc.invalidateQueries({ queryKey: queryKeys.renterDocuments(renterId) });
    },
  });
}

export function useDeleteRenterDocument() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ renterId, documentId }) =>
      deleteRenterDocument(renterId, documentId),
    onSuccess: (_, { renterId }) => {
      qc.invalidateQueries({ queryKey: queryKeys.renterDocuments(renterId) });
    },
  });
}