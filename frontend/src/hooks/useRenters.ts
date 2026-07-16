import { useQuery } from "@tanstack/react-query";

import { listRentersByOwner } from "@/services/renterService";
import { queryKeys } from "@/hooks/queryKeys";

import type { Renter } from "@/types/domain";

export function useRenters(
  ownerId: number | undefined,
): {
  renters: Renter[];
  isLoading: boolean;
  error: string;
} {
  const { data, isLoading, error } = useQuery({
    queryKey: queryKeys.renters(ownerId!),
    queryFn: () => listRentersByOwner(ownerId!),
    enabled: ownerId != null,
  });
  return {
    renters: data ?? [],
    isLoading,
    error: error ? "Não foi possível carregar os inquilinos." : "",
  };
}
