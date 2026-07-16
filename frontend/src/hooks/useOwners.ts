import { useQuery } from "@tanstack/react-query";

import { listOwners } from "@/services/ownerService";
import { queryKeys } from "@/hooks/queryKeys";

import type { Owner } from "@/types/domain";

/**
 * Fetch the current user's owners once.
 */
export function useOwners(): {
  owners: Owner[];
  isLoading: boolean;
  error: string;
} {
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
