import { useState } from "react";
import {
  FiAlertCircle, FiMeh, FiCheckCircle, FiMessageSquare,
  FiTrendingUp, FiExternalLink,
} from "react-icons/fi";

function countItems(arr) {
  return Array.isArray(arr) ? arr.length : 0;
}

function hasItems(arr) {
  return Array.isArray(arr) && arr.length > 0;
}

/* ── Summary stat card ───────────────────────────────────────────────────── */
function StatCard({ icon: Icon, count, label, accent }) {
  return (
    <div className="flex items-center gap-3 rounded-xl border border-brand-border bg-white px-4 py-3 shadow-card">
      <span className={`flex h-9 w-9 shrink-0 items-center justify-center rounded-xl ${accent}`}>
        <Icon size={16} />
      </span>
      <div>
        <p className="text-xl font-bold text-ink">{count}</p>
        <p className="text-2xs uppercase tracking-wide text-ink-subtle">{label}</p>
      </div>
    </div>
  );
}

/* ── Generic item list card ──────────────────────────────────────────────── */
function ItemCard({ icon: Icon, title, count, children }) {
  return (
    <div className="rounded-2xl border border-brand-border bg-white p-5 shadow-card">
      <div className="mb-4 flex items-center gap-2">
        <Icon size={15} className="text-ink-muted" />
        <p className="text-sm font-bold text-ink">{title}</p>
        <span className="rounded-full bg-gray-100 px-2 py-0.5 text-xs text-ink-subtle">{count}</span>
      </div>
      {children}
    </div>
  );
}

function normalizeInsightItem(item) {
  if (typeof item === "string") return { text: item, source: "" };
  if (item && typeof item === "object") {
    return {
      text: typeof item.insight === "string" ? item.insight : "",
      source: typeof item.source === "string" ? item.source : "",
    };
  }
  return { text: "", source: "" };
}

function normalizeQuoteItem(item) {
  if (typeof item === "string") return { quote: item, source: "" };
  if (item && typeof item === "object") {
    return {
      quote: typeof item.quote === "string" ? item.quote : "",
      source: typeof item.source === "string" ? item.source : "",
    };
  }
  return { quote: "", source: "" };
}

