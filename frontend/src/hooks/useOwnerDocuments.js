import { useQuery } from "@tanstack/react-query";

import { listOwnerDocuments } from "@/services/ownerService";
import { queryKeys } from "@/hooks/queryKeys";

/**
 * Fetch an owner's documents. Lazy by default (enabled=false) so the edit
 * dialog can load on open; the caller passes `enabled`.
 */
export function useOwnerDocuments(ownerId, { enabled = true } = {}) {
  const { data, isLoading, error } = useQuery({
    queryKey: queryKeys.ownerDocuments(ownerId),
    queryFn: () => listOwnerDocuments(ownerId),
    enabled: enabled && ownerId != null,
  });
  return {
    documents: data ?? [],
    isLoading,
    error: error ? "Não foi possível carregar os documentos." : "",
  };
}