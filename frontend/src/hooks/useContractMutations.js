import { useMutation, useQueryClient } from "@tanstack/react-query";

import {
  createContract,
  deleteContract,
  downloadContractPdf,
  updateContract,
} from "@/services/contractService";
import { queryKeys } from "@/hooks/queryKeys";

export function useCreateContract() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ ownerId, payload }) => createContract(ownerId, payload),
    onSuccess: (newContract, { ownerId }) => {
      qc.setQueryData(queryKeys.contracts(ownerId), (prev) => [
        ...(prev ?? []),
        newContract,
      ]);
    },
  });
}

export function useUpdateContract() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ contractId, payload }) => updateContract(contractId, payload),
    onSuccess: (updatedContract, { ownerId }) => {
      qc.setQueryData(queryKeys.contracts(ownerId), (prev) =>
        (prev ?? []).map((c) =>
          c.id === updatedContract.id ? updatedContract : c
        )
      );
    },
  });
}

export function useDeleteContract() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ contractId }) => deleteContract(contractId),
    onSuccess: (_, { contractId, ownerId }) => {
      qc.setQueryData(queryKeys.contracts(ownerId), (prev) =>
        (prev ?? []).filter((c) => c.id !== contractId)
      );
    },
  });
}

export function useDownloadContractPdf() {
  return useMutation({
    mutationFn: ({ contractId }) => downloadContractPdf(contractId),
  });
}