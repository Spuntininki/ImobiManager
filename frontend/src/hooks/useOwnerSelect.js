import { useEffect, useState } from "react";

import { useOwners } from "@/hooks/useOwners";

/**
 * Manages the selected-owner state. Defaults to the first owner once the
 * list arrives. Returns the selected id (string|null) + setter, plus the
 * raw `useOwners` return so the caller can trivially destructure both.
 */
export function useOwnerSelect() {
  const ownersState = useOwners();
  const [selectedOwnerId, setSelectedOwnerId] = useState(null);

  useEffect(() => {
    if (selectedOwnerId === null && ownersState.owners.length > 0) {
      setSelectedOwnerId(String(ownersState.owners[0].id));
    }
  }, [ownersState.owners, selectedOwnerId]);

  return { ...ownersState, selectedOwnerId, setSelectedOwnerId };
}