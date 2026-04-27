import { useState } from "react";
import {
  FiGlobe, FiMessageSquare, FiArrowRight, FiChevronDown, FiChevronUp,
} from "react-icons/fi";
import { FaFacebook, FaInstagram, FaLinkedin } from "react-icons/fa";

const PLATFORMS = [
  {
    key: "facebook",
    label: "Facebook",
    Icon: FaFacebook,
    accent: "#1877F2",
    bg: "bg-blue-50",
    border: "border-blue-200",
    pill: "bg-blue-100 text-blue-700",
    dot: "bg-blue-500",
    headerBg: "from-blue-50 to-blue-100",
    toneBg: "bg-blue-50 border-blue-200",
    ctaBg: "bg-blue-50 border-blue-200",
  },
  {
    key: "instagram",
    label: "Instagram",
    Icon: FaInstagram,
    accent: "#E1306C",
    bg: "bg-pink-50",
    border: "border-pink-200",
    pill: "bg-pink-100 text-pink-700",
    dot: "bg-pink-500",
    headerBg: "from-pink-50 to-rose-50",
    toneBg: "bg-pink-50 border-pink-200",
    ctaBg: "bg-pink-50 border-pink-200",
  },
  {
    key: "linkedin",
    label: "LinkedIn",
    Icon: FaLinkedin,
    accent: "#0A66C2",
    bg: "bg-sky-50",
    border: "border-sky-200",
    pill: "bg-sky-100 text-sky-700",
    dot: "bg-sky-600",
    headerBg: "from-sky-50 to-sky-100",
    toneBg: "bg-sky-50 border-sky-200",
    ctaBg: "bg-sky-50 border-sky-200",
  },
];

function PlatformCard({ config, data }) {
  const [open, setOpen] = useState(false);
  const pillars = Array.isArray(data?.content_pillars) ? data.content_pillars : [];
  const PlatformIcon = config.Icon;

  return (
    <div className={`flex flex-col overflow-hidden rounded-xl border ${config.border} bg-white shadow-sm`}>
      {/* Header */}
      <div className={`flex items-center gap-2 bg-gradient-to-r ${config.headerBg} px-3 py-2.5`}>
        <span className={`flex h-7 w-7 shrink-0 items-center justify-center rounded-lg border ${config.bg} ${config.border}`}>
          <PlatformIcon size={13} style={{ color: config.accent }} />
        </span>
        <div className="min-w-0 flex-1">
          <p className="text-[12px] font-bold text-ink">{config.label}</p>
          {data?.role && <p className="truncate text-[10px] text-ink-subtle">{data.role}</p>}
        </div>
        {pillars.length > 0 && (
          <span className={`rounded-full border px-1.5 py-0.5 text-[10px] font-bold ${config.pill}`}>
            {pillars.length}
          </span>
        )}
        <button type="button" onClick={() => setOpen((o) => !o)} className="ml-1 shrink-0 text-ink-subtle">
          {open ? <FiChevronUp size={12} /> : <FiChevronDown size={12} />}
        </button>
      </div>

      {/* Tone + CTA always visible */}
      {(data?.tone || data?.cta_direction) && (
        <div className="flex flex-wrap gap-1.5 px-3 py-2 border-t border-[color:var(--color-border,#ebebf5)]">
          {data?.tone && (
            <span className="text-[10px] text-ink-muted">
              <span className="font-semibold">Ton:</span> {data.tone}
            </span>
          )}
          {data?.cta_direction && (
            <span className="text-[10px] text-ink-muted">
              · <span className="font-semibold">CTA:</span> {data.cta_direction}
            </span>
          )}
        </div>
      )}

      {/* Pillars — collapsed by default */}
      {open && pillars.length > 0 && (
        <div className="flex flex-col gap-1.5 border-t border-[color:var(--color-border,#ebebf5)] px-3 py-2">
          {pillars.map((p, i) => (
            <div key={`pillar-${i}`} className="flex items-start gap-1.5">
              <span className={`mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full ${config.dot}`} />
              <div>
                <p className="text-[11px] font-semibold text-ink">{p.pillar || ""}</p>
                {p.description && <p className="text-[10px] leading-relaxed text-ink-subtle">{p.description}</p>}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export function ContentStrategySection({ plan }) {
  const platforms = plan?.contentDirection?.platforms ?? {};
  const global = platforms?.global_editorial ?? {};
  const activePlatforms = PLATFORMS.filter((cfg) => {
    const data = platforms?.[cfg.key];
    return data && typeof data === "object";
  });

  return (
    <div className="flex flex-col gap-3">
      {(global.content_ratio || global.brief_for_creator_agent) && (
        <div className="rounded-xl border border-brand-border bg-brand-light/40 px-3 py-2.5">
          <div className="mb-1 flex items-center gap-1.5">
            <FiGlobe size={11} className="text-brand" />
            <p className="text-[10px] font-bold uppercase tracking-widest text-brand-dark">Éditorial global</p>
          </div>
          {global.content_ratio && (
            <p className="text-[11px] text-ink"><span className="font-semibold">Ratio :</span> {global.content_ratio}</p>
          )}
          {global.brief_for_creator_agent && (
            <p className="text-[11px] leading-relaxed text-ink-body mt-0.5">
              <span className="font-semibold text-brand">Brief :</span> {global.brief_for_creator_agent}
            </p>
          )}
        </div>
      )}

      {/* 3 plateformes en ligne */}
      <div className="grid grid-cols-1 gap-2 sm:grid-cols-3">
        {activePlatforms.map((cfg) => (
          <PlatformCard key={cfg.key} config={cfg} data={platforms[cfg.key]} />
        ))}
      </div>
    </div>
  );
}
