import { useMutation, useQueryClient } from "@tanstack/react-query";

import {
  createOwner,
  deleteOwner,
  updateOwner,
  createOwnerDocument,
  deleteOwnerDocument,
} from "@/services/ownerService";
import { queryKeys } from "@/hooks/queryKeys";

export function useCreateOwner() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ name }) => createOwner({ name }),
    onSuccess: (newOwner) => {
      qc.setQueryData(queryKeys.owners, (prev) => [...(prev ?? []), newOwner]);
    },
  });
}

export function useUpdateOwner() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ ownerId, name }) => updateOwner(ownerId, { name }),
    onSuccess: (updatedOwner, { ownerId }) => {
      qc.setQueryData(queryKeys.owners, (prev) =>
        (prev ?? []).map((o) => (o.id === ownerId ? updatedOwner : o))
      );
    },
  });
}

export function useDeleteOwner() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ ownerId }) => deleteOwner(ownerId),
    onSuccess: (_, { ownerId }) => {
      qc.setQueryData(queryKeys.owners, (prev) =>
        (prev ?? []).filter((o) => o.id !== ownerId)
      );
    },
  });
}

export function useCreateOwnerDocument() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ ownerId, document_type, document }) =>
      createOwnerDocument(ownerId, { document_type, document }),
    onSuccess: (_, { ownerId }) => {
      qc.invalidateQueries({ queryKey: queryKeys.ownerDocuments(ownerId) });
    },
  });
}

export function useDeleteOwnerDocument() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ ownerId, documentId }) =>
      deleteOwnerDocument(ownerId, documentId),
    onSuccess: (_, { ownerId }) => {
      qc.invalidateQueries({ queryKey: queryKeys.ownerDocuments(ownerId) });
    },
  });
}