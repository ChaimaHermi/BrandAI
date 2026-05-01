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

/**
 * Phases :
 *   idle              — au démarrage, pas encore de contexte chargé
 *   loading_context   — fetch GET /context
 *   context_ready     — contexte affiché, on attend "Générer la description"
 *   describing        — génération du concept (POST /description/stream)
 *   description_ready — concept affiché, l'utilisateur peut le raffiner via chat
 *                        ou cliquer sur "J'approuve" pour passer en génération
 *   refining          — phase 2.5, l'agent applique les retours utilisateur
 *   generating        — génération HTML (POST /generate/stream)
 *   ready             — site rendu dans iframe ; révisions possibles
 *   revising          — POST /revise/stream en cours
 *   saving_edits      — sauvegarde des modifications manuelles (mode édition)
 *   deploying         — POST /deploy + polling
 *   deployed          — URL Vercel obtenue
 *   error             — erreur récupérable (le chat affiche un message)
 */

let _msgSeq = 0;
const PREVIEW_INJECTION_START = "<!-- BRANDAI_PREVIEW_INJECTION_START -->";
const PREVIEW_INJECTION_END = "<!-- BRANDAI_PREVIEW_INJECTION_END -->";

// Tokens identifiant les scripts injectés par le preview (guard + edit mode).
// On ne les retire que si tous les tokens du tag <script> appartiennent à
// l'injection — jamais en se basant sur un seul mot fragile (ex: "window.open"
// pourrait apparaître légitimement dans un script applicatif).
const PREVIEW_INJECTION_SCRIPT_TOKENS = [
  "BRANDAI_PREVIEW_READY",
  "BRANDAI_EDIT_MODE_ON",
  "BRANDAI_EDIT_MODE_OFF",
  "BRANDAI_HTML_UPDATE",
  "BRANDAI_REQUEST_HTML",
  "__brandai_edit_mode__",
  "data-brandai-editable",
  "__brandai_edit_styles__",
  "data-img-fallback",
  "isUnsafeNav",
];

function stripInjectedScripts(html) {
  if (!html || typeof html !== "string") return html || "";
  // Itère sur chaque <script>...</script> et retire UNIQUEMENT ceux qui
  // contiennent un de nos tokens. Le regex est ancré sur le couple ouvrant/
  // fermant pour ne JAMAIS traverser un autre </script> (ce qui sinon
  // engloutissait le contenu HTML entre deux scripts non liés).
  return html.replace(/<script\b[^>]*>([\s\S]*?)<\/script\s*>/gi, (match, body) => {
    return PREVIEW_INJECTION_SCRIPT_TOKENS.some((token) => body.includes(token))
      ? ""
      : match;
  });
}

// Récupération d'un état déjà corrompu : si un précédent cycle de save a
// laissé "fuir" du code JS d'injection sans balise <script> ouvrante (le
// navigateur l'affiche alors comme du texte sur la page), on essaie de le
// retirer en se basant sur des signatures uniques de notre script d'édition.
const LEAKED_INJECTION_HEADS = [
  "ensureStyles",
  "removeStyles",
  "enableEditMode",
  "disableEditMode",
  "sendHtmlUpdate",
  "scheduleHtmlUpdate",
];
const LEAKED_INJECTION_SIGNATURES = [
  "__brandai_edit_mode__",
  "__brandai_edit_styles__",
  "BRANDAI_PREVIEW_READY",
  "BRANDAI_HTML_UPDATE",
  "BRANDAI_EDIT_MODE_ON",
  "BRANDAI_EDIT_MODE_OFF",
  "data-brandai-editable",
  "data-img-fallback",
  "isUnsafeNav",
];

