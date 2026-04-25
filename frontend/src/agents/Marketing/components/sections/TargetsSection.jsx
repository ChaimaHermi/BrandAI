import { FiUser, FiCompass, FiAward } from "react-icons/fi";

export function TargetsSection({ plan }) {
  const t = plan?.targeting ?? {};

  return (
    <div className="flex flex-col gap-4">

      {/* Primary persona — hero card */}
      {t.primary_persona && (
        <div className="overflow-hidden rounded-2xl border border-brand-border bg-gradient-to-br from-brand-light to-[#f3f0ff] shadow-card">
          <div className="px-5 py-4">
            <div className="mb-1 flex items-center gap-1.5">
              <FiUser size={12} className="text-brand" />
              <p className="text-[10px] font-extrabold uppercase tracking-widest text-brand">
                Persona principal
              </p>
            </div>
            <p className="mt-1 text-sm font-semibold leading-relaxed text-ink">
              {t.primary_persona}
            </p>
          </div>
        </div>
      )}

      {/* Segment focus */}
      {t.market_segment_focus && (
        <div className="flex items-start gap-3 rounded-2xl border border-amber-200 bg-amber-50 px-5 py-4 shadow-card">
          <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-xl bg-amber-100">
            <FiCompass size={14} className="text-amber-600" />
          </span>
          <div>
            <p className="mb-0.5 text-[10px] font-extrabold uppercase tracking-widest text-amber-500">
              Focus segment
            </p>
            <p className="text-[13px] leading-relaxed text-ink">{t.market_segment_focus}</p>
          </div>
        </div>
      )}

      {/* Empty fallback */}
      {!t.primary_persona && !t.market_segment_focus && (
        <p className="text-sm text-ink-subtle">N'existe pas</p>
      )}
    </div>
  );
}
