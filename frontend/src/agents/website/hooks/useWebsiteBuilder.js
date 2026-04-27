import { useCallback, useEffect, useRef, useState } from "react";
import { useParams } from "react-router-dom";
import { useAuth } from "@/shared/hooks/useAuth";
import {
  apiFetchWebsiteContext,
  apiFetchWebsiteProject,
  apiGenerateWebsiteDescription,
  apiGenerateWebsite,
  apiReviseWebsite,
  apiDeployWebsite,
} from "../api/websiteBuilder.api";

/**
 * Phases :
 *   idle              — au démarrage, pas encore de contexte chargé
 *   loading_context   — fetch GET /context
 *   context_ready     — contexte affiché, on attend "Générer la description"
 *   describing        — génération du concept (POST /description)
 *   description_ready — concept affiché, on attend "Générer le site"
 *   generating        — génération HTML (POST /generate)
 *   ready             — site rendu dans iframe ; révisions possibles
 *   revising          — POST /revise en cours
 *   deploying         — POST /deploy + polling
 *   deployed          — URL Vercel obtenue
 *   error             — erreur récupérable (le chat affiche un message)
 */

let _msgSeq = 0;
function newId(kind) {
  _msgSeq += 1;
  return `${kind}-${Date.now()}-${_msgSeq}`;
}

function makeBotMessage(content, opts = {}) {
  return {
    id: newId("bot"),
    role: "bot",
    content,
    createdAt: Date.now(),
    ...opts,
  };
}

function makeUserMessage(content) {
  return {
    id: newId("user"),
    role: "user",
    content,
    createdAt: Date.now(),
  };
}

function makeSystemMessage(content, kind = "info") {
  return {
    id: newId("sys"),
    role: "system",
    kind,
    content,
    createdAt: Date.now(),
  };
}

function toUiMessage(savedMsg) {
  if (!savedMsg || typeof savedMsg !== "object") return null;
  const role = savedMsg.role === "assistant" ? "bot" : savedMsg.role;
  const createdAtRaw = Date.parse(String(savedMsg.created_at || ""));
  const createdAt = Number.isFinite(createdAtRaw) ? createdAtRaw : Date.now();
  const msgType = String(savedMsg.type || "");
  const meta = savedMsg.meta && typeof savedMsg.meta === "object" ? savedMsg.meta : null;
  const deploymentFromMeta = meta && (meta.full_url || meta.url) ? meta : null;

  const base = {
    id: savedMsg.id || newId(role === "bot" ? "bot" : role === "user" ? "user" : "sys"),
    role,
    content: String(savedMsg.content || ""),
    createdAt,
  };

  if (role === "system") {
    return {
      ...base,
      kind: msgType.includes("error") ? "error" : "info",
    };
  }

  if (role === "bot") {
    return {
      ...base,
      ...(msgType === "description_result" ? { title: "Phase 2 — Concept créatif" } : {}),
      ...(msgType === "generation_result" ? { title: "Phase 3 — Site généré" } : {}),
      ...(msgType === "deploy_result" ? { title: "Phase 5 — Site en ligne" } : {}),
      ...(msgType === "deploy_result" && deploymentFromMeta ? { deployment: deploymentFromMeta } : {}),
    };
  }

  return base;
}

function derivePhaseFromProject(project) {
  if (!project || typeof project !== "object") return "context_ready";
  if (project.status === "deployed" || project.status === "approved" || project.last_deployment_url) {
    return "deployed";
  }
  if (project.current_html) return "ready";
  if (project.description_json) return "description_ready";
  return "context_ready";
}

