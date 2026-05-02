import { FiZap, FiRefreshCw, FiInfo, FiCheckCircle } from "react-icons/fi";
import { Button } from "@/shared/ui/Button";
import { PLATFORMS } from "../constants";

function ActionItem({ text, index, color }) {
  return (
    <li className="flex items-start gap-2.5 border-b border-brand-border/50 py-2.5 last:border-0 list-none">
      <span
        className="mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded-full text-[10px] font-black"
        style={{ background: `${color}15`, color, border: `1px solid ${color}30` }}
      >
        {index + 1}
      </span>
      <span className="text-xs leading-relaxed text-ink-body">{text}</span>
    </li>
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
    <aside className="w-72 shrink-0 space-y-3">

      {/* Header card */}
      <div className="overflow-hidden rounded-2xl border border-brand-border bg-white shadow-sm">
        <div
          className="flex items-center justify-between border-b border-brand-border px-3 py-2.5"
          style={{
            background: `linear-gradient(135deg, ${platform.color}08, ${platform.color}03)`,
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
        <div className="max-h-[460px] overflow-y-auto p-3 scrollbar-thin scrollbar-thumb-brand-border scrollbar-track-transparent">

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
                  className="rounded-r-xl py-2 pl-3 pr-2 text-xs leading-relaxed text-ink-body"
                  style={{
                    borderLeft: `3px solid ${platform.color}`,
                    background: `${platform.color}07`,
                  }}
                >
                  {recommendation.summary}
                </p>
              )}

              {recommendation.actions?.length > 0 && (
                <div>
                  <p className="mb-1 text-2xs font-bold uppercase tracking-wider text-ink-muted">
                    Actions recommandées
                  </p>
                  <ul className="m-0 p-0">
                    {recommendation.actions.map((action, i) => (
                      <ActionItem
                        key={i}
                        text={action}
                        index={i}
                        color={platform.color}
                      />
                    ))}
                  </ul>
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
