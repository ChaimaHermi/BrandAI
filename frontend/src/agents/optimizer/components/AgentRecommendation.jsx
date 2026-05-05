import { FiZap, FiRefreshCw, FiInfo, FiFlag, FiCheckSquare, FiTarget } from "react-icons/fi";
import { Button } from "@/shared/ui/Button";
import { PLATFORMS } from "../constants";

function PriorityBadge({ priority }) {
  const p = String(priority || "medium").toLowerCase();
  const map = {
    high: { label: "Priorité haute", cls: "bg-red-50 text-red-700 border-red-200" },
    medium: { label: "Priorité moyenne", cls: "bg-amber-50 text-amber-700 border-amber-200" },
    low: { label: "Priorité basse", cls: "bg-emerald-50 text-emerald-700 border-emerald-200" },
  };
  const item = map[p] || map.medium;
  return (
    <span className={`rounded-full border px-2 py-0.5 text-[10px] font-bold ${item.cls}`}>
      {item.label}
    </span>
  );
}

function RecommendationCard({ item, color }) {
  const actions = Array.isArray(item?.actions) ? item.actions : [];
  const priority = String(item?.priority || "medium").toLowerCase();
  const borderColor =
    priority === "high"
      ? "#dc2626"
      : priority === "low"
        ? "#059669"
        : "#d97706";
  return (
    <article
      className="rounded-xl border border-brand-border/70 bg-white px-3 py-2"
      style={{ borderLeft: `4px solid ${borderColor}` }}
    >
      <div className="flex items-start justify-between gap-2">
        <p className="flex items-start gap-1.5 text-xs font-medium text-ink">
          <FiTarget className="mt-0.5 h-3.5 w-3.5 shrink-0 text-ink-muted" />
          <span>
          {item?.title || "Recommandation"}{item?.description ? ` — ${item.description}` : ""}
          </span>
        </p>
        <PriorityBadge priority={item?.priority} />
      </div>
      {actions.length > 0 && (
        <div
          className="mt-1.5 rounded-md px-2 py-1"
          style={{ background: "#f8fafc", border: "1px solid #e2e8f0" }}
        >
          <p className="flex items-start gap-1.5 text-[11px] text-ink">
            <FiCheckSquare className="mt-[1px] h-3.5 w-3.5 shrink-0 text-ink-muted" />
            <span>
            <span className="font-medium text-ink-muted">Actions :</span>
            <span className="ml-1">
              {actions.join(" · ")}
            </span>
            </span>
          </p>
        </div>
      )}
    </article>
  );
}

function SkeletonBlock({ lines = 3 }) {
  return (
    <div className="flex flex-col gap-2 pt-1">
      {Array.from({ length: lines }).map((_, i) => (
        <div
          key={i}
          className="h-3 animate-pulse rounded-md bg-brand-light/60"
          style={{ width: i % 2 === 0 ? "90%" : "70%" }}
        />
      ))}
    </div>
  );
}

/**
 * Panel recommandation toujours visible — aligné sur le style LeftPanel du Content Creator.
 *
 * @param {{
 *   recommendation: import('../types/optimizer.types').Recommendation | null,
 *   loading: boolean,
 *   error: string | null,
 *   activePlatform: string,
 *   onRegenerate: () => void
 * }} props
 */
export function AgentRecommendation({
  recommendation,
  loading,
  error,
  activePlatform,
  onRegenerate,
}) {
  const platform = PLATFORMS[activePlatform];

  return (
    <aside className="w-full space-y-3">

      {/* Header card */}
      <div className="overflow-hidden rounded-2xl border border-brand-border bg-white shadow-sm">
        <div
          className="flex items-center justify-between border-b border-brand-border px-3 py-2.5"
          style={{
            background: "#f8fafc",
          }}
        >
          <div className="flex items-center gap-2">
            <span
              className="flex h-7 w-7 shrink-0 items-center justify-center rounded-xl"
              style={{ background: `${platform.color}18` }}
            >
              <FiZap className="h-3.5 w-3.5" style={{ color: platform.color }} />
            </span>
            <div>
              <p className="text-xs font-bold text-ink">Recommandations IA</p>
              <p className="text-2xs text-ink-muted">{platform.label} · Analyse agent</p>
            </div>
          </div>

          <button
            type="button"
            onClick={onRegenerate}
            disabled={loading}
            title="Régénérer les recommandations"
            className="flex h-7 w-7 items-center justify-center rounded-full border border-brand-border bg-white text-ink-muted transition-colors hover:bg-brand-light hover:text-brand-dark disabled:cursor-not-allowed disabled:opacity-50"
          >
            <FiRefreshCw className={`h-3.5 w-3.5 ${loading ? "animate-spin" : ""}`} />
          </button>
        </div>

        {/* Body */}
        <div className="p-3">

          {error && (
            <div className="mb-3 rounded-xl border border-red-200 bg-red-50 px-3 py-2.5">
              <p className="text-2xs text-red-600">{error}</p>
            </div>
          )}

          {loading && !recommendation && (
            <div className="space-y-3">
              <SkeletonBlock lines={2} />
              <div className="mt-2 border-t border-brand-border/50 pt-3">
                <SkeletonBlock lines={4} />
              </div>
            </div>
          )}

          {!loading && !recommendation && !error && (
            <div className="flex flex-col items-center gap-2 py-8 text-center">
              <FiInfo className="h-6 w-6 text-ink-muted/30" />
              <p className="text-2xs text-ink-muted">Aucune recommandation</p>
              <button
                type="button"
                onClick={onRegenerate}
                className="text-2xs font-semibold text-brand underline-offset-2 hover:underline"
              >
                Générer maintenant
              </button>
            </div>
          )}

          {recommendation && (
            <div className="space-y-3">
              {recommendation.summary && (
                <p
                  className="rounded-xl py-2.5 pl-3 pr-2 text-xs leading-relaxed text-ink-body"
                  style={{
                    borderLeft: "3px solid #cbd5e1",
                    background: "#f8fafc",
                  }}
                >
                  {recommendation.summary}
                </p>
              )}

              {Array.isArray(recommendation.recommendations) && recommendation.recommendations.length > 0 && (
                <div>
                  <p className="mb-1 text-2xs font-bold uppercase tracking-wider text-ink-muted">
                    <span className="inline-flex items-center gap-1">
                      <FiFlag className="h-3.5 w-3.5" />
                      Recommandations
                    </span>
                  </p>
                  <div className="space-y-2">
                    {recommendation.recommendations.map((item, idx) => (
                      <RecommendationCard
                        key={item?.id || `rec-${idx}`}
                        item={item}
                        color={platform.color}
                      />
                    ))}
                  </div>
                </div>
              )}

              {recommendation.generated_at && (
                <p className="text-right text-[10px] text-ink-subtle">
                  Généré le{" "}
                  {new Date(recommendation.generated_at).toLocaleString("fr-FR", {
                    day: "2-digit",
                    month: "short",
                    hour: "2-digit",
                    minute: "2-digit",
                  })}
                </p>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Régénérer — bouton plein largeur en bas */}
      <Button
        type="button"
        variant="secondary"
        size="md"
        fullWidth
        onClick={onRegenerate}
        disabled={loading}
        shape="square"
      >
        <FiRefreshCw className={`h-3.5 w-3.5 ${loading ? "animate-spin" : ""}`} />
        {loading ? "Analyse en cours…" : "Régénérer les recommandations"}
      </Button>

    </aside>
  );
}

export default AgentRecommendation;
