import {
  FiTarget, FiZap, FiStar, FiMessageSquare,
  FiAlertCircle, FiHeart, FiTag, FiXCircle, FiUser, FiCompass,
} from "react-icons/fi";

function Block({ icon: Icon, color, title, children }) {
  return (
    <div className="rounded-xl border border-[color:var(--color-border,#ebebf5)] bg-white shadow-sm">
      <div className={`flex items-center gap-2 border-b border-[color:var(--color-border,#ebebf5)] px-3 py-2 ${color}`}>
        <Icon size={12} />
        <p className="text-[11px] font-bold uppercase tracking-widest">{title}</p>
      </div>
      <div className="flex flex-col gap-2.5 px-3 py-3">{children}</div>
    </div>
  );
}

function Field({ label, value }) {
  if (!value) return null;
  return (
    <div>
      <p className="mb-0.5 text-[10px] font-bold uppercase tracking-widest text-ink-subtle">{label}</p>
      <p className="text-[12px] leading-relaxed text-ink">{value}</p>
    </div>
  );
}

function ChipList({ items, chipClass }) {
  if (!Array.isArray(items) || items.length === 0) return null;
  return (
    <div className="flex flex-wrap gap-1.5">
      {items.map((item, idx) => (
        <span key={`${item}-${idx}`} className={`rounded-full border px-2 py-0.5 text-[11px] font-semibold ${chipClass}`}>
          {item}
        </span>
      ))}
    </div>
  );
}

export function PositioningSection({ plan }) {
  const p = plan?.positioning ?? {};
  const m = plan?.messaging   ?? {};
  const t = plan?.targeting   ?? {};

  return (
    <div className="flex flex-col gap-3">

      {/* Positionnement */}
      <Block icon={FiTarget} color="text-brand" title="Positionnement">
        <div className="grid gap-2 sm:grid-cols-2">
          <Field label="Segment cible" value={p.target_segment} />
          <Field label="Différenciation" value={p.differentiation} />
        </div>
        <Field label="Proposition de valeur" value={p.value_proposition} />
        {p.tagline_suggestion && (
          <div className="flex items-center gap-2 rounded-lg border border-brand/20 bg-brand-light/50 px-3 py-2">
            <FiTag size={11} className="shrink-0 text-brand" />
            <p className="text-[12px] font-semibold text-brand-darker">"{p.tagline_suggestion}"</p>
          </div>
        )}
      </Block>

      {/* Cibles */}
      <Block icon={FiUser} color="text-amber-500" title="Cibles & Persona">
        <div className="grid gap-2 sm:grid-cols-2">
          <Field label="Persona principal" value={t.primary_persona} />
          <div>
            <p className="mb-0.5 flex items-center gap-1 text-[10px] font-bold uppercase tracking-widest text-ink-subtle">
              <FiCompass size={9} /> Focus segment
            </p>
            <p className="text-[12px] leading-relaxed text-ink">{t.market_segment_focus || ""}</p>
          </div>
        </div>
      </Block>

      {/* Message */}
      <Block icon={FiMessageSquare} color="text-ink-muted" title="Message marketing">
        {m.main_message && (
          <div className="rounded-lg border-l-4 border-l-brand bg-brand-light/30 px-3 py-2">
            <p className="text-[12px] font-semibold leading-relaxed text-ink">{m.main_message}</p>
          </div>
        )}
        <div className="grid gap-2 sm:grid-cols-2">
          {m.pain_point_focus && (
            <div className="flex items-start gap-1.5 rounded-lg border border-red-100 bg-red-50/60 px-2.5 py-2">
              <FiAlertCircle size={11} className="mt-0.5 shrink-0 text-red-400" />
              <div>
                <p className="mb-0.5 text-[10px] font-bold uppercase tracking-widest text-red-400">Pain point</p>
                <p className="text-[11px] leading-relaxed text-red-700">{m.pain_point_focus}</p>
              </div>
            </div>
          )}
          {m.emotional_hook && (
            <div className="flex items-start gap-1.5 rounded-lg border border-success-border bg-success-light/60 px-2.5 py-2">
              <FiHeart size={11} className="mt-0.5 shrink-0 text-success" />
              <div>
                <p className="mb-0.5 text-[10px] font-bold uppercase tracking-widest text-success/70">Accroche</p>
                <p className="text-[11px] leading-relaxed text-success-dark">{m.emotional_hook}</p>
              </div>
            </div>
          )}
        </div>
        <div className="grid gap-2 sm:grid-cols-2">
          <div>
            <p className="mb-1.5 flex items-center gap-1 text-[10px] font-bold text-success">
              <FiStar size={9} /> Mots à utiliser
            </p>
            <ChipList items={m.vocabulary_to_use} chipClass="border-success-border bg-success-light text-success-dark" />
          </div>
          <div>
            <p className="mb-1.5 flex items-center gap-1 text-[10px] font-bold text-red-500">
              <FiXCircle size={9} /> Mots à éviter
            </p>
            <ChipList items={m.vocabulary_to_avoid} chipClass="border-red-100 bg-red-50 text-red-600" />
          </div>
        </div>
      </Block>

    </div>
  );
}
