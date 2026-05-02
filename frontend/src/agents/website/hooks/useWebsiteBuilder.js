import { useCallback, useEffect, useRef, useState } from "react";
import { useParams } from "react-router-dom";
import { useAuth } from "@/shared/hooks/useAuth";
import {
  apiFetchWebsiteContext,
  apiFetchWebsiteProject,
  apiApproveWebsiteDescription,
  apiReviseWebsite,
  apiDeployWebsite,
  apiStreamWebsiteDescription,
  apiStreamRefineWebsiteDescription,
  apiStreamGenerateWebsite,
  apiStreamReviseWebsite,
  apiDeleteWebsiteDeployment,
} from "../api/websiteBuilder.api";
import { WEBSITE_BUILDER_MANUAL_EDIT_INSTRUCTION } from "../config/websiteBuilder.config";
import { normalizeHtml, computeHtmlStats } from "../utils/htmlUtils";

/**
 * Phases :
 *   idle              — initialisation
 *   loading_context   — fetch GET /context
 *   context_ready     — contexte chargé, en attente de "Générer la description"
 *   describing        — Phase 2 stream en cours
 *   description_ready — concept prêt, raffinement possible via chat
 *   refining          — Phase 2.5 stream en cours
 *   generating        — Phase 3 stream en cours
 *   ready             — site prêt ; révisions possibles
 *   revising          — Phase 4 stream en cours (chat)
 *   saving_edits      — Phase 4 REST en cours (édition manuelle)
 *   deploying         — Phase 5 en cours
 *   deployed          — URL Vercel obtenue
 *   error             — erreur récupérable
 */

let _msgSeq = 0;

function newId(kind) {
  _msgSeq += 1;
  return `${kind}-${Date.now()}-${_msgSeq}`;
}

function makeBotMessage(content, opts = {}) {
  return { id: newId("bot"), role: "bot", content, createdAt: Date.now(), ...opts };
}
function makeUserMessage(content) {
  return { id: newId("user"), role: "user", content, createdAt: Date.now() };
}
function makeSystemMessage(content, kind = "info") {
  return { id: newId("sys"), role: "system", kind, content, createdAt: Date.now() };
}
function makeStepStreamMessage(title) {
  return {
    id: newId("stream"), role: "bot", content: "", createdAt: Date.now(),
    kind: "stream", title, streamTitle: title,
    streamSteps: [], streamTick: null, streamStatus: "running",
  };
}

function stripEmoji(text) {
  return String(text || "").replace(/[\u{1F300}-\u{1FAFF}\u{2600}-\u{27BF}]/gu, "").trim();
}

function toUiMessage(savedMsg) {
  if (!savedMsg || typeof savedMsg !== "object") return null;
  const role = savedMsg.role === "assistant" ? "bot" : savedMsg.role;
  const createdAt = Number.isFinite(Date.parse(String(savedMsg.created_at || "")))
    ? Date.parse(String(savedMsg.created_at || ""))
    : Date.now();
  const msgType = String(savedMsg.type || "");
  const meta = savedMsg.meta && typeof savedMsg.meta === "object" ? savedMsg.meta : null;
  const deploymentFromMeta = meta && (meta.full_url || meta.url) ? meta : null;

  const base = {
    id: savedMsg.id || newId(role === "bot" ? "bot" : role === "user" ? "user" : "sys"),
    role, content: String(savedMsg.content || ""), createdAt,
  };

  if (role === "system") return { ...base, kind: msgType.includes("error") ? "error" : "info" };
  if (role === "bot") {
    return {
      ...base,
      ...(msgType === "description_result" ? { title: "Phase 2 — Concept créatif" } : {}),
      ...(msgType === "description_refine_result" ? { title: "Phase 2.5 — Concept mis à jour" } : {}),
      ...(msgType === "generation_result" ? { title: "Phase 3 — Site généré" } : {}),
      ...(msgType === "deploy_result" ? { title: "Phase 5 — Site en ligne" } : {}),
      ...(msgType === "deploy_result" && deploymentFromMeta ? { deployment: deploymentFromMeta } : {}),
    };
  }
  return base;
}

function derivePhaseFromProject(project) {
  if (!project || typeof project !== "object") return "context_ready";
  if (project.status === "deployed" || project.last_deployment_url) return "deployed";
  if (project.current_html) return "ready";
  if (project.description_json) return "description_ready";
  return "context_ready";
}

