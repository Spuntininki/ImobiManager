import { useMutation, useQueryClient } from "@tanstack/react-query";

import {
  createContract,
  deleteContract,
  updateContract,
} from "@/services/contractService";
import { queryKeys } from "@/hooks/queryKeys";

import type { Contract } from "@/types/domain";

export function useCreateContract() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({
      ownerId,
      payload,
    }: {
      ownerId: number;
      payload: Record<string, unknown>;
    }) => createContract(ownerId, payload),
    onSuccess: (newContract: Contract, variables) => {
      qc.setQueryData(
        queryKeys.contracts(variables.ownerId),
        (prev: Contract[] | undefined) => [...(prev ?? []), newContract],
      );
    },
  });
}

export function useUpdateContract() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({
      contractId,
      payload,
      ownerId,
    }: {
      contractId: number;
      payload: Record<string, unknown>;
      ownerId: number;
    }) => updateContract(contractId, payload),
    onSuccess: (updatedContract: Contract, variables) => {
      qc.setQueryData(
        queryKeys.contracts(variables.ownerId),
        (prev: Contract[] | undefined) =>
          (prev ?? []).map((c: Contract) =>
            c.id === updatedContract.id ? updatedContract : c,
          ),
      );
    },
  });
}

export function useDeleteContract() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({
      contractId,
      ownerId,
    }: {
      contractId: number;
      ownerId: number;
    }) => deleteContract(contractId),
    onSuccess: (_data: void, variables) => {
      qc.setQueryData(
        queryKeys.contracts(variables.ownerId),
        (prev: Contract[] | undefined) =>
          (prev ?? []).filter((c: Contract) => c.id !== variables.contractId),
      );
    },
  });
}