function stripLeakedInjectedScripts(html) {
  if (!html || typeof html !== "string") return html || "";
  // Heuristique : si aucune signature d'injection n'apparaît hors <script>,
  // on ne touche à rien.
  let cleaned = html;
  // Cas 1 : leak d'un IIFE complet "(() => { ... })();" contenant des tokens.
  cleaned = cleaned.replace(
    /\(\s*\(\s*\)\s*=>\s*\{[\s\S]*?\}\s*\)\s*\(\s*\)\s*;?/g,
    (match) =>
      LEAKED_INJECTION_SIGNATURES.some((s) => match.includes(s)) ? "" : match
  );
  // Cas 2 : leak partiel — la coupe a tronqué le début du script et ne reste
  // qu'une queue commençant par "const ensureStyles = () => { ... })();".
  // On retire en suivant chaque tête connue jusqu'à la prochaine fermeture
  // d'IIFE "})();" si elle est suivie (ou contient) une signature d'injection.
  for (const head of LEAKED_INJECTION_HEADS) {
    const re = new RegExp(
      `\\bconst\\s+${head}\\s*=[\\s\\S]*?\\}\\s*\\)\\s*\\(\\s*\\)\\s*;?`,
      "g"
    );
    cleaned = cleaned.replace(re, (match) =>
      LEAKED_INJECTION_SIGNATURES.some((s) => match.includes(s)) ? "" : match
    );
  }
  // Cas 3 : retire les "</script>" orphelines (sans <script> ouvrant
  // correspondant avant) — typiquement la queue d'un script tronqué par
  // l'ancien bug. On scanne une seule fois en appariant les balises.
  cleaned = removeOrphanClosingScriptTags(cleaned);
  return cleaned;
}

function removeOrphanClosingScriptTags(html) {
  let result = "";
  let i = 0;
  let openCount = 0;
  while (i < html.length) {
    const openMatch = html.substring(i, i + 8).match(/^<script\b/i);
    if (openMatch) {
      const closeIdx = html.indexOf(">", i);
      if (closeIdx < 0) {
        result += html.substring(i);
        break;
      }
      result += html.substring(i, closeIdx + 1);
      i = closeIdx + 1;
      openCount += 1;
      continue;
    }
    const closeMatch = html.substring(i, i + 12).match(/^<\/script\s*>/i);
    if (closeMatch) {
      if (openCount > 0) {
        result += closeMatch[0];
        openCount -= 1;
      }
      // sinon : balise fermante orpheline → on la jette
      i += closeMatch[0].length;
      continue;
    }
    result += html[i];
    i += 1;
  }
  return result;
}

