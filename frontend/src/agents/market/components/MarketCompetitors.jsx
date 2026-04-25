import { useMemo, useState } from "react";
import {
  FiUsers, FiGlobe, FiZap, FiThumbsUp, FiAlertTriangle,
  FiExternalLink, FiTarget,
} from "react-icons/fi";

const AVATAR_PALETTES = [
  { bg: "bg-brand-light",   text: "text-brand-darker" },
  { bg: "bg-blue-100",      text: "text-blue-700" },
  { bg: "bg-emerald-100",   text: "text-emerald-700" },
  { bg: "bg-amber-100",     text: "text-amber-700" },
  { bg: "bg-rose-100",      text: "text-rose-700" },
];

function hasText(v)  { return typeof v === "string" && v.trim().length > 0; }
function hasArray(v) { return Array.isArray(v) && v.length > 0; }

function normalizeExternalUrl(url) {
  if (!hasText(url)) return null;
  const t = url.trim();
  return /^https?:\/\//i.test(t) ? t : `https://${t}`;
}

/* ── Shared section sub-label (same pattern as SectionLabel) ─────────────── */
function SubLabel({ icon: Icon, label, className = "" }) {
  return (
    <div className={`mb-2 flex items-center gap-1.5 border-l-2 border-brand-muted pl-2 ${className}`}>
      <Icon size={12} className="shrink-0 text-brand" />
      <span className="text-xs font-semibold uppercase tracking-[0.07em] text-brand">{label}</span>
    </div>
  );
}

/* ── Stat pill ───────────────────────────────────────────────────────────── */
function StatPill({ icon: Icon, label, value }) {
  return (
    <div className="flex items-center gap-2 rounded-xl border border-brand-border bg-white px-4 py-2.5 shadow-card">
      <span className="flex h-7 w-7 items-center justify-center rounded-lg bg-brand-light">
        <Icon size={13} className="text-brand" />
      </span>
      <div>
        <p className="text-base font-bold text-ink">{value}</p>
        <p className="text-2xs text-ink-subtle">{label}</p>
      </div>
    </div>
  );
}

/* ── Bullet list ─────────────────────────────────────────────────────────── */
function BulletList({ items, dotClass }) {
  return (
    <ul className="space-y-1">
      {items.map((item, i) => (
        <li key={`${item}-${i}`} className="flex items-start gap-2 text-sm">
          <span className={`mt-1.5 h-2 w-2 shrink-0 rounded-full ${dotClass}`} />
          <span className="text-ink-body">{item}</span>
        </li>
      ))}
    </ul>
  );
}

