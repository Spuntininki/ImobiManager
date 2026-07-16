import { useQuery } from "@tanstack/react-query";

import { listRentersByOwner } from "@/services/renterService";
import { queryKeys } from "@/hooks/queryKeys";

export function useRenters(ownerId) {
  const { data, isLoading, error } = useQuery({
    queryKey: queryKeys.renters(ownerId),
    queryFn: () => listRentersByOwner(ownerId),
    enabled: ownerId != null,
  });
  return {
    renters: data ?? [],
    isLoading,
    error: error ? "Não foi possível carregar os inquilinos." : "",
  };
}