import { useEffect, useState } from "react";

import { useOwners } from "@/hooks/useOwners";

import type { Owner } from "@/types/domain";

/**
 * Manages the selected-owner state. Defaults to the first owner once the
 * list arrives. Returns the selected id (string|null) + setter, plus the
 * raw `useOwners` return so the caller can trivially destructure both.
 */
export function useOwnerSelect(): {
  owners: Owner[];
  isLoading: boolean;
  error: string;
  selectedOwnerId: string | null;
  setSelectedOwnerId: (id: string | null) => void;
} {
  const ownersState = useOwners();
  const [selectedOwnerId, setSelectedOwnerId] = useState<string | null>(null);

  useEffect(() => {
    if (selectedOwnerId === null && ownersState.owners.length > 0) {
      setSelectedOwnerId(String(ownersState.owners[0]!.id));
    }
  }, [ownersState.owners, selectedOwnerId]);

  return { ...ownersState, selectedOwnerId, setSelectedOwnerId };
}
