import { useQuery } from "@tanstack/react-query";

import { listOwnerDocuments } from "@/services/ownerService";
import { queryKeys } from "@/hooks/queryKeys";

import type { Document } from "@/types/domain";

/**
 * Fetch an owner's documents. Lazy by default (enabled=false) so the edit
 * dialog can load on open; the caller passes `enabled`.
 */
export function useOwnerDocuments(
  ownerId: number | undefined,
  { enabled = true }: { enabled?: boolean } = {},
): {
  documents: Document[];
  isLoading: boolean;
  error: string;
} {
  const { data, isLoading, error } = useQuery({
    queryKey: queryKeys.ownerDocuments(ownerId!),
    queryFn: () => listOwnerDocuments(ownerId!),
    enabled: enabled && ownerId != null,
  });
  return {
    documents: data ?? [],
    isLoading,
    error: error ? "Não foi possível carregar os documentos." : "",
  };
}
