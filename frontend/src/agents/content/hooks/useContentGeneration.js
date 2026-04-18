import { useCallback, useState } from "react";
import { PLATFORMS } from "../constants";
import {
  buildGenerationPayload,
  initialInstagramForm,
  initialFacebookForm,
  initialLinkedInForm,
} from "../contentFormConfig";
import { postContentGeneration } from "../api/contentGeneration.api";

/**
 * @param {{ idea: object | null, token: string | null }} params
 */
export function useContentGeneration({ idea, token }) {
  const [activePlatform, setActivePlatform] = useState(PLATFORMS.instagram);

  const [forms, setForms] = useState({
    [PLATFORMS.instagram]: initialInstagramForm(),
    [PLATFORMS.facebook]: initialFacebookForm(),
    [PLATFORMS.linkedin]: initialLinkedInForm(),
  });

  const [generated, setGenerated] = useState(null);
  const [isGenerating, setIsGenerating] = useState(false);
  const [error, setError] = useState(null);

  const updateForm = useCallback((platform, patch) => {
    setForms((prev) => ({
      ...prev,
      [platform]: { ...prev[platform], ...patch },
    }));
  }, []);

  const setActivePlatformSafe = useCallback((platform) => {
    setActivePlatform(platform);
    setError(null);
  }, []);

  const generate = useCallback(async () => {
    const ideaId = idea?.id;
    if (!ideaId) {
      setError("Projet introuvable.");
      return;
    }

    const formValues = forms[activePlatform];
    if (!(formValues.subject || "").trim()) {
      setError("Indiquez un sujet pour le post.");
      return;
    }

    setError(null);
    setIsGenerating(true);
    setGenerated(null);

    try {
      const payload = buildGenerationPayload(ideaId, activePlatform, formValues);
      const result = await postContentGeneration(payload, token);
      setGenerated({
        caption: result.caption,
        imageUrl: result.image_url || null,
        charCount: result.char_count ?? (result.caption || "").length,
        platform: result.platform || activePlatform,
      });
    } catch (e) {
      setError(e?.message || "La génération a échoué.");
    } finally {
      setIsGenerating(false);
    }
  }, [idea?.id, activePlatform, forms, token]);

  /** Publier : réservé à la phase intégration Meta / LinkedIn */
  const publish = useCallback(() => {
    setError("La publication sera disponible après branchement des comptes sociaux.");
  }, []);

  return {
    activePlatform,
    setActivePlatform: setActivePlatformSafe,
    forms,
    updateForm,
    generated,
    isGenerating,
    error,
    setError,
    generate,
    publish,
  };
}
