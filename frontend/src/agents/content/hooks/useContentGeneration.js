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
  const [regenerationInstruction, setRegenerationInstruction] = useState("");
  const [isEditing, setIsEditing] = useState(false);
  const [draftCaption, setDraftCaption] = useState("");

  const toastByPlatform = useCallback((type, message, platform = activePlatform) => {
    const styles = {
      instagram: { borderLeft: "4px solid #E1306C" },
      facebook: { borderLeft: "4px solid #1877F2" },
      linkedin: { borderLeft: "4px solid #0A66C2" },
    };
    const opts = {
      style: {
        borderRadius: "12px",
        background: "#ffffff",
        color: "#1f2937",
        boxShadow: "0 10px 25px rgba(17,24,39,.08)",
        ...styles[platform],
      },
      progressStyle: { background: styles[platform]?.borderLeft?.split(" ").pop() || "#6b7280" },
    };
    if (type === "success") return toast.success(message, opts);
    if (type === "warning") return toast.warning(message, opts);
    return toast.error(message, opts);
  }, [activePlatform]);

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
    const nextGenerated = generatedByPlatform[platform];
    setDraftCaption(nextGenerated?.caption || "");
    setIsEditing(false);
    setError(null);
  }, [generatedByPlatform]);

  const generate = useCallback(async (options = {}) => {
    const ideaId = idea?.id;
    if (!ideaId) {
      setError("Projet introuvable.");
      toastByPlatform("error", "Projet introuvable.");
      return;
    }

    const formValues = forms[activePlatform];
    if (!(formValues.subject || "").trim()) {
      setError("Indiquez un sujet pour le post.");
      toastByPlatform("warning", "Indiquez un sujet pour le post.");
      return;
    }

    setError(null);
    resetSSE();
    setGeneratedByPlatform((prev) => ({ ...prev, [activePlatform]: null }));

    const instruction = (options.regenerationInstruction || "").trim();
    const previousCaption = (options.previousCaption || "").trim();
    const payload = buildGenerationPayload(ideaId, activePlatform, formValues, {
      alignWithProject,
      regenerationInstruction: instruction,
      previousCaption,
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
            toastByPlatform("warning", "Post généré, mais l'historique n'a pas pu être enregistré.");
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
        setIsEditing(false);
        setDraftCaption(result.caption || "");
        const isRegen = !!instruction || !!previousCaption;
        toastByPlatform(
          "success",
          isRegen ? "Post régénéré avec succès." : "Post généré avec succès.",
          currentPlatform,
        );
      },
      onError: (msg) => {
        setError(msg);
        toastByPlatform("error", msg, currentPlatform);
      },
    });
  }, [idea?.id, activePlatform, forms, token, alignWithProject, startStream, resetSSE, toastByPlatform]);

  const regenerate = useCallback(async () => {
    const current = generatedByPlatform[activePlatform];
    await generate({
      previousCaption: current?.caption || "",
      regenerationInstruction,
    });
  }, [generatedByPlatform, activePlatform, generate, regenerationInstruction]);

  const startEditing = useCallback(() => {
    const current = generatedByPlatform[activePlatform];
    setDraftCaption(current?.caption || "");
    setIsEditing(true);
    setError(null);
    toastByPlatform("success", "Mode édition activé.");
  }, [generatedByPlatform, activePlatform, toastByPlatform]);

  const cancelEditing = useCallback(() => {
    const current = generatedByPlatform[activePlatform];
    setDraftCaption(current?.caption || "");
    setIsEditing(false);
    toastByPlatform("warning", "Modifications annulées.");
  }, [generatedByPlatform, activePlatform, toastByPlatform]);

  const saveEditing = useCallback(async () => {
    const nextCaption = (draftCaption || "").trim();
    if (!nextCaption) {
      setError("Le contenu modifié ne peut pas être vide.");
      toastByPlatform("warning", "Le contenu modifié ne peut pas être vide.");
      return false;
    }

    const current = generatedByPlatform[activePlatform];
    if (!current) {
      setError("Aucun post généré à modifier.");
      toastByPlatform("warning", "Aucun post généré à modifier.");
      return false;
    }

    setGeneratedByPlatform((prev) => ({
      ...prev,
      [activePlatform]: {
        ...prev[activePlatform],
        caption: nextCaption,
        charCount: nextCaption.length,
      },
    }));
    setIsEditing(false);
    setError(null);

    if (token && idea?.id && current?.dbId) {
      try {
        await apiPatchGeneratedContent(idea.id, current.dbId, token, {
          caption: nextCaption,
          char_count: nextCaption.length,
        });
      } catch (err) {
        console.warn("[content] Édition non enregistrée:", err?.message || err);
        toastByPlatform("warning", "Texte modifié localement, mais l'enregistrement a échoué.");
      }
    }
    toastByPlatform("success", "Texte modifié et enregistré.");
    return true;
  }, [draftCaption, generatedByPlatform, activePlatform, token, idea?.id, toastByPlatform]);

  /** @returns {Promise<boolean>} */
  const publish = useCallback(async () => {
    const current = generatedByPlatform[activePlatform];
    if (!current?.caption?.trim()) {
      setError("Générez d'abord un post.");
      toastByPlatform("warning", "Générez d'abord un post.");
      return false;
    }
    if (!publishToPlatform) {
      setError("Publication non configurée.");
      toastByPlatform("error", "Publication non configurée.");
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
          toastByPlatform("warning", "Publication réussie, mais le statut n'a pas pu être mis à jour.");
        }
      }
      const label = PLATFORM_LABELS[activePlatform] || activePlatform;
      toastByPlatform("success", `Publié sur ${label} avec succès !`);
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
      toastByPlatform("error", errMsg);
      return false;
    } finally {
      setPublishLoading(false);
    }
  }, [generatedByPlatform, activePlatform, publishToPlatform, token, idea?.id, toastByPlatform]);

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
    regenerate,
    publish,
    publishLoading,
    alignWithProject,
    setAlignWithProject,
    regenerationInstruction,
    setRegenerationInstruction,
    isEditing,
    draftCaption,
    setDraftCaption,
    startEditing,
    cancelEditing,
    saveEditing,
  };
}
