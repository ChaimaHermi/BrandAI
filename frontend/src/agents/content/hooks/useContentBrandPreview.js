import { useCallback, useEffect, useMemo, useState } from "react";
import { fetchBrandingBundle } from "@/agents/brand/api/brandIdentity.api";
import { buildContentProjectDisplay } from "../utils/projectContextFromDb";

/**
 * Charge le bundle branding et retourne l’affichage projet (nom issu du kit, logo, etc.).
 * @param {object | null} idea — idée (au minimum { id } pour le fetch)
 * @param {string | null} token
 */
export function useContentBrandPreview(idea, token) {
  const [bundle, setBundle] = useState(null);

  const loadBundle = useCallback(async () => {
    if (!idea?.id || !token) {
      setBundle(null);
      return;
    }
    try {
      const b = await fetchBrandingBundle(idea.id, token);
      setBundle(b);
    } catch {
      setBundle(null);
    }
  }, [idea?.id, token]);

  useEffect(() => {
    loadBundle();
  }, [loadBundle]);

  return useMemo(() => buildContentProjectDisplay(idea, bundle), [idea, bundle]);
}
