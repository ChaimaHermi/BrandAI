import { useState } from "react";
import { FiFacebook, FiInstagram, FiLinkedin, FiGlobe, FiClock, FiMessageSquare, FiArrowRight } from "react-icons/fi";

const PLATFORMS = [
  {
    key: "facebook",
    label: "Facebook",
    icon: FiFacebook,
    accent: "#1877F2",
    bg: "bg-blue-50",
    border: "border-blue-200",
    pill: "bg-blue-100 text-blue-700",
    dot: "bg-blue-500",
    headerBg: "bg-gradient-to-r from-blue-50 to-blue-100",
  },
  {
    key: "instagram",
    label: "Instagram",
    icon: FiInstagram,
    accent: "#E1306C",
    bg: "bg-pink-50",
    border: "border-pink-200",
    pill: "bg-pink-100 text-pink-700",
    dot: "bg-pink-500",
    headerBg: "bg-gradient-to-r from-pink-50 to-rose-50",
  },
  {
    key: "linkedin",
    label: "LinkedIn",
    icon: FiLinkedin,
    accent: "#0A66C2",
    bg: "bg-sky-50",
    border: "border-sky-200",
    pill: "bg-sky-100 text-sky-700",
    dot: "bg-sky-600",
    headerBg: "bg-gradient-to-r from-sky-50 to-sky-100",
  },
];

function FormatChip({ label, pillClass }) {
  return (
    <span className={`inline-block rounded-full px-2 py-0.5 text-[11px] font-semibold ${pillClass}`}>
      {label}
    </span>
  );
}

function PillarCard({ pillar, pillClass, dotClass }) {
  const formats = Array.isArray(pillar.formats) ? pillar.formats : [];
  return (
    <div className="rounded-xl border border-[color:var(--color-border,#ebebf5)] bg-white p-3.5 shadow-sm">
      <div className="mb-2 flex items-start justify-between gap-2">
        <div className="flex items-center gap-1.5">
          <span className={`h-2 w-2 shrink-0 rounded-full ${dotClass}`} />
          <p className="text-[13px] font-bold text-ink">{pillar.pillar || "N'existe pas"}</p>
        </div>
        {pillar.frequency && (
          <span className="flex items-center gap-1 text-[11px] text-ink-subtle">
            <FiClock size={10} />
            {pillar.frequency}
          </span>
        )}
      </div>
      {pillar.description && (
        <p className="mb-2 text-xs leading-relaxed text-ink-body">{pillar.description}</p>
      )}
      {formats.length > 0 && (
        <div className="flex flex-wrap gap-1">
          {formats.map((f, i) => (
            <FormatChip key={`${f}-${i}`} label={f} pillClass={pillClass} />
          ))}
        </div>
      )}
    </div>
  );
}

function PlatformCard({ config, data }) {
  const [open, setOpen] = useState(true);
  const Icon = config.icon;
  const pillars = Array.isArray(data?.content_pillars) ? data.content_pillars : [];

  return (
    <div className={`overflow-hidden rounded-2xl border ${config.border} shadow-card`}>
      {/* Header */}
      <button
        type="button"
        onClick={() => setOpen((o) => !o)}
        className={`flex w-full items-center gap-3 px-4 py-3 text-left ${config.headerBg} transition-colors`}
      >
        <span className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-xl ${config.bg} ${config.border} border`}>
          <Icon size={15} style={{ color: config.accent }} />
        </span>
        <div className="min-w-0 flex-1">
          <p className="text-sm font-bold text-ink">{config.label}</p>
          {data?.role && (
            <p className="truncate text-[11px] text-ink-subtle">{data.role}</p>
          )}
        </div>
        <span className={`text-[11px] font-semibold ${config.dot.replace("bg-", "text-")} mr-1`}>
          {pillars.length} pilier{pillars.length > 1 ? "s" : ""}
        </span>
        <FiArrowRight
          size={12}
          className={`shrink-0 text-ink-subtle transition-transform ${open ? "rotate-90" : ""}`}
        />
      </button>

      {open && (
        <div className="bg-white p-4">
          {/* Pillars grid */}
          {pillars.length > 0 ? (
            <div className="mb-4 grid gap-2 sm:grid-cols-2">
              {pillars.map((p, i) => (
                <PillarCard
                  key={`pillar-${i}`}
                  pillar={p}
                  pillClass={config.pill}
                  dotClass={config.dot}
                />
              ))}
            </div>
          ) : (
            <p className="mb-3 text-sm text-ink-subtle">N'existe pas</p>
          )}

          {/* Tone + CTA row */}
          <div className="flex flex-wrap gap-2">
            {data?.tone && (
              <div className={`flex items-center gap-1.5 rounded-lg border ${config.border} ${config.bg} px-3 py-1.5`}>
                <FiMessageSquare size={12} style={{ color: config.accent }} />
                <span className="text-[12px] font-medium text-ink-body">
                  Ton : <span className="font-semibold text-ink">{data.tone}</span>
                </span>
              </div>
            )}
            {data?.cta_direction && (
              <div className={`flex items-center gap-1.5 rounded-lg border ${config.border} ${config.bg} px-3 py-1.5`}>
                <FiArrowRight size={12} style={{ color: config.accent }} />
                <span className="text-[12px] font-medium text-ink-body">
                  CTA : <span className="font-semibold text-ink">{data.cta_direction}</span>
                </span>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

export function ContentStrategySection({ plan }) {
  const platforms = plan?.contentDirection?.platforms ?? {};
  const global = platforms?.global_editorial ?? {};

  return (
    <div className="flex flex-col gap-5">
      {/* Global editorial banner */}
      {(global.content_ratio || global.brief_for_creator_agent) && (
        <div className="flex flex-wrap gap-3 rounded-2xl border border-brand-border bg-gradient-to-br from-brand-light to-[#f3f0ff] px-5 py-4 shadow-card">
          <div className="flex items-center gap-2">
            <FiGlobe size={14} className="text-brand" />
            <p className="text-xs font-bold uppercase tracking-wide text-brand-dark">Éditorial global</p>
          </div>
          <div className="flex flex-wrap gap-4 text-[13px] text-ink">
            {global.content_ratio && (
              <span>
                <span className="font-semibold">Ratio :</span>{" "}
                {global.content_ratio}
              </span>
            )}
          </div>
          {global.brief_for_creator_agent && (
            <p className="w-full text-[12px] leading-relaxed text-ink-body">
              <span className="font-semibold text-brand">Brief Content Agent :</span>{" "}
              {global.brief_for_creator_agent}
            </p>
          )}
        </div>
      )}

      {/* Platform cards */}
      <div className="flex flex-col gap-3">
        {PLATFORMS.map((cfg) => (
          <PlatformCard
            key={cfg.key}
            config={cfg}
            data={platforms[cfg.key]}
          />
        ))}
      </div>
    </div>
  );
}
