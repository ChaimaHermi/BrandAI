import { useEffect, useMemo, useRef, useState } from "react";
import {
  FiMonitor, FiTablet, FiSmartphone, FiExternalLink,
  FiDownload, FiRefreshCw, FiCpu, FiCloud, FiGlobe, FiCode,
  FiMaximize2, FiX, FiEdit3, FiSave, FiCheck,
} from "react-icons/fi";

const VIEWPORTS = [
  { id: "desktop", label: "Desktop", Icon: FiMonitor, width: "100%" },
  { id: "tablet", label: "Tablet", Icon: FiTablet, width: "768px" },
  { id: "mobile", label: "Mobile", Icon: FiSmartphone, width: "390px" },
];

// Tags rendus éditables en place (selon spec utilisateur).
const EDITABLE_TAGS = ["h1", "h2", "h3", "h4", "h5", "h6", "p", "button", "span", "li", "a"];

function ViewportSwitcher({ value, onChange }) {
  return (
    <div className="inline-flex items-center gap-0.5 rounded-full border border-brand-border bg-white p-0.5 shadow-card">
      {VIEWPORTS.map((vp) => {
        const active = value === vp.id;
        const Icon = vp.Icon;
        return (
          <button
            key={vp.id}
            type="button"
            onClick={() => onChange(vp.id)}
            className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-2xs font-semibold transition-all duration-200 ${
              active
                ? "bg-gradient-to-br from-brand to-brand-dark text-white shadow-pill"
                : "text-ink-muted hover:bg-brand-light"
            }`}
            aria-label={vp.label}
          >
            <Icon size={11} />
            <span className="hidden md:inline">{vp.label}</span>
          </button>
        );
      })}
    </div>
  );
}

function EmptyState({ phase }) {
  const isDescribing = phase === "describing" || phase === "description_ready" || phase === "context_ready" || phase === "refining";
  const isGenerating = phase === "generating";

  let title = "Le preview apparaîtra ici";
  let subtitle = "Lancez la description puis approuvez pour voir votre site en direct.";
  let Icon = FiCode;
  let pulse = false;

  if (phase === "loading_context") {
    title = "Chargement du projet…";
    subtitle = "Récupération des informations et du brand kit.";
    Icon = FiRefreshCw;
    pulse = true;
  } else if (isGenerating) {
    title = "Construction de votre site…";
    subtitle = "Je rédige le HTML, applique le brand kit et règle les animations.";
    Icon = FiCpu;
    pulse = true;
  } else if (phase === "describing") {
    title = "Imagination du concept…";
    subtitle = "Je définis la structure, les sections et les animations.";
    Icon = FiCpu;
    pulse = true;
  } else if (phase === "refining") {
    title = "Affinage du concept…";
    subtitle = "J'applique tes retours sur la description.";
    Icon = FiCpu;
    pulse = true;
  } else if (isDescribing) {
    title = "Discute le concept à gauche";
    subtitle = "Tu peux affiner la description via le chat, puis approuver pour générer le site.";
    Icon = FiGlobe;
  }

  return (
    <div className="flex h-full flex-col items-center justify-center gap-3 bg-gradient-to-br from-brand-light/40 to-white p-8 text-center">
      <div
        className={`flex h-14 w-14 items-center justify-center rounded-2xl bg-white shadow-card ${
          pulse ? "animate-pulse" : ""
        }`}
      >
        <Icon size={22} className="text-brand" />
      </div>
      <div className="max-w-sm">
        <p className="text-sm font-extrabold text-ink">{title}</p>
        <p className="mt-1 text-xs text-ink-subtle">{subtitle}</p>
      </div>
    </div>
  );
}

function FullscreenOverlay({ kind }) {
  const map = {
    revising: { title: "Application de la modification…", icon: FiRefreshCw },
    deploying: { title: "Déploiement sur Vercel…", icon: FiCloud },
    saving_edits: { title: "Sauvegarde des modifications…", icon: FiSave },
  };
  const cfg = map[kind];
  if (!cfg) return null;
  const Icon = cfg.icon;
  return (
    <div className="absolute inset-0 z-10 flex items-center justify-center bg-white/85 backdrop-blur-sm">
      <div className="flex flex-col items-center gap-3 rounded-2xl border border-brand-border bg-white px-6 py-5 shadow-card">
        <Icon size={22} className="animate-spin text-brand" />
        <p className="text-sm font-bold text-ink">{cfg.title}</p>
      </div>
    </div>
  );
}

/**
 * Construit le HTML rendu dans l'iframe.
 * Injecte :
 *  - un script "guard" (anti-navigation accidentelle, fallback images cassées)
 *  - un script "edit-mode" qui se réveille quand on lui envoie postMessage,
 *    rend les tags éditables, ajoute un outline bleu au hover, et émet
 *    chaque modification vers le parent (HTML_UPDATE).
 */
function buildPreviewHtml(html) {
  if (!html) return "";

  const editableTagsLiteral = JSON.stringify(EDITABLE_TAGS);

  const guardScript = `
<script>
(() => {
  const isExternalHref = (href) => /^(https?:|mailto:|tel:)/i.test(href);
  const originalAssign = window.location.assign.bind(window.location);
  const originalReplace = window.location.replace.bind(window.location);
  const originalOpen = window.open.bind(window);

  const isUnsafeNav = (target) => {
    const v = String(target || "").trim();
    if (!v) return false;
    if (v.startsWith("#")) return false;
    if (isExternalHref(v)) return false;
    return true;
  };

  window.location.assign = (target) => {
    if (isUnsafeNav(target)) return;
    return originalAssign(target);
  };
  window.location.replace = (target) => {
    if (isUnsafeNav(target)) return;
    return originalReplace(target);
  };
  window.open = (target, ...rest) => {
    if (isUnsafeNav(target)) return null;
    return originalOpen(target, ...rest);
  };

  document.addEventListener("click", (e) => {
    // En mode édition, on bloque toute navigation (l'utilisateur veut éditer
    // le texte, pas suivre les liens).
    if (window.__brandai_edit_mode__) {
      const a = e.target && e.target.closest ? e.target.closest("a[href]") : null;
      if (a) e.preventDefault();
      return;
    }
    const a = e.target && e.target.closest ? e.target.closest("a[href]") : null;
    if (!a) return;
    const href = (a.getAttribute("href") || "").trim();
    if (!href || href.startsWith("#")) return;
    if (isExternalHref(href)) {
      a.setAttribute("target", "_blank");
      a.setAttribute("rel", "noopener noreferrer");
      return;
    }
    e.preventDefault();
  }, true);
  document.addEventListener("submit", (e) => {
    e.preventDefault();
  }, true);

  const hideBrokenImage = (img) => {
    if (!img) return;
    img.style.display = "none";
    const placeholder = document.createElement("div");
    placeholder.setAttribute("data-img-fallback", "1");
    placeholder.style.width = (img.width || 320) + "px";
    placeholder.style.height = (img.height || 180) + "px";
    placeholder.style.borderRadius = "12px";
    placeholder.style.background = "linear-gradient(135deg,#f3f4f6,#e5e7eb)";
    placeholder.style.display = "flex";
    placeholder.style.alignItems = "center";
    placeholder.style.justifyContent = "center";
    placeholder.style.color = "#6b7280";
    placeholder.style.fontSize = "12px";
    placeholder.style.fontFamily = "Inter, system-ui, sans-serif";
    placeholder.textContent = "Image indisponible";
    if (img.parentNode) img.parentNode.insertBefore(placeholder, img.nextSibling);
  };

  document.querySelectorAll("img").forEach((img) => {
    img.addEventListener("error", () => hideBrokenImage(img), { once: true });
  });
})();
</script>`;

  const editScript = `
<script>
(() => {
  const EDITABLE_TAGS = ${editableTagsLiteral};
  const STYLE_ID = "__brandai_edit_styles__";

  const ensureStyles = () => {
    if (document.getElementById(STYLE_ID)) return;
    const style = document.createElement("style");
    style.id = STYLE_ID;
    style.textContent = \`
      [data-brandai-editable="1"] {
        outline-offset: 2px;
        transition: outline-color 0.15s ease, background-color 0.15s ease;
        cursor: text;
      }
      [data-brandai-editable="1"]:hover {
        outline: 2px dashed #2563eb !important;
        background-color: rgba(37, 99, 235, 0.06) !important;
      }
      [data-brandai-editable="1"]:focus {
        outline: 2px solid #2563eb !important;
        background-color: rgba(37, 99, 235, 0.1) !important;
      }
    \`;
    document.head.appendChild(style);
  };

  const removeStyles = () => {
    const el = document.getElementById(STYLE_ID);
    if (el && el.parentNode) el.parentNode.removeChild(el);
  };

  const enableEditMode = () => {
    window.__brandai_edit_mode__ = true;
    ensureStyles();
    const selector = EDITABLE_TAGS.join(",");
    document.querySelectorAll(selector).forEach((el) => {
      // Évite les zones de menu mobile/burger contenant des SVG only.
      if (!el.textContent || !el.textContent.trim()) return;
      el.setAttribute("contenteditable", "true");
      el.setAttribute("data-brandai-editable", "1");
      el.setAttribute("spellcheck", "true");
    });
    document.body.setAttribute("data-brandai-edit-mode", "1");
  };

  const disableEditMode = () => {
    window.__brandai_edit_mode__ = false;
    document.querySelectorAll("[data-brandai-editable='1']").forEach((el) => {
      el.removeAttribute("contenteditable");
      el.removeAttribute("data-brandai-editable");
      el.removeAttribute("spellcheck");
    });
    document.body.removeAttribute("data-brandai-edit-mode");
    removeStyles();
  };

  const sendHtmlUpdate = () => {
    try {
      const fullHtml = "<!DOCTYPE html>\\n" + document.documentElement.outerHTML;
      window.parent.postMessage(
        { type: "BRANDAI_HTML_UPDATE", html: fullHtml },
        "*"
      );
    } catch (e) {
      // ignore
    }
  };

  // Throttle : ne pas spammer le parent React à chaque keystroke.
  let pendingTimer = null;
  const scheduleHtmlUpdate = () => {
    if (pendingTimer) clearTimeout(pendingTimer);
    pendingTimer = setTimeout(sendHtmlUpdate, 120);
  };

  document.addEventListener("input", (e) => {
    const target = e.target;
    if (target && target.getAttribute && target.getAttribute("data-brandai-editable") === "1") {
      scheduleHtmlUpdate();
    }
  }, true);

  document.addEventListener("blur", (e) => {
    const target = e.target;
    if (target && target.getAttribute && target.getAttribute("data-brandai-editable") === "1") {
      sendHtmlUpdate();
    }
  }, true);

  // Désactive l'événement Enter par défaut (sinon il insère du HTML inline).
  document.addEventListener("keydown", (e) => {
    if (!window.__brandai_edit_mode__) return;
    const target = e.target;
    if (target && target.getAttribute && target.getAttribute("data-brandai-editable") === "1") {
      if (e.key === "Enter" && (target.tagName === "BUTTON" || target.tagName === "A" || target.tagName === "SPAN")) {
        e.preventDefault();
      }
    }
  }, true);

  window.addEventListener("message", (event) => {
    const data = event && event.data;
    if (!data || typeof data !== "object") return;
    if (data.type === "BRANDAI_EDIT_MODE_ON") {
      enableEditMode();
      sendHtmlUpdate();
      window.parent.postMessage({ type: "BRANDAI_EDIT_MODE_READY", on: true }, "*");
    } else if (data.type === "BRANDAI_EDIT_MODE_OFF") {
      disableEditMode();
      sendHtmlUpdate();
      window.parent.postMessage({ type: "BRANDAI_EDIT_MODE_READY", on: false }, "*");
    } else if (data.type === "BRANDAI_REQUEST_HTML") {
      sendHtmlUpdate();
    }
  });

  // Notifie le parent que le contenu est prêt à recevoir des commandes.
  window.parent.postMessage({ type: "BRANDAI_PREVIEW_READY" }, "*");
})();
</script>`;

  const injection = guardScript + editScript;
  if (html.includes("</body>")) {
    return html.replace("</body>", `${injection}</body>`);
  }
  return `${html}${injection}`;
}

export function PreviewPanel({
  html,
  phase,
  isBusy,
  htmlStats,
  deployment,
  onDeploy,
  onRefresh,
  onSaveEdits,
}) {
  const [viewport, setViewport] = useState("desktop");
  const [isFullscreen, setIsFullscreen] = useState(false);
  const hasHtml = Boolean(html && html.length > 0);

  // Mode édition manuelle (toggle "Modifier le site")
  const [isEditMode, setIsEditMode] = useState(false);
  // HTML "live" pendant l'édition. On ne le pousse PAS dans srcDoc pour ne pas
  // recharger l'iframe à chaque keystroke.
  const [liveHtml, setLiveHtml] = useState("");
  const [showSourcePanel, setShowSourcePanel] = useState(false);
  const [hasUnsavedEdits, setHasUnsavedEdits] = useState(false);

  const iframeRef = useRef(null);

  // En mode édition, on FREEZE la srcDoc pour éviter les rechargements
  // intempestifs : on garde la version envoyée au moment où l'edit a
  // commencé. On utilise un state (et non un ref) pour rester compatible
  // avec les règles React (refs interdits en render).
  const [frozenHtml, setFrozenHtml] = useState(null);
  // Toujours à jour avec la dernière valeur reçue de l'iframe (sans attendre
  // un re-render React).
  const liveHtmlRef = useRef("");
  // Indique qu'on souhaite activer l'edit mode dès que l'iframe émet PREVIEW_READY.
  const pendingEditModeRef = useRef(false);

  const sourceHtml = isEditMode && liveHtml ? liveHtml : html;

  const iframeKey = useMemo(() => {
    if (!hasHtml) return "empty";
    if (isEditMode) return "edit-mode";
    return `${html.length}-${htmlStats?.length || 0}-${htmlStats?.approx_lines || 0}`;
  }, [hasHtml, html, htmlStats, isEditMode]);

  const vp = VIEWPORTS.find((v) => v.id === viewport) || VIEWPORTS[0];

  const safePreviewHtml = useMemo(() => {
    if (!hasHtml) return "";
    if (isEditMode && frozenHtml) {
      return frozenHtml;
    }
    return buildPreviewHtml(html);
  }, [hasHtml, html, isEditMode, frozenHtml]);

  // Écoute les messages postMessage de l'iframe (mises à jour HTML, ready).
  useEffect(() => {
    const onMessage = (event) => {
      const data = event && event.data;
      if (!data || typeof data !== "object") return;

      if (data.type === "BRANDAI_HTML_UPDATE" && typeof data.html === "string") {
        liveHtmlRef.current = data.html;
        setLiveHtml(data.html);
        setHasUnsavedEdits(true);
        return;
      }

      if (data.type === "BRANDAI_PREVIEW_READY") {
        // Si on a demandé l'edit mode juste avant, l'envoyer maintenant.
        if (pendingEditModeRef.current) {
          pendingEditModeRef.current = false;
          const win = iframeRef.current?.contentWindow;
          if (win) {
            win.postMessage({ type: "BRANDAI_EDIT_MODE_ON" }, "*");
          }
        }
      }
    };
    window.addEventListener("message", onMessage);
    return () => window.removeEventListener("message", onMessage);
  }, []);

  // Toggle edit mode : envoie un postMessage à l'iframe.
  const enableEditMode = () => {
    if (!hasHtml) return;
    // Freeze la version actuelle pour empêcher tout reload pendant édition.
    setFrozenHtml(buildPreviewHtml(html));
    liveHtmlRef.current = html;
    setLiveHtml(html);
    setHasUnsavedEdits(false);
    setIsEditMode(true);
    setShowSourcePanel(true);
    // Si l'iframe est déjà chargée (cas rare, même clé), on envoie direct.
    // Sinon on attend BRANDAI_PREVIEW_READY déclenché après le reload (clé "edit-mode").
    pendingEditModeRef.current = true;
    // Failsafe : si "ready" n'arrive pas en 800 ms, on tente quand même.
    setTimeout(() => {
      if (!pendingEditModeRef.current) return;
      pendingEditModeRef.current = false;
      const win = iframeRef.current?.contentWindow;
      if (win) {
        win.postMessage({ type: "BRANDAI_EDIT_MODE_ON" }, "*");
      }
    }, 800);
  };

  const disableEditMode = async ({ persist = true } = {}) => {
    pendingEditModeRef.current = false;
    const win = iframeRef.current?.contentWindow;
    if (win) {
      win.postMessage({ type: "BRANDAI_EDIT_MODE_OFF" }, "*");
    }
    // Petit délai pour laisser l'iframe émettre son dernier HTML_UPDATE.
    await new Promise((r) => setTimeout(r, 250));

    const finalHtml = liveHtmlRef.current || html;
    const changed = hasUnsavedEdits && finalHtml && finalHtml !== html;
    setIsEditMode(false);
    setFrozenHtml(null);

    if (persist && changed && onSaveEdits) {
      const ok = await onSaveEdits(finalHtml);
      if (!ok) {
        // Échec : on garde quand même le liveHtml affiché pour pas perdre
        // le travail de l'utilisateur (il pourra retenter).
        return;
      }
    }
    liveHtmlRef.current = "";
    setLiveHtml("");
    setHasUnsavedEdits(false);
  };

  const toggleEditMode = () => {
    if (isEditMode) {
      disableEditMode({ persist: true });
    } else {
      enableEditMode();
    }
  };

  useEffect(() => {
    if (!isFullscreen) return undefined;
    const onEsc = (e) => {
      if (e.key === "Escape") setIsFullscreen(false);
    };
    window.addEventListener("keydown", onEsc);
    return () => window.removeEventListener("keydown", onEsc);
  }, [isFullscreen]);

  const downloadHtml = () => {
    if (!hasHtml) return;
    const blob = new Blob([sourceHtml], { type: "text/html;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `website-${Date.now()}.html`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const openLive = () => {
    const url = deployment?.full_url || (deployment?.url ? `https://${deployment.url}` : null);
    if (url) window.open(url, "_blank", "noopener,noreferrer");
  };

  const isDeploying = phase === "deploying";
  const isSaving = phase === "saving_edits";
  const canDeploy = hasHtml && !isBusy && !isEditMode;
  const canEdit = hasHtml && !isBusy;

  return (
    <div className="flex h-full flex-col overflow-hidden rounded-2xl border border-brand-border bg-white shadow-card">
      {/* Toolbar */}
      <div className="flex flex-wrap items-center gap-2 border-b border-brand-border bg-white px-3 py-2">
        <ViewportSwitcher value={viewport} onChange={setViewport} />

        {htmlStats && !isEditMode && (
          <span className="hidden rounded-full bg-brand-light px-2 py-0.5 text-2xs font-semibold text-brand-darker md:inline">
            {htmlStats.approx_lines} lignes · {(htmlStats.length / 1000).toFixed(1)} ko
          </span>
        )}

        {isEditMode && (
          <span className="inline-flex items-center gap-1.5 rounded-full bg-blue-50 px-2.5 py-0.5 text-2xs font-bold uppercase tracking-wider text-blue-700">
            <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-blue-500" />
            Mode édition · clique sur un texte
          </span>
        )}

        <div className="ml-auto flex items-center gap-1.5">
          {/* Toggle Modifier le site */}
          <button
            type="button"
            onClick={toggleEditMode}
            disabled={!canEdit}
            className={`inline-flex items-center gap-1.5 rounded-full px-3 py-1.5 text-2xs font-bold shadow-btn transition-all duration-200 hover:-translate-y-px hover:shadow-btn-hover disabled:cursor-not-allowed disabled:opacity-50 ${
              isEditMode
                ? "bg-gradient-to-br from-blue-500 to-blue-600 text-white"
                : "border border-blue-300 bg-white text-blue-600 hover:bg-blue-50"
            }`}
            title={isEditMode ? "Quitter le mode édition (sauvegarde auto)" : "Activer l'édition en place sur le site"}
          >
            {isEditMode ? <FiCheck size={11} /> : <FiEdit3 size={11} />}
            <span className="hidden sm:inline">
              {isEditMode ? "Terminer l'édition" : "Modifier le site"}
            </span>
          </button>

          {isEditMode && (
            <button
              type="button"
              onClick={() => setShowSourcePanel((v) => !v)}
              className={`inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-2xs font-semibold transition-colors ${
                showSourcePanel
                  ? "border-blue-300 bg-blue-50 text-blue-700"
                  : "border-brand-border bg-white text-ink-muted hover:bg-brand-light"
              }`}
              title="Afficher / masquer le code HTML source"
            >
              <FiCode size={11} />
              <span className="hidden md:inline">HTML source</span>
            </button>
          )}

          {deployment?.full_url && !isEditMode && (
            <button
              type="button"
              onClick={openLive}
              className="inline-flex items-center gap-1.5 rounded-full border border-success/30 bg-success/5 px-2.5 py-1 text-2xs font-semibold text-success transition-colors hover:bg-success/10"
              title={deployment.full_url}
            >
              <FiExternalLink size={11} />
              <span className="hidden lg:inline">Voir en ligne</span>
            </button>
          )}

          <button
            type="button"
            onClick={onRefresh}
            disabled={!hasHtml || isBusy || isEditMode}
            className="inline-flex h-7 w-7 items-center justify-center rounded-full border border-brand-border bg-white text-ink-muted transition-colors hover:bg-brand-light disabled:cursor-not-allowed disabled:opacity-40"
            title="Recharger l'iframe"
          >
            <FiRefreshCw size={11} />
          </button>

          <button
            type="button"
            onClick={downloadHtml}
            disabled={!hasHtml}
            className="inline-flex h-7 w-7 items-center justify-center rounded-full border border-brand-border bg-white text-ink-muted transition-colors hover:bg-brand-light disabled:cursor-not-allowed disabled:opacity-40"
            title="Télécharger le HTML"
          >
            <FiDownload size={11} />
          </button>

          <button
            type="button"
            onClick={() => setIsFullscreen(true)}
            disabled={!hasHtml || isEditMode}
            className="inline-flex h-7 w-7 items-center justify-center rounded-full border border-brand-border bg-white text-ink-muted transition-colors hover:bg-brand-light disabled:cursor-not-allowed disabled:opacity-40"
            title="Plein écran"
          >
            <FiMaximize2 size={11} />
          </button>

          <button
            type="button"
            onClick={onDeploy}
            disabled={!canDeploy}
            className="inline-flex items-center gap-1.5 rounded-full bg-gradient-to-br from-brand to-brand-dark px-3 py-1.5 text-2xs font-bold text-white shadow-btn transition-all duration-200 hover:-translate-y-px hover:shadow-btn-hover disabled:cursor-not-allowed disabled:opacity-50"
          >
            <FiCloud size={11} />
            {isDeploying ? "Déploiement…" : deployment ? "Re-déployer" : "Déployer"}
          </button>
        </div>
      </div>

      {/* Stage */}
      <div className="relative flex-1 overflow-hidden bg-[radial-gradient(circle_at_30%_20%,#f0eeff_0%,#ffffff_50%)]">
        {hasHtml ? (
          <div
            className={`grid h-full w-full ${
              isEditMode && showSourcePanel
                ? "grid-cols-1 lg:grid-cols-[3fr_2fr]"
                : "grid-cols-1"
            }`}
          >
            <div className="flex h-full w-full items-start justify-center overflow-auto p-3">
              <div
                className="h-full overflow-hidden rounded-xl border border-brand-border bg-white shadow-card transition-[width] duration-300"
                style={{
                  width: isEditMode ? "100%" : vp.width,
                  maxWidth: "100%",
                }}
              >
                <iframe
                  key={iframeKey}
                  ref={iframeRef}
                  title="Website preview"
                  srcDoc={safePreviewHtml}
                  sandbox="allow-scripts allow-forms allow-popups"
                  className="block h-full w-full border-0"
                />
              </div>
            </div>

            {isEditMode && showSourcePanel && (
              <div className="flex h-full min-h-0 flex-col border-l border-brand-border bg-slate-950 lg:max-h-full">
                <div className="flex items-center justify-between border-b border-slate-800 px-3 py-2">
                  <p className="text-2xs font-bold uppercase tracking-wider text-slate-300">
                    HTML source · live
                  </p>
                  <span className="text-2xs text-slate-500">
                    {sourceHtml.length.toLocaleString()} caractères
                  </span>
                </div>
                <textarea
                  value={sourceHtml}
                  readOnly
                  spellCheck={false}
                  className="flex-1 resize-none bg-slate-950 px-3 py-2 font-mono text-2xs leading-relaxed text-slate-100 focus:outline-none"
                />
              </div>
            )}
          </div>
        ) : (
          <EmptyState phase={phase} />
        )}

        <FullscreenOverlay
          kind={
            isSaving
              ? "saving_edits"
              : phase === "deploying"
                ? "deploying"
                : phase === "revising"
                  ? "revising"
                  : null
          }
        />
      </div>

      {isFullscreen && hasHtml && !isEditMode && (
        <div className="fixed inset-0 z-[80] bg-black/70 backdrop-blur-sm">
          <div className="flex h-full w-full flex-col bg-white">
            <div className="flex items-center justify-between border-b border-brand-border px-3 py-2">
              <p className="text-xs font-bold text-ink">Preview plein écran</p>
              <button
                type="button"
                onClick={() => setIsFullscreen(false)}
                className="inline-flex h-8 w-8 items-center justify-center rounded-full border border-brand-border bg-white text-ink-muted transition-colors hover:bg-brand-light"
                title="Fermer (Esc)"
              >
                <FiX size={14} />
              </button>
            </div>
            <div className="flex-1 overflow-auto bg-[radial-gradient(circle_at_30%_20%,#f0eeff_0%,#ffffff_50%)] p-3">
              <div className="mx-auto h-full w-full overflow-hidden rounded-xl border border-brand-border bg-white shadow-card">
                <iframe
                  key={`${iframeKey}-fullscreen`}
                  title="Website preview fullscreen"
                  srcDoc={safePreviewHtml}
                  sandbox="allow-scripts allow-forms allow-popups"
                  className="block h-full w-full border-0"
                />
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default PreviewPanel;
