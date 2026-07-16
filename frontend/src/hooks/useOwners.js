import { useQuery } from "@tanstack/react-query";

import { listOwners } from "@/services/ownerService";
import { queryKeys } from "@/hooks/queryKeys";

/**
 * Fetch the current user's owners once.
 * @returns {{ owners: Array<{id:number,name:string}>, isLoading: boolean, error: unknown }}
 */
export function useOwners() {
  const { data, isLoading, error } = useQuery({
    queryKey: queryKeys.owners,
    queryFn: listOwners,
  });
  return {
    owners: data ?? [],
    isLoading,
    // Preserve the original string contract so pages render the message as-is.
    error: error ? "Não foi possível carregar os proprietários." : "",
  };
}