import { useCallback, useState } from "react";
import { PLATFORMS, PLATFORM_LABELS } from "../constants";
import {
  buildGenerationPayload,
  initialInstagramForm,
  initialFacebookForm,
  initialLinkedInForm,
} from "../contentFormConfig";
import { postContentGeneration } from "../api/contentGeneration.api";
import {
  apiCreateGeneratedContent,
  apiPatchGeneratedContent,
} from "@/services/generatedContentApi";

/**
 * @param {{ idea: object | null, token: string | null, publishToPlatform?: (platform: string, payload: { caption: string, imageUrl: string | null }) => Promise<any> }} params
 */
export function useContentGeneration({ idea, token, publishToPlatform }) {
  const [activePlatform, setActivePlatform] = useState(PLATFORMS.instagram);

  const [forms, setForms] = useState({
    [PLATFORMS.instagram]: initialInstagramForm(),
    [PLATFORMS.facebook]: initialFacebookForm(),
    [PLATFORMS.linkedin]: initialLinkedInForm(),
  });

  const [generated, setGenerated] = useState(null);
  const [isGenerating, setIsGenerating] = useState(false);
  const [error, setError] = useState(null);
  /** true = posts ancrés sur l’idée ; false = sujet libre / éducatif sans forcer le projet */
  const [alignWithProject, setAlignWithProject] = useState(true);
  const [publishLoading, setPublishLoading] = useState(false);
  const [publishSuccess, setPublishSuccess] = useState("");

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
    setPublishSuccess("");

    try {
      const payload = buildGenerationPayload(ideaId, activePlatform, formValues, {
        alignWithProject,
      });
      const result = await postContentGeneration(payload, token);
      let dbId = null;
      if (token) {
        try {
          const row = await apiCreateGeneratedContent(ideaId, token, {
            platform: result.platform || activePlatform,
            caption: result.caption,
            image_url: result.image_url || null,
            char_count:
              result.char_count ?? (result.caption || "").length,
          });
          dbId = row?.id ?? null;
        } catch (err) {
          console.warn("[content] Historique BDD non enregistré:", err?.message || err);
        }
      }
      setGenerated({
        caption: result.caption,
        imageUrl: result.image_url || null,
        charCount: result.char_count ?? (result.caption || "").length,
        platform: result.platform || activePlatform,
        dbId,
      });
    } catch (e) {
      setError(e?.message || "La génération a échoué.");
    } finally {
      setIsGenerating(false);
    }
  }, [idea?.id, activePlatform, forms, token, alignWithProject]);

  /** @returns {Promise<boolean>} */
  const publish = useCallback(async () => {
    if (!generated?.caption?.trim()) {
      setError("Générez d’abord un post.");
      return false;
    }
    if (!publishToPlatform) {
      setError("Publication non configurée.");
      return false;
    }
    setError(null);
    setPublishLoading(true);
    try {
      await publishToPlatform(activePlatform, {
        caption: generated.caption,
        imageUrl: generated.imageUrl ?? null,
      });
      if (token && idea?.id && generated?.dbId) {
        try {
          await apiPatchGeneratedContent(idea.id, generated.dbId, token, {
            status: "published",
          });
        } catch (err) {
          console.warn("[content] Statut publié non enregistré:", err?.message || err);
        }
      }
      const label = PLATFORM_LABELS[activePlatform] || activePlatform;
      setPublishSuccess(`Publication publiée sur ${label}.`);
      setTimeout(() => setPublishSuccess(""), 6000);
      return true;
    } catch (e) {
      if (token && idea?.id && generated?.dbId) {
        try {
          await apiPatchGeneratedContent(idea.id, generated.dbId, token, {
            status: "publish_failed",
            publish_error: String(e?.message || "Publication échouée").slice(0, 2000),
          });
        } catch (err) {
          console.warn("[content] Statut échec non enregistré:", err?.message || err);
        }
      }
      setError(e?.message || "Publication échouée.");
      return false;
    } finally {
      setPublishLoading(false);
    }
  }, [generated, activePlatform, publishToPlatform, token, idea?.id]);

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
    publishLoading,
    publishSuccess,
    alignWithProject,
    setAlignWithProject,
  };
}
