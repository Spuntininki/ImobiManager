import { useQueries } from "@tanstack/react-query";

import { listContractsByOwner } from "@/services/contractService";
import { listRentersByOwner } from "@/services/renterService";
import { listAddressesByOwner } from "@/services/addressService";
import { queryKeys } from "@/hooks/queryKeys";

import type { Address, Contract, Renter } from "@/types/domain";

/**
 * Fetch contracts, renters, and addresses for an owner together, mirroring the
 * original Promise.all behavior: a single loading flag and a single error
 * message (the first failure's).
 */
export function useContractsPageData(
  ownerId: number | undefined,
): {
  contracts: Contract[];
  renters: Renter[];
  addresses: Address[];
  isLoading: boolean;
  error: string;
} {
  const enabled = ownerId != null;
  const [contractsQ, rentersQ, addressesQ] = useQueries({
    queries: [
      {
        queryKey: queryKeys.contracts(ownerId!),
        queryFn: () => listContractsByOwner(ownerId!),
        enabled,
      },
      {
        queryKey: queryKeys.renters(ownerId!),
        queryFn: () => listRentersByOwner(ownerId!),
        enabled,
      },
      {
        queryKey: queryKeys.addresses(ownerId!),
        queryFn: () => listAddressesByOwner(ownerId!),
        enabled,
      },
    ],
  });

  const isLoading =
    enabled &&
    (contractsQ.isLoading || rentersQ.isLoading || addressesQ.isLoading);
  const firstError = [contractsQ, rentersQ, addressesQ].find((q) => q.error);

  return {
    contracts: contractsQ.data ?? [],
    renters: rentersQ.data ?? [],
    addresses: addressesQ.data ?? [],
    isLoading,
    error: firstError ? "Não foi possível carregar os contratos." : "",
  };
}