function sanitizePreviewArtifacts(rawHtml) {
  const input = typeof rawHtml === "string" ? rawHtml : "";
  if (!input) return "";
  let cleaned = input;
  // 1) Retire les blocs entre les marqueurs explicites (cas standard).
  while (true) {
    const start = cleaned.indexOf(PREVIEW_INJECTION_START);
    if (start < 0) break;
    const end = cleaned.indexOf(
      PREVIEW_INJECTION_END,
      start + PREVIEW_INJECTION_START.length
    );
    if (end < 0) break;
    cleaned = cleaned.slice(0, start) + cleaned.slice(end + PREVIEW_INJECTION_END.length);
  }
  // 2) Compat : retire les scripts d'injection orphelins (sans marqueurs).
  //    Le strip est borné à un <script>...</script> unique pour ne pas
  //    traverser le contenu utile entre plusieurs scripts.
  cleaned = stripInjectedScripts(cleaned);
  // 2bis) Récupération d'état corrompu : retire le code JS d'injection qui
  //       a "fuité" SANS balise <script> dans des cycles précédents (le
  //       navigateur l'affichait alors comme du texte sur la page).
  cleaned = stripLeakedInjectedScripts(cleaned);
  // 3) Retire le <style> d'édition s'il a été oublié.
  cleaned = cleaned.replace(
    /<style[^>]*id\s*=\s*["']__brandai_edit_styles__["'][^>]*>[\s\S]*?<\/style\s*>/gi,
    ""
  );
  // 4) Retire les attributs résiduels du mode édition sur les éléments éditables.
  cleaned = cleaned
    .replace(/\s+contenteditable\s*=\s*["']true["']/gi, "")
    .replace(/\s+data-brandai-editable\s*=\s*["']1["']/gi, "")
    .replace(/\s+data-brandai-edit-mode\s*=\s*["']1["']/gi, "");
  // 5) Nettoie les marqueurs orphelins si un des deux manque.
  cleaned = cleaned
    .replace(/<!--\s*BRANDAI_PREVIEW_INJECTION_START\s*-->/g, "")
    .replace(/<!--\s*BRANDAI_PREVIEW_INJECTION_END\s*-->/g, "");
  // 6) Évite les fermetures dupliquées qui peuvent apparaître après édition/sauvegarde.
  cleaned = cleaned.replace(/(\s*<\/body>\s*<\/html>\s*){2,}/gi, "\n</body>\n</html>");
  return cleaned.trim();
}

function normalizeWebsiteHtml(rawHtml) {
  const raw = String(rawHtml || "");
  const sanitized = sanitizePreviewArtifacts(raw);
  const cleaned = sanitized || raw;
  const trimmed = cleaned.trim();
  if (!trimmed) return "";

  const lower = trimmed.toLowerCase();
  if (lower.includes("<html") && lower.includes("<body") && lower.includes("</html>")) {
    return trimmed;
  }

  // Si le modèle renvoie un fragment (ou un body/head partiel), on l'enveloppe
  // dans un document complet pour garantir un rendu/ téléchargement valides.
  return `<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Website Preview</title>
</head>
<body>
${trimmed}
</body>
</html>`;
}

function computeHtmlStatsFromString(rawHtml) {
  const html = String(rawHtml || "");
  return {
    length: html.length,
    approx_lines: (html.match(/\n/g) || []).length + 1,
  };
}

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

function stripEmoji(text) {
  return String(text || "")
    .replace(/[\u{1F300}-\u{1FAFF}\u{2600}-\u{27BF}]/gu, "")
    .trim();
}

/**
 * Carte "live" affichée dans le chat pendant qu'une opération SSE tourne.
 * Stocke l'historique des étapes (steps + ticks) reçues du backend.
 */
function makeStepStreamMessage(title) {
  return {
    id: newId("stream"),
    role: "bot",
    content: "",
    createdAt: Date.now(),
    kind: "stream",
    title,
    streamTitle: title,
    streamSteps: [],
    streamTick: null,
    streamStatus: "running",
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
      ...(msgType === "description_refine_result"
        ? { title: "Phase 2.5 — Concept mis à jour" }
        : {}),
      ...(msgType === "generation_result" ? { title: "Phase 3 — Site généré" } : {}),
      ...(msgType === "deploy_result" ? { title: "Phase 5 — Site en ligne" } : {}),
      ...(msgType === "deploy_result" && deploymentFromMeta ? { deployment: deploymentFromMeta } : {}),
    };
  }

  return base;
}

function derivePhaseFromProject(project) {
  if (!project || typeof project !== "object") return "context_ready";
  if (project.status === "deployed" || project.last_deployment_url) {
    return "deployed";
  }
  if (project.current_html) return "ready";
  if (project.description_json) return "description_ready";
  return "context_ready";
}

function ensureResumeGuidance(messages, phase) {
  const list = Array.isArray(messages) ? [...messages] : [];
  const hasAction = (actionId) =>
    list.some(
      (m) =>
        m &&
        Array.isArray(m.actions) &&
        m.actions.some((a) => a && a.id === actionId)
    );

  if (phase === "context_ready" && !hasAction("describe")) {
    list.push(
      makeBotMessage(
        "Session reprise. Tu peux continuer en générant le concept créatif.",
        {
          phase: "context",
          actions: [{ id: "describe", label: "Générer la description" }],
        }
      )
    );
  }

  if (phase === "description_ready" && !hasAction("approve_description")) {
    list.push(
      makeBotMessage(
        "Session reprise. Le concept est prêt : raffine-le via le chat (ex: « ajoute une section pricing ») ou approuve-le pour générer le site.",
        {
          phase: "description",
          actions: [
            { id: "approve_description", label: "J'approuve, générer le site" },
            { id: "describe_again", label: "Re-générer la description" },
          ],
        }
      )
    );
  }

  if (phase === "ready" && !hasAction("deploy")) {
    list.push(
      makeBotMessage(
        "Session reprise. Ton site est prêt ; tu peux le modifier via le chat, l'éditer en place dans le preview, ou le déployer.",
        {
          phase: "generation",
          actions: [{ id: "deploy", label: "Déployer sur Vercel" }],
        }
      )
    );
  }

  if (phase === "deployed") {
    list.push(
      makeBotMessage(
        "Session reprise. Ton site est déjà en ligne ; tu peux demander des modifications dans le chat puis re-déployer quand tu veux.",
        {
          phase: "deployment",
        }
      )
    );
  }

  return list;
}

function hasMessageTitle(messages, title) {
  return (messages || []).some((m) => m && m.title === title);
}

function buildResumeSnapshotMessages(project, flatContext) {
  const snapshots = [];

  if (flatContext && typeof flatContext === "object") {
    snapshots.push(
      makeBotMessage("Contexte restauré depuis la session sauvegardée.", {
        phase: "context",
        title: "Phase 1 — Contexte chargé",
        context: flatContext,
      })
    );
  }

  if (project?.description_json && typeof project.description_json === "object") {
    snapshots.push(
      makeBotMessage("Concept créatif restauré depuis la session sauvegardée.", {
        phase: "description",
        title: "Phase 2 — Concept créatif",
      })
    );
  }

  if (typeof project?.current_html === "string" && project.current_html.trim()) {
    snapshots.push(
      makeBotMessage("Site restauré depuis la session sauvegardée.", {
        phase: "generation",
        title: "Phase 3 — Site généré",
      })
    );
  }

  if (project?.last_deployment_url || project?.last_deployment_id) {
    snapshots.push(
      makeBotMessage("Déploiement restauré depuis la session sauvegardée.", {
        phase: "deployment",
        title: "Phase 5 — Site en ligne",
      })
    );
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
    let steps;
    if (existingIdx >= 0) {
      steps = message.streamSteps.map((s, idx) =>
        idx === existingIdx ? { ...s, label, status, meta: meta || s.meta } : s
      );
    } else {
      steps = [...message.streamSteps, { id, label, status, meta }];
    }
    return {
      ...message,
      streamSteps: steps,
      streamTick: status === "done" ? null : message.streamTick,
    };
  }

  if (type === "tick") {
    return {
      ...message,
      streamTick: {
        id: String(event.id || ""),
        label: String(event.label || ""),
        elapsed: Number(event.elapsed_seconds || 0),
      },
    };
  }

  if (type === "result") {
    return { ...message, streamStatus: "done", streamTick: null };
  }

  if (type === "error") {
    return {
      ...message,
      streamStatus: "error",
      streamError: String(event.message || "Erreur inconnue."),
      streamTick: null,
    };
  }

  if (type === "done") {
    return { ...message, streamTick: null };
  }

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
  const [context, setContext] = useState(null);
  const [description, setDescription] = useState(null);
  const [html, setHtml] = useState("");
  const [htmlStats, setHtmlStats] = useState(null);
  const [deployment, setDeployment] = useState(null);
  const [messages, setMessages] = useState([]);
  const [error, setError] = useState(null);
  const [descriptionApproved, setDescriptionApproved] = useState(false);
  const [currentVersion, setCurrentVersion] = useState(0);

  const bootstrappedRef = useRef(false);
  const descriptionRef = useRef(null);
  const htmlRef = useRef("");

  useEffect(() => {
    descriptionRef.current = description;
  }, [description]);

  useEffect(() => {
    htmlRef.current = html;
  }, [html]);

  const pushBot = useCallback((content, opts) => {
    setMessages((m) => [...m, makeBotMessage(content, opts)]);
  }, []);
  const pushUser = useCallback((content) => {
    setMessages((m) => [...m, makeUserMessage(content)]);
  }, []);
  const pushSystem = useCallback((content, kind) => {
    setMessages((m) => [...m, makeSystemMessage(content, kind)]);
  }, []);

  // Pousse une carte "stream" puis renvoie son id stable. La carte est mise
  // à jour en place via patchStreamMessage à chaque event reçu.
  const pushStreamMessage = useCallback((title) => {
    const msg = makeStepStreamMessage(title);
    setMessages((m) => [...m, msg]);
    return msg.id;
  }, []);

  const patchStreamMessage = useCallback((id, mutator) => {
    setMessages((list) =>
      list.map((m) => (m.id === id ? mutator(m) : m))
    );
  }, []);

  const handleStreamEvent = useCallback(
    (id) => (event) => {
      patchStreamMessage(id, (msg) => applyStreamEvent(msg, event));
    },
    [patchStreamMessage]
  );

  const finalizeStream = useCallback(
    (id, { status = "done", error: errorMsg = null } = {}) => {
      patchStreamMessage(id, (msg) => ({
        ...msg,
        streamStatus: status,
        streamTick: null,
        ...(errorMsg ? { streamError: errorMsg } : {}),
      }));
    },
    [patchStreamMessage]
  );

  // ── PHASE 1 : Context ─────────────────────────────────────────────────────
  const loadContext = useCallback(async ({ silent = false } = {}) => {
    if (!ideaId || !token) return;
    setPhase("loading_context");
    setError(null);
    try {
      const data = await apiFetchWebsiteContext(token, ideaId);
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
          "Prêt à imaginer votre site ? Je vais d'abord te proposer un **concept créatif** détaillé (sections, animations, ton). Tu pourras le raffiner via le chat avant qu'on passe à la génération du HTML.",
          {
            phase: "context",
            actions: [
              { id: "describe", label: "Générer la description" },
            ],
          }
        );
      }
      setPhase((prev) => {
        if (silent && (prev === "ready" || prev === "deployed")) return prev;
        return "context_ready";
      });
    } catch (err) {
      setError(err?.message || "Impossible de charger le contexte.");
      pushSystem(
        `Impossible de charger le contexte : ${err?.message || "erreur inconnue"}`,
        "error"
      );
      setPhase("error");
    }
  }, [ideaId, token, pushBot, pushSystem]);

  // ── PHASE 2 : Description (streamée) ──────────────────────────────────────
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
          if (event?.type === "result" && event.payload) {
            result = event.payload;
          }
        },
      });

      if (!result || !result.description) {
        throw new Error("Aucune description reçue du backend.");
      }

      setDescription(result.description);
      finalizeStream(streamId, { status: "done" });

      pushBot(
        result.description_summary_md || "Concept généré.",
        { phase: "description", title: "Phase 2 — Concept créatif" }
      );

      if (result.description && typeof result.description === "object") {
        pushBot(
          "Voici la description complète du site que j'ai générée :",
          {
            phase: "description",
            title: "Description complète (JSON)",
            json: result.description,
          }
        );
      }

      pushBot(
        "**Discute avec moi pour ajuster ce concept** (ex: « ajoute une section pricing », « rends le hero plus minimaliste », « ton plus chaleureux »...). Quand il te convient, clique sur **« J'approuve »** pour passer à la génération HTML.",
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

  // ── PHASE 2.5 : Refinement (chat avant approbation) ───────────────────────
  const refineDescription = useCallback(
    async (instruction) => {
      const trimmed = String(instruction || "").trim();
      if (!trimmed || !ideaId || !token) return;
      const currentDescription = descriptionRef.current;
      if (!currentDescription || typeof currentDescription !== "object") {
        pushSystem(
          "Génère d'abord une description avant de demander des ajustements.",
          "error"
        );
        return;
      }

      pushUser(trimmed);
      setPhase("refining");
      setError(null);

      const streamId = pushStreamMessage("Phase 2.5 — Affinage du concept (live)");

      try {
        let result = null;
        await apiStreamRefineWebsiteDescription(token, {
          ideaId,
          description: currentDescription,
          instruction: trimmed,
          onEvent: (event) => {
            handleStreamEvent(streamId)(event);
            if (event?.type === "result" && event.payload) {
              result = event.payload;
            }
          },
        });

        if (!result || !result.description) {
          throw new Error("Aucune description mise à jour reçue.");
        }

        setDescription(result.description);
        finalizeStream(streamId, { status: "done" });

        pushBot(
          result.description_summary_md || "Concept mis à jour.",
          { phase: "description", title: "Phase 2.5 — Concept mis à jour" }
        );

        if (result.description && typeof result.description === "object") {
          pushBot(
            "Voici la description mise à jour :",
            {
              phase: "description",
              title: "Description complète (JSON)",
              json: result.description,
            }
          );
        }

        pushBot(
          "Continue les retours si tu veux affiner encore, ou approuve pour générer le site.",
          {
            phase: "description",
            actions: [
              { id: "approve_description", label: "J'approuve, générer le site" },
            ],
          }
        );
        setPhase("description_ready");
      } catch (err) {
        finalizeStream(streamId, { status: "error", error: err?.message });
        setError(err?.message || "Affinage impossible.");
        pushSystem(`${err?.message || "Erreur"}`, "error");
        setPhase("description_ready");
      }
    },
    [ideaId, token, pushUser, pushBot, pushSystem, pushStreamMessage, handleStreamEvent, finalizeStream]
  );

  // ── PHASE 3 : Generation (streamée) ───────────────────────────────────────
  const generateWebsite = useCallback(async () => {
    if (!ideaId || !token) return;
    setPhase("generating");
    setError(null);

    const streamId = pushStreamMessage("Phase 3 — Génération du site HTML (live)");

    try {
      let result = null;
      await apiStreamGenerateWebsite(token, {
        ideaId,
        description: descriptionRef.current || null,
        onEvent: (event) => {
          handleStreamEvent(streamId)(event);
          if (event?.type === "result" && event.payload) {
            result = event.payload;
          }
        },
      });

      if (!result || !result.html) {
        throw new Error("Aucun HTML reçu du backend.");
      }

      setHtml(normalizeWebsiteHtml(result.html));
      setHtmlStats(result.html_stats || null);
      if (result.description) setDescription(result.description);
      setCurrentVersion(1);
      finalizeStream(streamId, { status: "done" });

      pushBot(
        "**Ton site est prêt !** Tu peux le voir à droite. Pour le modifier :\n- Écris-moi une consigne dans le chat (ex: « rends le hero plus sombre »).\n- Ou clique sur **« Modifier le site »** dans le preview pour éditer le texte directement en place.",
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
      finalizeStream(streamId, { status: "error", error: err?.message });
      setError(err?.message || "Génération impossible.");
      pushSystem(`${err?.message || "Erreur"}`, "error");
      setPhase("description_ready");
    }
  }, [ideaId, token, pushBot, pushSystem, pushStreamMessage, handleStreamEvent, finalizeStream]);

  // ── PHASE 2.6 : Approval → bascule vers PHASE 3 ───────────────────────────
  const approveDescription = useCallback(async () => {
    if (!ideaId || !token) return;
    pushUser("J'approuve le concept, génère le site");
    try {
      await apiApproveWebsiteDescription(token, { ideaId });
      setDescriptionApproved(true);
    } catch (err) {
      // L'approbation côté backend n'est pas bloquante pour la génération.
      console.warn("[website_builder] approve failed:", err?.message);
    }
    await generateWebsite();
  }, [ideaId, token, pushUser, generateWebsite]);

  // ── PHASE 4 : Revision (streamée) ─────────────────────────────────────────
  const reviseWebsite = useCallback(
    async (instruction) => {
      const trimmed = String(instruction || "").trim();
      if (!trimmed || !ideaId || !token) return;
      const currentHtml = htmlRef.current;
      if (!currentHtml) return;

      pushUser(trimmed);
      setPhase("revising");
      setError(null);

      try {
        let result = null;
        await apiStreamReviseWebsite(token, {
          ideaId,
          currentHtml,
          instruction: trimmed,
          onEvent: (event) => {
            if (event?.type === "result" && event.payload) {
              result = event.payload;
            }
          },
        });

        if (!result || typeof result.html !== "string" || !result.html.trim()) {
          throw new Error(
            "Révision backend incomplète : aucun HTML renvoyé par l'agent (erreur fournisseur possible)."
          );
        }

        const finalHtmlRaw = result?.html || currentHtml;
        const finalHtml = normalizeWebsiteHtml(finalHtmlRaw);
        const hasHtmlChanged = finalHtml !== currentHtml;
        setHtml(finalHtml);
        if (result?.html_stats) setHtmlStats(result.html_stats);
        setCurrentVersion((v) => Math.max(1, v + 1));

        if (hasHtmlChanged) {
          pushBot("Modification appliquée. Le preview est à jour.", {
            phase: "revision",
          });
        } else {
          pushSystem("Aucune modification visible à appliquer sur le preview.", "info");
        }
        setPhase("ready");
      } catch (err) {
        setError(err?.message || "Révision impossible.");
        pushSystem(`${err?.message || "Erreur"}`, "error");
        setPhase("ready");
      }
    },
    [ideaId, token, pushUser, pushBot, pushSystem]
  );

  // ── EDIT MODE : sauvegarde HTML édité manuellement ────────────────────────
  const saveManualEdits = useCallback(
    async (newHtml) => {
      if (!ideaId || !token) return false;
      const trimmed = typeof newHtml === "string" ? newHtml : "";
      const sanitized = normalizeWebsiteHtml(trimmed);
      if (!sanitized) return false;

      setHtml(sanitized);
      setHtmlStats(computeHtmlStatsFromString(sanitized));
      setCurrentVersion((v) => Math.max(1, v + 1));

      setPhase("saving_edits");
      setError(null);
      try {
        const data = await apiReviseWebsite(token, {
          ideaId,
          currentHtml: sanitized,
          instruction: WEBSITE_BUILDER_MANUAL_EDIT_INSTRUCTION,
        });
        const serverHtml = normalizeWebsiteHtml(data?.html || sanitized);
        setHtml(serverHtml);
        if (data?.html_stats) setHtmlStats(data.html_stats);
        pushSystem("Modifications enregistrées.", "info");
        setPhase("ready");
        return true;
      } catch (err) {
        setError(err?.message || "Sauvegarde impossible.");
        pushSystem(
          `Enregistrement impossible (${err?.message || "erreur"}). Le preview affiche encore ta version locale.`,
          "error"
        );
        setPhase("ready");
        return true;
      }
    },
    [ideaId, token, pushSystem]
  );

  // ── PHASE 5 : Deployment ──────────────────────────────────────────────────
  const deployWebsite = useCallback(async () => {
    if (!ideaId || !token || !htmlRef.current) return;
    pushUser("Déploie sur Vercel");
    setPhase("deploying");
    setError(null);
    try {
      const htmlForDeploy = normalizeWebsiteHtml(htmlRef.current);
      const data = await apiDeployWebsite(token, { ideaId, html: htmlForDeploy });
      setDeployment(data?.deployment || null);
      pushBot(
        stripEmoji(data?.summary_md || "Site déployé."),
        {
          phase: "deployment",
          title: "Phase 5 — Site en ligne",
          deployment: data?.deployment,
        }
      );
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
      setError(err?.message || "Suppression du déploiement impossible.");
      setPhase("deployed");
      pushSystem(`Suppression du déploiement échouée : ${err?.message || "erreur"}`, "error");
      return false;
    }
  }, [ideaId, token, deployment, pushSystem]);

  // Action dispatch (for action buttons inside bot messages)
  const handleAction = useCallback(
    (actionId) => {
      switch (actionId) {
        case "describe":
        case "describe_again":
          return generateDescription();
        case "approve_description":
        case "generate":
          return approveDescription();
        case "deploy":
          return deployWebsite();
        default:
          return undefined;
      }
    },
    [generateDescription, approveDescription, deployWebsite]
  );

  // Submit handler unique pour le chat input. Selon la phase courante,
  // il dispatch vers refineDescription (phase 2.5) ou reviseWebsite (phase 4).
  const submitChatMessage = useCallback(
    (instruction) => {
      const trimmed = String(instruction || "").trim();
      if (!trimmed) return;
      const hasGeneratedHtml = Boolean((htmlRef.current || "").trim());
      if (!hasGeneratedHtml && (phase === "description_ready" || phase === "refining")) {
        return refineDescription(trimmed);
      }
      if (hasGeneratedHtml) {
        return reviseWebsite(trimmed);
      }
      return undefined;
    },
    [phase, refineDescription, reviseWebsite]
  );

  const bootstrapFromPersistence = useCallback(async () => {
    if (!ideaId || !token) return false;
    try {
      const project = await apiFetchWebsiteProject(token, ideaId);
      if (!project || typeof project !== "object") return false;
      let restoredContext = null;
      try {
        const ctxData = await apiFetchWebsiteContext(token, ideaId);
        restoredContext = ctxData && typeof ctxData === "object"
          ? {
              idea_id: ctxData.idea_id,
              project_name: ctxData.project_name,
              sector: ctxData.sector,
              target_audience: ctxData.target_audience,
              short_pitch: ctxData.short_pitch,
              description_brief: ctxData.description_brief,
              language: ctxData.language,
              brand_name: ctxData.brand_name,
              slogan: ctxData.slogan,
              logo_url: ctxData.logo_url,
              primary_color: ctxData.primary_color,
              secondary_color: ctxData.secondary_color,
              accent_color: ctxData.accent_color,
              background_color: ctxData.background_color,
              text_color: ctxData.text_color,
              title_font: ctxData.title_font,
              body_font: ctxData.body_font,
              visual_style: ctxData.visual_style,
              raw_logo: ctxData.raw_logo,
            }
          : null;
      } catch {
        restoredContext = null;
      }

      if (restoredContext) {
        setContext(restoredContext);
      }
      setDescriptionApproved(Boolean(project.approved));
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
        setHtml(normalizeWebsiteHtml(project.current_html));
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

      const resumeSnapshots = buildResumeSnapshotMessages(project, restoredContext);
      const mergedConversation = [...savedConversation];
      for (const snap of resumeSnapshots) {
        if (snap?.title && !hasMessageTitle(mergedConversation, snap.title)) {
          mergedConversation.unshift(snap);
        }
      }

      const restoredPhase = derivePhaseFromProject(project);
      if (mergedConversation.length > 0) {
        setMessages(ensureResumeGuidance(mergedConversation, restoredPhase));
        hasRestoredState = true;
      } else if (hasRestoredState) {
        setMessages(ensureResumeGuidance(mergedConversation, restoredPhase));
      }

      setPhase(restoredPhase);
      return hasRestoredState;
    } catch {
      return false;
    }
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
    phase === "loading_context" ||
    phase === "describing" ||
    phase === "refining" ||
    phase === "generating" ||
    phase === "revising" ||
    phase === "saving_edits" ||
    phase === "deploying";

  // Le chat input est utilisable :
  //  - quand on a une description en attente d'approbation (refinement)
  //  - quand on a un site généré (revision)
  const canChatSubmit =
    !isBusy && (
      phase === "description_ready" ||
      phase === "ready" ||
      phase === "deployed" ||
      Boolean((html || "").trim())
    );

  return {
    ideaId,
    phase,
    isBusy,
    canChatSubmit,
    context,
    description,
    html,
    htmlStats,
    deployment,
    messages,
    error,
    descriptionApproved,
    currentVersion,
    loadContext,
    generateDescription,
    refineDescription,
    approveDescription,
    generateWebsite,
    reviseWebsite,
    saveManualEdits,
    deployWebsite,
    clearDeployment,
    handleAction,
    submitChatMessage,
  };
}

export default useWebsiteBuilder;
