import { useQuery } from "@tanstack/react-query";

import { listRenterDocuments } from "@/services/renterService";
import { queryKeys } from "@/hooks/queryKeys";

/**
 * Fetch a renter's documents. Lazy by default (enabled=false) so the edit
 * dialog can load on open; the caller passes `enabled`.
 */
export function useRenterDocuments(renterId, { enabled = true } = {}) {
  const { data, isLoading, error } = useQuery({
    queryKey: queryKeys.renterDocuments(renterId),
    queryFn: () => listRenterDocuments(renterId),
    enabled: enabled && renterId != null,
  });
  return {
    documents: data ?? [],
    isLoading,
    error: error ? "Não foi possível carregar os documentos." : "",
  };
}