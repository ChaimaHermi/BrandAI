import {
  FiTarget, FiZap, FiStar, FiMessageSquare,
  FiAlertCircle, FiHeart, FiTag, FiXCircle,
} from "react-icons/fi";

function InfoCard({ icon: Icon, iconClass, borderClass, bgClass, label, children }) {
  return (
    <div className={`rounded-2xl border ${borderClass} ${bgClass} p-4 shadow-card`}>
      <div className="mb-2 flex items-center gap-2">
        <span className={`flex h-7 w-7 items-center justify-center rounded-lg ${iconClass}`}>
          <Icon size={13} />
        </span>
        <p className="text-xs font-bold uppercase tracking-wide text-ink-muted">{label}</p>
      </div>
      {children}
    </div>
  );
}

function ChipList({ items, chipClass }) {
  if (!Array.isArray(items) || items.length === 0)
    return <p className="text-sm text-ink-subtle">N'existe pas</p>;
  return (
    <div className="flex flex-wrap gap-1.5">
      {items.map((item, idx) => (
        <span
          key={`${item}-${idx}`}
          className={`rounded-full border px-2.5 py-1 text-[11px] font-semibold ${chipClass}`}
        >
          {item}
        </span>
      ))}
    </div>
  );
}

function TextBlock({ value }) {
  return <p className="text-[13px] leading-relaxed text-ink">{value || "N'existe pas"}</p>;
}

export function PositioningSection({ plan }) {
  const p = plan?.positioning ?? {};
  const m = plan?.messaging   ?? {};

  return (
    <div className="flex flex-col gap-4">

      {/* Row 1 — Segment + Différenciation */}
      <div className="grid gap-4 md:grid-cols-2">
        <InfoCard
          icon={FiTarget}
          iconClass="bg-brand-light text-brand"
          borderClass="border-brand-border"
          bgClass="bg-white"
          label="Segment cible"
        >
          <TextBlock value={p.target_segment} />
        </InfoCard>

        <InfoCard
          icon={FiZap}
          iconClass="bg-amber-50 text-amber-500"
          borderClass="border-amber-200"
          bgClass="bg-white"
          label="Différenciation"
        >
          <TextBlock value={p.differentiation} />
        </InfoCard>
      </div>

      {/* Row 2 — Value prop (quote style) */}
      <div className="relative overflow-hidden rounded-2xl border border-purple-200 bg-white p-4 shadow-card">
        <span className="pointer-events-none absolute -top-2 -left-1 select-none text-7xl font-serif leading-none text-purple-100">"</span>
        <div className="relative">
          <div className="mb-2 flex items-center gap-2">
            <span className="flex h-7 w-7 items-center justify-center rounded-lg bg-purple-50 text-purple-600">
              <FiStar size={13} />
            </span>
            <p className="text-xs font-bold uppercase tracking-wide text-ink-muted">Proposition de valeur</p>
          </div>
          <p className="pl-1 text-[13px] font-medium leading-relaxed text-ink">{p.value_proposition || "N'existe pas"}</p>
        </div>
      </div>

      {/* Tagline — highlight banner */}
      {p.tagline_suggestion && (
        <div className="flex items-center gap-3 rounded-2xl border border-brand/30 bg-gradient-to-r from-brand-light to-[#f3f0ff] px-5 py-4">
          <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-gradient-to-br from-brand to-brand-dark text-white shadow-pill">
            <FiTag size={14} />
          </span>
          <div>
            <p className="text-[10px] font-bold uppercase tracking-widest text-brand-muted">
              Tagline suggérée
            </p>
            <p className="mt-0.5 text-sm font-bold text-brand-darker">
              "{p.tagline_suggestion}"
            </p>
          </div>
        </div>
      )}

      {/* Message principal */}
      <div className="rounded-2xl border border-brand-border bg-white p-5 shadow-card">
        <div className="mb-3 flex items-center gap-2">
          <span className="flex h-7 w-7 items-center justify-center rounded-lg bg-ink/5">
            <FiMessageSquare size={13} className="text-ink-muted" />
          </span>
          <p className="text-xs font-bold uppercase tracking-wide text-ink-muted">Message principal</p>
        </div>
        <div className="mb-4 rounded-xl border-l-4 border-l-brand bg-brand-light/40 px-4 py-3">
          <p className="text-[13px] font-semibold leading-relaxed text-ink">{m.main_message || "N'existe pas"}</p>
        </div>

        <div className="grid gap-3 sm:grid-cols-2">
          <div className="flex items-start gap-2 rounded-xl border border-red-100 bg-red-50 p-3">
            <FiAlertCircle size={13} className="mt-0.5 shrink-0 text-red-500" />
            <div>
              <p className="mb-1 text-[10px] font-bold uppercase tracking-wide text-red-400">
                Pain point focus
              </p>
              <p className="text-xs leading-relaxed text-red-700">{m.pain_point_focus || "N'existe pas"}</p>
            </div>
          </div>
          <div className="flex items-start gap-2 rounded-xl border border-success-border bg-success-light p-3">
            <FiHeart size={13} className="mt-0.5 shrink-0 text-success" />
            <div>
              <p className="mb-1 text-[10px] font-bold uppercase tracking-wide text-success/60">
                Accroche émotionnelle
              </p>
              <p className="text-xs leading-relaxed text-success-dark">{m.emotional_hook || "N'existe pas"}</p>
            </div>
          </div>
        </div>

        {/* Vocab */}
        <div className="mt-4 grid gap-3 sm:grid-cols-2">
          <div>
            <p className="mb-2 flex items-center gap-1.5 text-[11px] font-bold text-success">
              <FiStar size={10} /> Vocabulaire à utiliser
            </p>
            <ChipList
              items={m.vocabulary_to_use}
              chipClass="border-success-border bg-success-light text-success-dark"
            />
          </div>
          <div>
            <p className="mb-2 flex items-center gap-1.5 text-[11px] font-bold text-red-500">
              <FiXCircle size={10} /> Vocabulaire à éviter
            </p>
            <ChipList
              items={m.vocabulary_to_avoid}
              chipClass="border-red-100 bg-red-50 text-red-600"
            />
          </div>
        </div>
      </div>
    </div>
  );
}