export function useWebsiteBuilder() {
  const { id: routeId } = useParams();
  const { token } = useAuth();

  const ideaId = (() => {
    const parsed = Number.parseInt(String(routeId ?? ""), 10);
    return Number.isFinite(parsed) && parsed > 0 ? parsed : null;
  })();

  const [phase, setPhase] = useState("idle");
  const [context, setContext] = useState(null);
  const [description, setDescription] = useState(null);
  const [html, setHtml] = useState("");
  const [htmlStats, setHtmlStats] = useState(null);
  const [deployment, setDeployment] = useState(null);
  const [messages, setMessages] = useState([]);
  const [error, setError] = useState(null);
  const [approved, setApproved] = useState(false);
  const [currentVersion, setCurrentVersion] = useState(0);

  const bootstrappedRef = useRef(false);

  const pushBot = useCallback((content, opts) => {
    setMessages((m) => [...m, makeBotMessage(content, opts)]);
  }, []);
  const pushUser = useCallback((content) => {
    setMessages((m) => [...m, makeUserMessage(content)]);
  }, []);
  const pushSystem = useCallback((content, kind) => {
    setMessages((m) => [...m, makeSystemMessage(content, kind)]);
  }, []);

  // ── PHASE 1 : Context ─────────────────────────────────────────────────────
  const loadContext = useCallback(async ({ silent = false } = {}) => {
    if (!ideaId || !token) return;
    setPhase("loading_context");
    setError(null);
    try {
      const data = await apiFetchWebsiteContext(token, ideaId);
      // GET /website/context renvoie un payload "flat" (pas { context: ... }).
      const flatContext = data && typeof data === "object"
        ? {
            idea_id: data.idea_id,
            project_name: data.project_name,
            sector: data.sector,
            target_audience: data.target_audience,
            short_pitch: data.short_pitch,
            description_brief: data.description_brief,
            language: data.language,
            brand_name: data.brand_name,
            slogan: data.slogan,
            logo_url: data.logo_url,
            primary_color: data.primary_color,
            secondary_color: data.secondary_color,
            accent_color: data.accent_color,
            background_color: data.background_color,
            text_color: data.text_color,
            title_font: data.title_font,
            body_font: data.body_font,
            visual_style: data.visual_style,
            raw_logo: data.raw_logo,
          }
        : null;

      setContext(flatContext);
      if (!silent) {
        pushBot("Contexte projet et identité de marque chargés.", {
          phase: "context",
          title: "Phase 1 — Contexte chargé",
          context: flatContext,
        });
        pushBot(
          "Prêt à imaginer votre site ? Je peux te proposer un **concept créatif** (sections, animations, ambiance) avant de coder.",
          {
            phase: "context",
            actions: [
              { id: "describe", label: "Générer la description" },
            ],
          }
        );
      }
      setPhase((prev) => {
        // If a persisted editable/deployed state was restored, keep it.
        if (silent && (prev === "ready" || prev === "deployed")) return prev;
        return "context_ready";
      });
    } catch (err) {
      setError(err?.message || "Impossible de charger le contexte.");
      pushSystem(
        `❌ Impossible de charger le contexte : ${err?.message || "erreur inconnue"}`,
        "error"
      );
      setPhase("error");
    }
  }, [ideaId, token, pushBot, pushSystem]);

  // ── PHASE 2 : Description ─────────────────────────────────────────────────
  const generateDescription = useCallback(async () => {
    if (!ideaId || !token) return;
    pushUser("Génère la description du site");
    setPhase("describing");
    setError(null);
    try {
      const data = await apiGenerateWebsiteDescription(token, { ideaId });
      setDescription(data?.description || null);
      pushBot(
        data?.summary_md || "Concept généré.",
        { phase: "description", title: "Phase 2 — Concept créatif" }
      );
      // Affiche aussi la structure complète générée pour transparence utilisateur.
      if (data?.description && typeof data.description === "object") {
        pushBot(
          "Voici la description complète du site que j'ai générée :",
          {
            phase: "description",
            title: "Description complète (JSON)",
            json: data.description,
          }
        );
      }
      pushBot(
        "Si ça te plaît, je passe à la **génération du HTML complet** (Tailwind + animations). Sinon dis-moi ce qu'il faut changer.",
        {
          phase: "description",
          actions: [
            { id: "generate", label: "Générer le site" },
            { id: "describe_again", label: "Re-générer la description" },
          ],
        }
      );
      setPhase("description_ready");
    } catch (err) {
      setError(err?.message || "Impossible de générer la description.");
      pushSystem(`❌ ${err?.message || "Erreur"}`, "error");
      setPhase("context_ready");
    }
  }, [ideaId, token, pushUser, pushBot, pushSystem]);

  // ── PHASE 3 : Generation ──────────────────────────────────────────────────
  const generateWebsite = useCallback(async () => {
    if (!ideaId || !token) return;
    pushUser("Génère le site");
    setPhase("generating");
    setError(null);
    try {
      const data = await apiGenerateWebsite(token, {
        ideaId,
        description: description || null,
      });
      setHtml(data?.html || "");
      setHtmlStats(data?.html_stats || null);
      pushBot(
        "✅ **Ton site est prêt !** Tu peux le voir à droite. Pour le modifier, écris-moi ta demande dans le chat (ex: « rends le hero plus sombre », « ajoute une section témoignages », ...).",
        {
          phase: "generation",
          title: "Phase 3 — Site généré",
          actions: [
            { id: "deploy", label: "Déployer sur Vercel" },
          ],
        }
      );
      setPhase("ready");
    } catch (err) {
      setError(err?.message || "Génération impossible.");
      pushSystem(`❌ ${err?.message || "Erreur"}`, "error");
      setPhase("description_ready");
    }
  }, [ideaId, token, description, pushUser, pushBot, pushSystem]);

  // ── PHASE 4 : Revision ────────────────────────────────────────────────────
  const reviseWebsite = useCallback(
    async (instruction) => {
      const trimmed = String(instruction || "").trim();
      if (!trimmed || !ideaId || !token || !html || approved) return;
      pushUser(trimmed);
      setPhase("revising");
      setError(null);
      try {
        const data = await apiReviseWebsite(token, {
          ideaId,
          currentHtml: html,
          instruction: trimmed,
        });
        setHtml(data?.html || html);
        setHtmlStats(data?.html_stats || null);
        setCurrentVersion((v) => Math.max(1, v + 1));
        pushBot(
          "✅ Modification appliquée. Le preview est à jour.",
          { phase: "revision" }
        );
        setPhase("ready");
      } catch (err) {
        setError(err?.message || "Révision impossible.");
        pushSystem(`❌ ${err?.message || "Erreur"}`, "error");
        setPhase("ready");
      }
    },
    [ideaId, token, html, approved, pushUser, pushBot, pushSystem]
  );

  // ── PHASE 5 : Deployment ──────────────────────────────────────────────────
  const deployWebsite = useCallback(async () => {
    if (!ideaId || !token || !html) return;
    pushUser("Déploie sur Vercel");
    setPhase("deploying");
    setError(null);
    try {
      const data = await apiDeployWebsite(token, { ideaId, html });
      setDeployment(data?.deployment || null);
      pushBot(
        data?.summary_md || "🎉 Site déployé.",
        {
          phase: "deployment",
          title: "Phase 5 — Site en ligne",
          deployment: data?.deployment,
        }
      );
      setPhase("deployed");
    } catch (err) {
      setError(err?.message || "Déploiement impossible.");
      pushSystem(`❌ Déploiement échoué : ${err?.message || "erreur"}`, "error");
      setPhase("ready");
    }
  }, [ideaId, token, html, pushUser, pushBot, pushSystem]);

  // Action dispatch (for action buttons inside bot messages)
  const handleAction = useCallback(
    (actionId) => {
      switch (actionId) {
        case "describe":
        case "describe_again":
          return generateDescription();
        case "generate":
          return generateWebsite();
        case "deploy":
          return deployWebsite();
        default:
          return undefined;
      }
    },
    [generateDescription, generateWebsite, deployWebsite]
  );

  const bootstrapFromPersistence = useCallback(async () => {
    if (!ideaId || !token) return false;
    try {
      const project = await apiFetchWebsiteProject(token, ideaId);
      if (!project || typeof project !== "object") return false;
      setApproved(Boolean(project.approved));
      setCurrentVersion(Number(project.current_version) || 0);

      let hasRestoredState = false;
      if (
        project.description_json &&
        typeof project.description_json === "object" &&
        Object.keys(project.description_json).length > 0
      ) {
        setDescription(project.description_json);
        hasRestoredState = true;
      }
      if (typeof project.current_html === "string") {
        setHtml(project.current_html);
        if (project.current_html.trim().length > 0) {
          hasRestoredState = true;
        }
      }

      const hasDeploy = Boolean(project.last_deployment_url || project.last_deployment_id);
      if (hasDeploy) {
        setDeployment({
          deployment_id: project.last_deployment_id || null,
          full_url: project.last_deployment_url || null,
          state: project.last_deployment_state || null,
        });
        hasRestoredState = true;
      }

      const savedConversation = Array.isArray(project.conversation_json)
        ? project.conversation_json
            .map((m) => toUiMessage(m))
            .filter(Boolean)
            .sort((a, b) => a.createdAt - b.createdAt)
        : [];

      if (savedConversation.length > 0) {
        setMessages(savedConversation);
        hasRestoredState = true;
      }

      setPhase(derivePhaseFromProject(project));
      return hasRestoredState;
    } catch {
      return false;
    }
  }, [ideaId, token]);

  // Auto bootstrap : restore persisted project + context
  useEffect(() => {
    if (bootstrappedRef.current) return;
    if (!ideaId || !token) return;
    bootstrappedRef.current = true;
    (async () => {
      const restored = await bootstrapFromPersistence();
      await loadContext({ silent: restored });
    })();
  }, [ideaId, token, loadContext, bootstrapFromPersistence]);

  const isBusy =
    phase === "loading_context" ||
    phase === "describing" ||
    phase === "generating" ||
    phase === "revising" ||
    phase === "deploying";

  const canChatRevise = !approved && !isBusy && Boolean(html);

  return {
    ideaId,
    phase,
    isBusy,
    canChatRevise,
    context,
    description,
    html,
    htmlStats,
    deployment,
    messages,
    error,
    approved,
    currentVersion,
    loadContext,
    generateDescription,
    generateWebsite,
    reviseWebsite,
    deployWebsite,
    handleAction,
  };
}

export default useWebsiteBuilder;
