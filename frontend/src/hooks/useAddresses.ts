import { useQuery } from "@tanstack/react-query";

import { listAddressesByOwner } from "@/services/addressService";
import { queryKeys } from "@/hooks/queryKeys";

import type { Address } from "@/types/domain";

export function useAddresses(
  ownerId: number | undefined,
): {
  addresses: Address[];
  isLoading: boolean;
  error: string;
} {
  const { data, isLoading, error } = useQuery({
    queryKey: queryKeys.addresses(ownerId!),
    queryFn: () => listAddressesByOwner(ownerId!),
    enabled: ownerId != null,
  });
  return {
    addresses: data ?? [],
    isLoading,
    error: error ? "Não foi possível carregar os imóveis." : "",
  };
}