export default function MarketCompetitors({ competitors }) {
  const [showSources, setShowSources] = useState(false);
  const list     = Array.isArray(competitors) ? competitors : [];
  const total    = list.length;
  const direct   = list.filter((c) => c?.type === "direct").length;
  const indirect = list.filter((c) => c?.type === "indirect").length;
  const local    = list.filter((c) => c?.scope === "local").length;
  const global   = list.filter((c) => c?.scope === "global").length;
  const competitorSources = useMemo(() => (
    list
      .map((c) => ({ name: c?.name || "source", url: normalizeExternalUrl(c?.website) }))
      .filter((x) => x.url)
  ), [list]);

  return (
    <div className="flex flex-col gap-4">
      {/* ── Stats row ─────────────────────────────────────────────────────── */}
      <div className="flex flex-wrap gap-3">
        <StatPill icon={FiUsers}  label="Total"     value={total}    />
        <StatPill icon={FiTarget} label="Directs"   value={direct}   />
        <StatPill icon={FiZap}    label="Indirects"  value={indirect} />
        <StatPill icon={FiGlobe}  label="Locaux"    value={local}    />
        <StatPill icon={FiGlobe}  label="Globaux"   value={global}   />
      </div>

      {/* ── Competitor cards ──────────────────────────────────────────────── */}
      {list.map((competitor, index) => {
        const palette     = AVATAR_PALETTES[index % AVATAR_PALETTES.length];
        const name        = competitor?.name ?? "";
        const firstLetter = hasText(name) ? name.trim().charAt(0).toUpperCase() : "?";
        const type        = competitor?.type ?? "";
        const scope       = competitor?.scope ?? "";
        const websiteHref = normalizeExternalUrl(competitor?.website);

        return (
          <div
            key={`${name}-${index}`}
            className="rounded-2xl border border-brand-border bg-white p-5 shadow-card transition-shadow hover:shadow-card-md"
          >
            {/* ── Header: avatar + name + badges ──────────────────────────── */}
            <div className="flex flex-wrap items-start justify-between gap-4">
              <div className="flex items-start gap-3">
                <div className={`flex h-11 w-11 shrink-0 items-center justify-center rounded-full text-sm font-bold ${palette.bg} ${palette.text}`}>
                  {firstLetter}
                </div>
                <div>
                  <p className="text-base font-bold text-ink">{name}</p>
                  {websiteHref && hasText(competitor?.website) && (
                    <a
                      href={websiteHref}
                      target="_blank"
                      rel="noreferrer"
                      className="inline-flex items-center gap-1 text-xs text-brand hover:underline"
                    >
                      <FiExternalLink size={11} />
                      {competitor.website}
                    </a>
                  )}
                </div>
              </div>

              <div className="flex flex-wrap gap-2">
                {hasText(type) && (
                  <span className={
                    type === "direct"
                      ? "rounded-full bg-brand-light px-2.5 py-0.5 text-xs font-semibold text-brand-dark"
                      : "rounded-full bg-gray-100 px-2.5 py-0.5 text-xs font-semibold text-ink-muted"
                  }>
                    {type}
                  </span>
                )}
                {hasText(scope) && (
                  <span className={
                    scope === "local"
                      ? "rounded-full bg-blue-100 px-2.5 py-0.5 text-xs font-semibold text-blue-700"
                      : "rounded-full bg-emerald-100 px-2.5 py-0.5 text-xs font-semibold text-emerald-700"
                  }>
                    {scope}
                  </span>
                )}
              </div>
            </div>

            {/* ── Description + positioning + target ──────────────────────── */}
            <div className="mt-4 space-y-3">
              {hasText(competitor?.description) && (
                <p className="text-sm leading-relaxed text-ink-body">{competitor.description}</p>
              )}
              {hasText(competitor?.positioning) && (
                <div>
                  <SubLabel icon={FiTarget} label="Positionnement" />
                  <p className="text-sm text-ink-body">{competitor.positioning}</p>
                </div>
              )}
              {hasText(competitor?.target_users) && (
                <div>
                  <SubLabel icon={FiUsers} label="Utilisateurs cibles" />
                  <p className="text-sm text-ink-body">{competitor.target_users}</p>
                </div>
              )}
            </div>

            {/* ── Features / Strengths / Weaknesses ───────────────────────── */}
            {(hasArray(competitor?.key_features) || hasArray(competitor?.strengths) || hasArray(competitor?.weaknesses)) && (
              <div className="mt-4 grid grid-cols-1 gap-4 sm:grid-cols-3">
                {hasArray(competitor?.key_features) && (
                  <div>
                    <SubLabel icon={FiZap} label="Fonctionnalités" />
                    <BulletList items={competitor.key_features} dotClass="bg-brand-muted" />
                  </div>
                )}
                {hasArray(competitor?.strengths) && (
                  <div>
                    <div className="mb-2 flex items-center gap-1.5 border-l-2 border-success pl-2">
                      <FiThumbsUp size={12} className="shrink-0 text-success" />
                      <span className="text-xs font-semibold uppercase tracking-[0.07em] text-success">Forces</span>
                    </div>
                    <BulletList items={competitor.strengths} dotClass="bg-success" />
                  </div>
                )}
                {hasArray(competitor?.weaknesses) && (
                  <div>
                    <div className="mb-2 flex items-center gap-1.5 border-l-2 border-red-400 pl-2">
                      <FiAlertTriangle size={12} className="shrink-0 text-red-500" />
                      <span className="text-xs font-semibold uppercase tracking-[0.07em] text-red-500">Faiblesses</span>
                    </div>
                    <BulletList items={competitor.weaknesses} dotClass="bg-red-400" />
                  </div>
                )}
              </div>
            )}

            {/* ── Differentiation / pricing / model ───────────────────────── */}
            {(hasText(competitor?.differentiation) || hasText(competitor?.pricing) || hasText(competitor?.business_model)) && (
              <div className="mt-4 space-y-2">
                {hasText(competitor?.differentiation) && (
                  <p className="border-l-2 border-brand-muted pl-3 text-sm italic text-ink-muted">
                    <span className="font-semibold not-italic text-ink">Différenciation</span>:{" "}
                    {competitor.differentiation}
                  </p>
                )}
                <div className="flex flex-wrap gap-4 text-sm text-ink-body">
                  {hasText(competitor?.pricing) && (
                    <span><span className="font-semibold text-ink">Pricing :</span> {competitor.pricing}</span>
                  )}
                  {hasText(competitor?.business_model) && (
                    <span><span className="font-semibold text-ink">Modèle :</span> {competitor.business_model}</span>
                  )}
                </div>
              </div>
            )}
          </div>
        );
      })}

      {competitorSources.length > 0 && (
        <div className="rounded-xl border border-brand-border bg-white p-4 shadow-card">
          <p className="mb-3 border-l-2 border-brand-muted pl-2 text-xs font-semibold uppercase tracking-[0.07em] text-brand">
            Sources concurrents
          </p>
          <button
            type="button"
            onClick={() => setShowSources((v) => !v)}
            className="rounded-lg border border-brand-border px-3 py-1.5 text-xs font-semibold text-brand hover:bg-brand-light"
          >
            {showSources ? "Masquer sources" : "Voir sources"}
          </button>
          {showSources && (
            <div className="mt-3 grid grid-cols-1 gap-2">
              {competitorSources.map((src, idx) => (
                <a
                  key={`${src.url}-${idx}`}
                  href={src.url}
                  target="_blank"
                  rel="noreferrer"
                  className="flex items-center justify-between rounded-lg border border-brand-border px-3 py-2 text-sm transition-colors hover:bg-brand-light"
                >
                  <span className="flex items-center gap-2 font-medium text-ink-muted">
                    <FiExternalLink size={12} className="text-brand-muted" />
                    {src.name}
                  </span>
                  <span className="ml-4 truncate text-brand">{src.url}</span>
                </a>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
