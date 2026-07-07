import { useEffect, useState } from "react";

import api from "@/lib/api";

/**
 * Fetch the current user's owners once on mount.
 *
 * Used by pages that list owner-scoped children (renters, addresses,
 * contracts). The backend exposes these only via /owners/{id}/<child>,
 * so the UI must pick an owner first; this hook supplies the list.
 *
 * @returns {{ owners: Array<{id:number,name:string}>, isLoading: boolean, error: string }}
 */
export function useOwners() {
  const [owners, setOwners] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;
    setIsLoading(true);
    setError("");
    api
      .get("/owners")
      .then((resp) => {
        if (!cancelled) setOwners(resp.data);
      })
      .catch(() => {
        if (!cancelled) setError("Não foi possível carregar os proprietários.");
      })
      .finally(() => {
        if (!cancelled) setIsLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  return { owners, isLoading, error };
}