function normalizeUrl(value) {
  if (typeof value !== "string") return "";
  const raw = value.trim();
  if (!raw) return "";
  if (/^https?:\/\//i.test(raw)) return raw;
  if (/^[\w.-]+\.[a-z]{2,}(\/.*)?$/i.test(raw)) return `https://${raw}`;
  return "";
}

function SourceLabel({ source, className = "mt-1 text-2xs text-brand" }) {
  if (!source) return null;
  const href = normalizeUrl(source);
  if (!href) return <p className={className}>{source}</p>;
  return (
    <a
      href={href}
      target="_blank"
      rel="noreferrer"
      className={`${className} inline-flex items-center gap-1 hover:underline`}
    >
      <FiExternalLink size={10} />
      {source}
    </a>
  );
}

export default function MarketVOC({ voc }) {
  const [showSources, setShowSources] = useState(false);
  const painPoints      = (voc?.pain_points      ?? []).map(normalizeInsightItem).filter((x) => x.text);
  const frustrations    = (voc?.frustrations     ?? []).map(normalizeInsightItem).filter((x) => x.text);
  const desiredFeatures = (voc?.desired_features ?? []).map(normalizeInsightItem).filter((x) => x.text);
  const userQuotes      = (voc?.user_quotes      ?? []).map(normalizeQuoteItem).filter((x) => x.quote);
  const marketInsights  = (voc?.market_insights  ?? []).map(normalizeInsightItem).filter((x) => x.text);
  const sources         = voc?.sources          ?? [];

  const hasSummary = countItems(painPoints) > 0 || countItems(frustrations) > 0 ||
    countItems(desiredFeatures) > 0 || countItems(userQuotes) > 0;
  const hasPainOrFrustrations = countItems(painPoints) > 0 || countItems(frustrations) > 0;
  const hasDesiredFeatures    = countItems(desiredFeatures) > 0;
  const hasQuotesInsights     = countItems(userQuotes) > 0 || countItems(marketInsights) > 0;
  const hasSources            = countItems(sources) > 0;

  return (
    <div className="flex flex-col gap-4">
      {/* ── Summary stats ───────────────────────────────────────────────── */}
      {hasSummary && (
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
          <StatCard icon={FiAlertCircle} count={countItems(painPoints)}      label="Pain points"  accent="bg-red-50 text-red-500" />
          <StatCard icon={FiMeh}         count={countItems(frustrations)}    label="Frustrations" accent="bg-amber-50 text-amber-500" />
          <StatCard icon={FiCheckCircle} count={countItems(desiredFeatures)} label="Fonctionnalités souhaitées" accent="bg-brand-light text-brand" />
          <StatCard icon={FiMessageSquare} count={countItems(userQuotes)}    label="Verbatims"    accent="bg-success-light text-success" />
        </div>
      )}

      {/* ── Pain points + Frustrations ───────────────────────────────────── */}
      {hasPainOrFrustrations && (
        <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
          {countItems(painPoints) > 0 && (
            <ItemCard icon={FiAlertCircle} title="Pain points" count={countItems(painPoints)}>
              {painPoints.map((item, idx) => (
                <div key={`pp-${idx}`} className="flex gap-2.5 border-b border-gray-50 py-2.5 last:border-0">
                  <span className="mt-2 h-2 w-2 shrink-0 rounded-full bg-red-400" />
                  <div>
                    <p className="text-sm leading-relaxed text-ink-body">{item.text}</p>
                    <SourceLabel source={item.source} />
                  </div>
                </div>
              ))}
            </ItemCard>
          )}
          {countItems(frustrations) > 0 && (
            <ItemCard icon={FiMeh} title="Frustrations" count={countItems(frustrations)}>
              {frustrations.map((item, idx) => (
                <div key={`fr-${idx}`} className="flex gap-3 border-b border-gray-50 py-3 last:border-0">
                  <span className="mt-2 h-2 w-2 shrink-0 rounded-full bg-amber-400" />
                  <div>
                    <p className="text-sm leading-relaxed text-ink-body">{item.text}</p>
                    <SourceLabel source={item.source} />
                  </div>
                </div>
              ))}
            </ItemCard>
          )}
        </div>
      )}

      {/* ── Desired features ─────────────────────────────────────────────── */}
      {hasDesiredFeatures && (
        <ItemCard icon={FiCheckCircle} title="Fonctionnalités souhaitées" count={countItems(desiredFeatures)}>
          <div className="grid grid-cols-1 gap-2 sm:grid-cols-2">
            {desiredFeatures.map((feature, idx) => (
              <div key={`feat-${idx}`} className="flex items-start gap-2 rounded-xl border border-brand-border bg-brand-light px-4 py-3">
                <FiCheckCircle size={14} className="mt-0.5 shrink-0 text-brand" />
                <div>
                  <span className="text-sm text-ink-body">{feature.text}</span>
                  <SourceLabel source={feature.source} />
                </div>
              </div>
            ))}
          </div>
        </ItemCard>
      )}

      {/* ── Verbatims + Market insights ──────────────────────────────────── */}
      {hasQuotesInsights && (
        <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
          {countItems(userQuotes) > 0 && (
            <ItemCard icon={FiMessageSquare} title="Verbatims utilisateurs" count={countItems(userQuotes)}>
              {userQuotes.map((quote, idx) => (
                <div key={`q-${idx}`} className="mb-2.5 border-l-4 border-brand-muted py-1.5 pl-3 last:mb-0">
                  <FiMessageSquare size={22} className="mb-1 text-brand-border" />
                  <p className="text-sm italic leading-relaxed text-ink-body">{quote.quote}</p>
                  <SourceLabel source={quote.source} className="mt-1 text-2xs not-italic text-brand" />
                </div>
              ))}
            </ItemCard>
          )}
          {countItems(marketInsights) > 0 && (
            <ItemCard icon={FiTrendingUp} title="Market insights" count={countItems(marketInsights)}>
              {marketInsights.map((insight, idx) => (
                <div key={`mi-${idx}`} className="flex gap-3 border-b border-gray-50 py-3 last:border-0">
                  <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-brand-light text-xs font-bold text-brand">
                    {idx + 1}
                  </span>
                  <div>
                    <p className="text-sm text-ink-body">{insight.text}</p>
                    <SourceLabel source={insight.source} />
                  </div>
                </div>
              ))}
            </ItemCard>
          )}
        </div>
      )}

      {/* ── Sources VOC ───────────────────────────────────────────────────── */}
      {hasSources && (
        <ItemCard icon={FiExternalLink} title="Sources VOC" count={countItems(sources)}>
          <button
            type="button"
            onClick={() => setShowSources((v) => !v)}
            className="rounded-lg border border-brand-border px-3 py-1.5 text-xs font-semibold text-brand hover:bg-brand-light"
          >
            {showSources ? "Masquer sources" : "Voir sources"}
          </button>
          {showSources && (
            <div className="mt-3 grid grid-cols-1 gap-2">
              {sources.map((s, idx) => {
                const source = typeof s?.source === "string" ? s.source : "web";
                const url    = typeof s?.url    === "string" ? s.url    : "";
                if (!url) return null;
                return (
                  <a
                    key={`src-${source}-${idx}`}
                    href={url}
                    target="_blank"
                    rel="noreferrer"
                    className="flex items-center justify-between rounded-lg border border-brand-border px-3 py-2 text-sm transition-colors hover:bg-brand-light"
                  >
                    <span className="flex items-center gap-2 font-medium uppercase tracking-wide text-ink-muted">
                      <FiExternalLink size={12} className="text-brand-muted" />
                      {source}
                    </span>
                    <span className="ml-4 truncate text-brand">{url}</span>
                  </a>
                );
              })}
            </div>
          )}
        </ItemCard>
      )}

      {!hasSummary && !hasPainOrFrustrations && !hasDesiredFeatures && !hasQuotesInsights && !hasSources && (
        <div className="rounded-xl border border-dashed border-brand-border bg-white px-4 py-3 text-sm italic text-ink-subtle">
          Aucune donnée VOC disponible.
        </div>
      )}
    </div>
  );
}
