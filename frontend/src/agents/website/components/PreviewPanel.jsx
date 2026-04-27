import { useEffect, useMemo, useState } from "react";
import {
  FiMonitor, FiTablet, FiSmartphone, FiExternalLink,
  FiDownload, FiRefreshCw, FiCpu, FiCloud, FiGlobe, FiCode,
  FiMaximize2, FiX,
} from "react-icons/fi";

const VIEWPORTS = [
  { id: "desktop", label: "Desktop", Icon: FiMonitor, width: "100%" },
  { id: "tablet", label: "Tablet", Icon: FiTablet, width: "768px" },
  { id: "mobile", label: "Mobile", Icon: FiSmartphone, width: "390px" },
];

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
  const isDescribing = phase === "describing" || phase === "description_ready" || phase === "context_ready";
  const isGenerating = phase === "generating";

  let title = "Le preview apparaîtra ici";
  let subtitle = "Lancez la description puis la génération pour voir votre site en direct.";
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
  } else if (isDescribing) {
    title = "Prêt à construire";
    subtitle = "Validez le concept à gauche pour générer le site.";
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

export function PreviewPanel({
  html,
  phase,
  isBusy,
  htmlStats,
  deployment,
  onDeploy,
  onRefresh,
}) {
  const [viewport, setViewport] = useState("desktop");
  const [isFullscreen, setIsFullscreen] = useState(false);
  const hasHtml = Boolean(html && html.length > 0);

  const iframeKey = useMemo(() => {
    if (!hasHtml) return "empty";
    return `${html.length}-${htmlStats?.length || 0}-${htmlStats?.approx_lines || 0}`;
  }, [hasHtml, html, htmlStats]);

  const vp = VIEWPORTS.find((v) => v.id === viewport) || VIEWPORTS[0];

  const safePreviewHtml = useMemo(() => {
    if (!hasHtml) return "";
    // Garde le preview confiné: on bloque les navigations relatives (qui chargeaient parfois l'app).
    const guardScript = `
<script>
(() => {
  const isExternalHref = (href) => /^(https?:|mailto:|tel:)/i.test(href);
  document.addEventListener("click", (e) => {
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
})();
</script>`;

    if (html.includes("</body>")) {
      return html.replace("</body>", `${guardScript}</body>`);
    }
    return `${html}${guardScript}`;
  }, [hasHtml, html]);

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
    const blob = new Blob([html], { type: "text/html;charset=utf-8" });
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
  const canDeploy = hasHtml && !isBusy;

  return (
    <div className="flex h-full flex-col overflow-hidden rounded-2xl border border-brand-border bg-white shadow-card">
      {/* Toolbar */}
      <div className="flex flex-wrap items-center gap-2 border-b border-brand-border bg-white px-3 py-2">
        <ViewportSwitcher value={viewport} onChange={setViewport} />

        {htmlStats && (
          <span className="hidden rounded-full bg-brand-light px-2 py-0.5 text-2xs font-semibold text-brand-darker md:inline">
            {htmlStats.approx_lines} lignes · {(htmlStats.length / 1000).toFixed(1)} ko
          </span>
        )}

        <div className="ml-auto flex items-center gap-1.5">
          {deployment?.full_url && (
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
            disabled={!hasHtml || isBusy}
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
            disabled={!hasHtml}
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
          <div className="flex h-full w-full items-start justify-center overflow-auto p-3">
            <div
              className="h-full overflow-hidden rounded-xl border border-brand-border bg-white shadow-card transition-[width] duration-300"
              style={{
                width: vp.width,
                maxWidth: "100%",
              }}
            >
              <iframe
                key={iframeKey}
                title="Website preview"
                srcDoc={safePreviewHtml}
                sandbox="allow-scripts allow-same-origin allow-forms allow-popups"
                className="block h-full w-full border-0"
              />
            </div>
          </div>
        ) : (
          <EmptyState phase={phase} />
        )}

        <FullscreenOverlay
          kind={phase === "deploying" ? "deploying" : phase === "revising" ? "revising" : null}
        />
      </div>

      {isFullscreen && hasHtml && (
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
                  sandbox="allow-scripts allow-same-origin allow-forms allow-popups"
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
