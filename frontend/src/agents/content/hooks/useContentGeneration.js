import { useCallback, useState } from "react";
import { toast } from "react-toastify";
import { PLATFORMS, PLATFORM_LABELS } from "../constants";
import {
  buildGenerationPayload,
  initialInstagramForm,
  initialFacebookForm,
  initialLinkedInForm,
} from "../contentFormConfig";
import {
  apiCreateGeneratedContent,
  apiPatchGeneratedContent,
} from "@/services/generatedContentApi";
import { useContentGenerationSSE } from "./useContentGenerationSSE";

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

  const [generatedByPlatform, setGeneratedByPlatform] = useState({});
  const generated = generatedByPlatform[activePlatform] ?? null;
  const [error, setError] = useState(null);
  /** true = posts ancrés sur l'idée ; false = sujet libre / éducatif sans forcer le projet */
  const [alignWithProject, setAlignWithProject] = useState(true);
  const [publishLoading, setPublishLoading] = useState(false);

  // SSE streaming hook — replaces isGenerating + postContentGeneration
  const {
    steps: generationSteps,
    isStreaming: isGenerating,
    sseError,
    startStream,
    resetSSE,
  } = useContentGenerationSSE();

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
    resetSSE();
    setGeneratedByPlatform((prev) => ({ ...prev, [activePlatform]: null }));

    const payload = buildGenerationPayload(ideaId, activePlatform, formValues, {
      alignWithProject,
    });

    // Capture activePlatform in closure for the async callback
    const currentPlatform = activePlatform;

    await startStream(payload, token, {
      onResult: async (result) => {
        // result = { success: true, caption, image_url, char_count, platform }
        let dbId = null;
        if (token) {
          try {
            const row = await apiCreateGeneratedContent(ideaId, token, {
              platform: result.platform || currentPlatform,
              caption: result.caption,
              image_url: result.image_url || null,
              char_count:
                result.char_count ?? (result.caption || "").length,
            });
            dbId = row?.id ?? null;
          } catch (err) {
            console.warn("[content] Historique BDD non enregistré:", err?.message || err);
            toast.warning("Post généré, mais l'historique n'a pas pu être enregistré.");
          }
        }
        setGeneratedByPlatform((prev) => ({
          ...prev,
          [currentPlatform]: {
            caption: result.caption,
            imageUrl: result.image_url || null,
            charCount: result.char_count ?? (result.caption || "").length,
            platform: result.platform || currentPlatform,
            dbId,
          },
        }));
      },
      onError: (msg) => setError(msg),
    });
  }, [idea?.id, activePlatform, forms, token, alignWithProject, startStream, resetSSE]);

  /** @returns {Promise<boolean>} */
  const publish = useCallback(async () => {
    const current = generatedByPlatform[activePlatform];
    if (!current?.caption?.trim()) {
      setError("Générez d'abord un post.");
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
        caption:  current.caption,
        imageUrl: current.imageUrl ?? null,
      });
      if (token && idea?.id && current?.dbId) {
        try {
          await apiPatchGeneratedContent(idea.id, current.dbId, token, {
            status: "published",
          });
        } catch (err) {
          console.warn("[content] Statut publié non enregistré:", err?.message || err);
          toast.warning("Publication réussie, mais le statut n'a pas pu être mis à jour.");
        }
      }
      const label = PLATFORM_LABELS[activePlatform] || activePlatform;
      toast.success(`Publié sur ${label} avec succès !`);
      return true;
    } catch (e) {
      const current2 = generatedByPlatform[activePlatform];
      if (token && idea?.id && current2?.dbId) {
        try {
          await apiPatchGeneratedContent(idea.id, current2.dbId, token, {
            status: "publish_failed",
            publish_error: String(e?.message || "Publication échouée").slice(0, 2000),
          });
        } catch (err) {
          console.warn("[content] Statut échec non enregistré:", err?.message || err);
        }
      }
      const errMsg = e?.message || "Publication échouée.";
      setError(errMsg);
      toast.error(errMsg);
      return false;
    } finally {
      setPublishLoading(false);
    }
  }, [generatedByPlatform, activePlatform, publishToPlatform, token, idea?.id]);

  return {
    activePlatform,
    setActivePlatform: setActivePlatformSafe,
    forms,
    updateForm,
    generated,
    isGenerating,
    generationSteps,
    sseError,
    error,
    setError,
    generate,
    publish,
    publishLoading,
    alignWithProject,
    setAlignWithProject,
  };
}