function hasMessageTitle(messages, title) {
  return (messages || []).some((m) => m && m.title === title);
}

function ensureResumeGuidance(messages, phase) {
  const list = Array.isArray(messages) ? [...messages] : [];
  const hasAction = (id) => list.some((m) => m && Array.isArray(m.actions) && m.actions.some((a) => a?.id === id));

  if (phase === "context_ready" && !hasAction("describe")) {
    list.push(makeBotMessage("Session reprise. Tu peux continuer en générant le concept créatif.", {
      phase: "context", actions: [{ id: "describe", label: "Générer la description" }],
    }));
  }
  if (phase === "description_ready" && !hasAction("approve_description")) {
    list.push(makeBotMessage("Session reprise. Le concept est prêt : raffine-le ou approuve-le pour générer le site.", {
      phase: "description",
      actions: [
        { id: "approve_description", label: "J'approuve, générer le site" },
        { id: "describe_again", label: "Re-générer la description" },
      ],
    }));
  }
  if (phase === "ready" && !hasAction("deploy")) {
    list.push(makeBotMessage("Session reprise. Ton site est prêt ; modifie-le via le chat, édite en place, ou déploie.", {
      phase: "generation", actions: [{ id: "deploy", label: "Déployer sur Vercel" }],
    }));
  }
  if (phase === "deployed") {
    list.push(makeBotMessage("Session reprise. Ton site est déjà en ligne ; tu peux demander des modifications puis re-déployer.", {
      phase: "deployment",
    }));
  }
  return list;
}

function buildResumeSnapshotMessages(project, flatContext) {
  const snapshots = [];
  if (flatContext && typeof flatContext === "object") {
    snapshots.push(makeBotMessage("Contexte restauré depuis la session sauvegardée.", {
      phase: "context", title: "Phase 1 — Contexte chargé", context: flatContext,
    }));
  }
  if (project?.description_json && typeof project.description_json === "object") {
    snapshots.push(makeBotMessage("Concept créatif restauré.", { phase: "description", title: "Phase 2 — Concept créatif" }));
  }
  if (typeof project?.current_html === "string" && project.current_html.trim()) {
    snapshots.push(makeBotMessage("Site restauré.", { phase: "generation", title: "Phase 3 — Site généré" }));
  }
  if (project?.last_deployment_url || project?.last_deployment_id) {
    snapshots.push(makeBotMessage("Déploiement restauré.", { phase: "deployment", title: "Phase 5 — Site en ligne" }));
  }
  return snapshots;
}

function applyStreamEvent(message, event) {
  if (!event || typeof event !== "object") return message;
  const type = event.type;

  if (type === "step") {
    const status = event.status === "done" ? "done" : "running";
    const id = String(event.id || "step");
    const label = String(event.label || "");
    const meta = event.meta && typeof event.meta === "object" ? event.meta : null;
    const existingIdx = message.streamSteps.findIndex((s) => s.id === id);
    const steps = existingIdx >= 0
      ? message.streamSteps.map((s, idx) => idx === existingIdx ? { ...s, label, status, meta: meta || s.meta } : s)
      : [...message.streamSteps, { id, label, status, meta }];
    return { ...message, streamSteps: steps, streamTick: status === "done" ? null : message.streamTick };
  }
  if (type === "tick") {
    return { ...message, streamTick: { id: String(event.id || ""), label: String(event.label || ""), elapsed: Number(event.elapsed_seconds || 0) } };
  }
  if (type === "result") return { ...message, streamStatus: "done", streamTick: null };
  if (type === "error") return { ...message, streamStatus: "error", streamError: String(event.message || "Erreur inconnue."), streamTick: null };
  if (type === "done") return { ...message, streamTick: null };
  return message;
}

export function useWebsiteBuilder() {
  const { id: routeId } = useParams();
  const { token } = useAuth();

  const ideaId = (() => {
    const parsed = Number.parseInt(String(routeId ?? ""), 10);
    return Number.isFinite(parsed) && parsed > 0 ? parsed : null;
  })();

  const [phase, setPhase] = useState("idle");
  const [html, setHtml] = useState("");
  const [htmlStats, setHtmlStats] = useState(null);
  const [deployment, setDeployment] = useState(null);
  const [messages, setMessages] = useState([]);
  const [error, setError] = useState(null);

  const bootstrappedRef = useRef(false);
  const descriptionRef = useRef(null);
  const htmlRef = useRef("");

  useEffect(() => { htmlRef.current = html; }, [html]);

  const pushBot = useCallback((content, opts) => setMessages((m) => [...m, makeBotMessage(content, opts)]), []);
  const pushUser = useCallback((content) => setMessages((m) => [...m, makeUserMessage(content)]), []);
  const pushSystem = useCallback((content, kind) => setMessages((m) => [...m, makeSystemMessage(content, kind)]), []);

  const pushStreamMessage = useCallback((title) => {
    const msg = makeStepStreamMessage(title);
    setMessages((m) => [...m, msg]);
    return msg.id;
  }, []);

  const patchStreamMessage = useCallback((id, mutator) => {
    setMessages((list) => list.map((m) => (m.id === id ? mutator(m) : m)));
  }, []);

  const handleStreamEvent = useCallback(
    (id) => (event) => patchStreamMessage(id, (msg) => applyStreamEvent(msg, event)),
    [patchStreamMessage]
  );

  const finalizeStream = useCallback(
    (id, { status = "done", error: errorMsg = null } = {}) => {
      patchStreamMessage(id, (msg) => ({
        ...msg, streamStatus: status, streamTick: null,
        ...(errorMsg ? { streamError: errorMsg } : {}),
      }));
    },
    [patchStreamMessage]
  );

  // ── Phase 1 : Context ──────────────────────────────────────────────────────
  const loadContext = useCallback(async ({ silent = false } = {}) => {
    if (!ideaId || !token) return;
    setPhase("loading_context");
    setError(null);
    try {
      const data = await apiFetchWebsiteContext(token, ideaId);
      const flatContext = data && typeof data === "object" ? {
        idea_id: data.idea_id, project_name: data.project_name, sector: data.sector,
        target_audience: data.target_audience, short_pitch: data.short_pitch,
        description_brief: data.description_brief, language: data.language,
        brand_name: data.brand_name, slogan: data.slogan, logo_url: data.logo_url,
        primary_color: data.primary_color, secondary_color: data.secondary_color,
        accent_color: data.accent_color, background_color: data.background_color,
        text_color: data.text_color, title_font: data.title_font, body_font: data.body_font,
        visual_style: data.visual_style, raw_logo: data.raw_logo,
      } : null;

      if (!silent) {
        pushBot("Contexte projet et identité de marque chargés.", {
          phase: "context", title: "Phase 1 — Contexte chargé", context: flatContext,
        });
        pushBot(
          "Prêt à imaginer votre site ? Je vais d'abord te proposer un **concept créatif** détaillé. Tu pourras le raffiner avant la génération HTML.",
          { phase: "context", actions: [{ id: "describe", label: "Générer la description" }] }
        );
      }
      setPhase((prev) => (silent && (prev === "ready" || prev === "deployed")) ? prev : "context_ready");
    } catch (err) {
      setError(err?.message || "Impossible de charger le contexte.");
      pushSystem(`Impossible de charger le contexte : ${err?.message || "erreur inconnue"}`, "error");
      setPhase("error");
    }
  }, [ideaId, token, pushBot, pushSystem]);

  // ── Phase 2 : Description (SSE) ───────────────────────────────────────────
  const generateDescription = useCallback(async () => {
    if (!ideaId || !token) return;
    pushUser("Génère la description du site");
    setPhase("describing");
    setError(null);
    const streamId = pushStreamMessage("Phase 2 — Conception du site (live)");

    try {
      let result = null;
      await apiStreamWebsiteDescription(token, {
        ideaId,
        onEvent: (event) => {
          handleStreamEvent(streamId)(event);
          if (event?.type === "result" && event.payload) result = event.payload;
        },
      });

      if (!result?.description) throw new Error("Aucune description reçue du backend.");

      descriptionRef.current = result.description;
      finalizeStream(streamId, { status: "done" });

      pushBot(result.description_summary_md || "Concept généré.", { phase: "description", title: "Phase 2 — Concept créatif" });
      if (result.description && typeof result.description === "object") {
        pushBot("Voici la description complète du site que j'ai générée :", {
          phase: "description", title: "Description complète (JSON)", json: result.description,
        });
      }
      pushBot(
        "**Discute avec moi pour ajuster ce concept** puis clique sur **« J'approuve »** pour passer à la génération HTML.",
        {
          phase: "description",
          actions: [
            { id: "approve_description", label: "J'approuve, générer le site" },
            { id: "describe_again", label: "Re-générer la description" },
          ],
        }
      );
      setPhase("description_ready");
    } catch (err) {
      finalizeStream(streamId, { status: "error", error: err?.message });
      setError(err?.message || "Impossible de générer la description.");
      pushSystem(`${err?.message || "Erreur"}`, "error");
      setPhase("context_ready");
    }
  }, [ideaId, token, pushUser, pushBot, pushSystem, pushStreamMessage, handleStreamEvent, finalizeStream]);

  // ── Phase 2.5 : Refinement (chat avant approbation) ───────────────────────
  const refineDescription = useCallback(async (instruction) => {
    const trimmed = String(instruction || "").trim();
    if (!trimmed || !ideaId || !token) return;
    if (!descriptionRef.current) {
      pushSystem("Génère d'abord une description avant de demander des ajustements.", "error");
      return;
    }
    pushUser(trimmed);
    setPhase("refining");
    setError(null);
    const streamId = pushStreamMessage("Phase 2.5 — Affinage du concept (live)");

    try {
      let result = null;
      await apiStreamRefineWebsiteDescription(token, {
        ideaId, description: descriptionRef.current, instruction: trimmed,
        onEvent: (event) => {
          handleStreamEvent(streamId)(event);
          if (event?.type === "result" && event.payload) result = event.payload;
        },
      });

      if (!result?.description) throw new Error("Aucune description mise à jour reçue.");

      descriptionRef.current = result.description;
      finalizeStream(streamId, { status: "done" });

      pushBot(result.description_summary_md || "Concept mis à jour.", { phase: "description", title: "Phase 2.5 — Concept mis à jour" });
      if (result.description && typeof result.description === "object") {
        pushBot("Voici la description mise à jour :", {
          phase: "description", title: "Description complète (JSON)", json: result.description,
        });
      }
      pushBot("Continue les retours si tu veux affiner encore, ou approuve pour générer le site.", {
        phase: "description",
        actions: [{ id: "approve_description", label: "J'approuve, générer le site" }],
      });
      setPhase("description_ready");
    } catch (err) {
      finalizeStream(streamId, { status: "error", error: err?.message });
      setError(err?.message || "Affinage impossible.");
      pushSystem(`${err?.message || "Erreur"}`, "error");
      setPhase("description_ready");
    }
  }, [ideaId, token, pushUser, pushBot, pushSystem, pushStreamMessage, handleStreamEvent, finalizeStream]);

  // ── Phase 3 : Génération HTML (SSE) ───────────────────────────────────────
  const generateWebsite = useCallback(async () => {
    if (!ideaId || !token) return;
    setPhase("generating");
    setError(null);
    const streamId = pushStreamMessage("Phase 3 — Génération du site HTML (live)");

    try {
      let result = null;
      await apiStreamGenerateWebsite(token, {
        ideaId, description: descriptionRef.current || null,
        onEvent: (event) => {
          handleStreamEvent(streamId)(event);
          if (event?.type === "result" && event.payload) result = event.payload;
        },
      });

      if (!result?.html) throw new Error("Aucun HTML reçu du backend.");

      setHtml(normalizeHtml(result.html));
      setHtmlStats(result.html_stats || null);
      if (result.description) descriptionRef.current = result.description;
      finalizeStream(streamId, { status: "done" });

      pushBot(
        "**Ton site est prêt !** Pour le modifier :\n- Écris-moi une consigne dans le chat.\n- Ou clique sur **« Modifier le site »** dans le preview pour éditer en place.",
        { phase: "generation", title: "Phase 3 — Site généré", actions: [{ id: "deploy", label: "Déployer sur Vercel" }] }
      );
      setPhase("ready");
    } catch (err) {
      finalizeStream(streamId, { status: "error", error: err?.message });
      setError(err?.message || "Génération impossible.");
      pushSystem(`${err?.message || "Erreur"}`, "error");
      setPhase("description_ready");
    }
  }, [ideaId, token, pushBot, pushSystem, pushStreamMessage, handleStreamEvent, finalizeStream]);

  // ── Approval → Phase 3 ────────────────────────────────────────────────────
  const approveDescription = useCallback(async () => {
    if (!ideaId || !token) return;
    pushUser("J'approuve le concept, génère le site");
    try {
      await apiApproveWebsiteDescription(token, { ideaId });
    } catch (err) {
      console.warn("[website_builder] approve failed:", err?.message);
    }
    await generateWebsite();
  }, [ideaId, token, pushUser, generateWebsite]);

  // ── Phase 4 : Révision via chat (SSE avec steps live) ─────────────────────
  const reviseWebsite = useCallback(async (instruction) => {
    const trimmed = String(instruction || "").trim();
    if (!trimmed || !ideaId || !token || !htmlRef.current) return;

    pushUser(trimmed);
    setPhase("revising");
    setError(null);
    const streamId = pushStreamMessage("Phase 4 — Modification en cours (live)");

    try {
      let result = null;
      await apiStreamReviseWebsite(token, {
        ideaId, currentHtml: htmlRef.current, instruction: trimmed,
        onEvent: (event) => {
          handleStreamEvent(streamId)(event);
          if (event?.type === "result" && event.payload) result = event.payload;
        },
      });

      if (!result?.html?.trim()) {
        throw new Error("Révision incomplète : aucun HTML renvoyé par l'agent.");
      }

      setHtml(normalizeHtml(result.html));
      if (result.html_stats) setHtmlStats(result.html_stats);
      finalizeStream(streamId, { status: "done" });
      pushBot("Modification appliquée. Le preview est à jour.", { phase: "revision" });
      setPhase("ready");
    } catch (err) {
      finalizeStream(streamId, { status: "error", error: err?.message });
      setError(err?.message || "Révision impossible.");
      pushSystem(`${err?.message || "Erreur"}`, "error");
      setPhase("ready");
    }
  }, [ideaId, token, pushUser, pushBot, pushSystem, pushStreamMessage, handleStreamEvent, finalizeStream]);

  // ── Phase 4 : Édition manuelle (REST → revise + QA) ──────────────────────
  const saveManualEdits = useCallback(async (newHtml) => {
    if (!ideaId || !token) return false;
    const sanitized = normalizeHtml(typeof newHtml === "string" ? newHtml : "");
    if (!sanitized) return false;

    setHtml(sanitized);
    setHtmlStats(computeHtmlStats(sanitized));
    setPhase("saving_edits");
    setError(null);

    try {
      const data = await apiReviseWebsite(token, {
        ideaId, currentHtml: sanitized,
        instruction: WEBSITE_BUILDER_MANUAL_EDIT_INSTRUCTION,
      });
      setHtml(normalizeHtml(data?.html || sanitized));
      if (data?.html_stats) setHtmlStats(data.html_stats);
      pushSystem("Modifications enregistrées.", "info");
      setPhase("ready");
      return true;
    } catch (err) {
      setError(err?.message || "Sauvegarde impossible.");
      pushSystem(`Enregistrement impossible (${err?.message || "erreur"}). Le preview affiche ta version locale.`, "error");
      setPhase("ready");
      return true;
    }
  }, [ideaId, token, pushSystem]);

  // ── Phase 5 : Déploiement ─────────────────────────────────────────────────
  const deployWebsite = useCallback(async () => {
    if (!ideaId || !token || !htmlRef.current) return;
    pushUser("Déploie sur Vercel");
    setPhase("deploying");
    setError(null);
    try {
      const data = await apiDeployWebsite(token, { ideaId, html: normalizeHtml(htmlRef.current) });
      setDeployment(data?.deployment || null);
      pushBot(stripEmoji(data?.summary_md || "Site déployé."), {
        phase: "deployment", title: "Phase 5 — Site en ligne", deployment: data?.deployment,
      });
      setPhase("deployed");
    } catch (err) {
      setError(err?.message || "Déploiement impossible.");
      pushSystem(`Déploiement échoué : ${err?.message || "erreur"}`, "error");
      setPhase("ready");
    }
  }, [ideaId, token, pushUser, pushBot, pushSystem]);

  const clearDeployment = useCallback(async () => {
    if (!ideaId || !token) return false;
    const depId = String(deployment?.deployment_id || "").trim();
    if (!depId) {
      setDeployment(null);
      setPhase("ready");
      pushSystem("Aucun déploiement actif à supprimer.", "info");
      return true;
    }
    setPhase("deploying");
    setError(null);
    try {
      await apiDeleteWebsiteDeployment(token, { ideaId, deploymentId: depId });
      setDeployment(null);
      setPhase("ready");
      pushSystem("Déploiement Vercel supprimé. Le lien n'est plus actif.", "info");
      return true;
    } catch (err) {
      setError(err?.message || "Suppression impossible.");
      setPhase("deployed");
      pushSystem(`Suppression échouée : ${err?.message || "erreur"}`, "error");
      return false;
    }
  }, [ideaId, token, deployment, pushSystem]);

  // ── Actions (boutons dans les messages bot) ───────────────────────────────
  const handleAction = useCallback((actionId) => {
    switch (actionId) {
      case "describe":
      case "describe_again":     return generateDescription();
      case "approve_description":
      case "generate":           return approveDescription();
      case "deploy":             return deployWebsite();
      default:                   return undefined;
    }
  }, [generateDescription, approveDescription, deployWebsite]);

  // ── Chat input dispatch ───────────────────────────────────────────────────
  const submitChatMessage = useCallback((instruction) => {
    const trimmed = String(instruction || "").trim();
    if (!trimmed) return;
    const hasHtml = Boolean((htmlRef.current || "").trim());
    if (!hasHtml && (phase === "description_ready" || phase === "refining")) return refineDescription(trimmed);
    if (hasHtml) return reviseWebsite(trimmed);
    return undefined;
  }, [phase, refineDescription, reviseWebsite]);

  // ── Bootstrap depuis la persistance ──────────────────────────────────────
  const bootstrapFromPersistence = useCallback(async () => {
    if (!ideaId || !token) return false;
    try {
      const project = await apiFetchWebsiteProject(token, ideaId);
      if (!project || typeof project !== "object") return false;

      let restoredContext = null;
      try {
        const ctxData = await apiFetchWebsiteContext(token, ideaId);
        restoredContext = ctxData && typeof ctxData === "object" ? {
          idea_id: ctxData.idea_id, project_name: ctxData.project_name, sector: ctxData.sector,
          target_audience: ctxData.target_audience, short_pitch: ctxData.short_pitch,
          description_brief: ctxData.description_brief, language: ctxData.language,
          brand_name: ctxData.brand_name, slogan: ctxData.slogan, logo_url: ctxData.logo_url,
          primary_color: ctxData.primary_color, secondary_color: ctxData.secondary_color,
          accent_color: ctxData.accent_color, background_color: ctxData.background_color,
          text_color: ctxData.text_color, title_font: ctxData.title_font, body_font: ctxData.body_font,
          visual_style: ctxData.visual_style, raw_logo: ctxData.raw_logo,
        } : null;
      } catch { restoredContext = null; }

      let hasRestoredState = false;

      if (project.description_json && typeof project.description_json === "object" && Object.keys(project.description_json).length > 0) {
        descriptionRef.current = project.description_json;
        hasRestoredState = true;
      }
      if (typeof project.current_html === "string") {
        setHtml(normalizeHtml(project.current_html));
        if (project.current_html.trim()) hasRestoredState = true;
      }
      if (project.last_deployment_url || project.last_deployment_id) {
        setDeployment({
          deployment_id: project.last_deployment_id || null,
          full_url: project.last_deployment_url || null,
          state: project.last_deployment_state || null,
        });
        hasRestoredState = true;
      }

      const savedConversation = Array.isArray(project.conversation_json)
        ? project.conversation_json.map(toUiMessage).filter(Boolean).sort((a, b) => a.createdAt - b.createdAt)
        : [];

      const resumeSnapshots = buildResumeSnapshotMessages(project, restoredContext);
      const mergedConversation = [...savedConversation];
      for (const snap of resumeSnapshots) {
        if (snap?.title && !hasMessageTitle(mergedConversation, snap.title)) mergedConversation.unshift(snap);
      }

      const restoredPhase = derivePhaseFromProject(project);
      if (mergedConversation.length > 0 || hasRestoredState) {
        setMessages(ensureResumeGuidance(mergedConversation, restoredPhase));
        hasRestoredState = true;
      }

      setPhase(restoredPhase);
      return hasRestoredState;
    } catch { return false; }
  }, [ideaId, token]);

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
    phase === "loading_context" || phase === "describing" || phase === "refining" ||
    phase === "generating" || phase === "revising" || phase === "saving_edits" || phase === "deploying";

  const canChatSubmit =
    !isBusy && (
      phase === "description_ready" || phase === "ready" || phase === "deployed" ||
      Boolean((html || "").trim())
    );

  return {
    phase,
    isBusy,
    canChatSubmit,
    html,
    htmlStats,
    deployment,
    messages,
    error,
    submitChatMessage,
    saveManualEdits,
    deployWebsite,
    clearDeployment,
    handleAction,
  };
}

export default useWebsiteBuilder;
