function Row({ label, value, fallback = "—" }) {
  const display =
    value != null && String(value).trim() !== ""
      ? String(value).trim()
      : null;
  return (
    <div className="border-b border-brand-light py-3 last:border-b-0 last:pb-0">
      <dt className="text-2xs font-bold uppercase tracking-wide text-brand">
        {label}
      </dt>
      <dd className="mt-1 text-sm font-semibold leading-snug text-ink">
        {display ?? fallback}
      </dd>
    </div>
  );
}

/**
 * @param {object}  props
 * @param {object}  props.idea
 * @param {boolean} [props.embedded] — sans bandeau d'étape (utilisé avec SectionHeader parent)
 */
export default function AboutProjectCard({ idea, embedded = false }) {
  if (!idea?.id) {
    return (
      <div className="bi-card text-sm text-ink-muted">
        Chargement de l&apos;idée…
      </div>
    );
  }

  const sector  = idea.clarity_sector || idea.sector;
  const target  = idea.clarity_target_users || idea.target_audience;
  const problem = idea.clarity_problem;

  const body = (
    <>
      {!embedded && (
        <div className="mb-4">
          <h2 className="text-sm font-bold text-ink">À propos de votre projet</h2>
          <p className="mt-0.5 text-xs text-ink-subtle">
            Pré-rempli depuis votre idée clarifiée
          </p>
        </div>
      )}

      <dl>
        <Row label="Secteur"        value={sector}  />
        <Row label="Public cible"   value={target}  />
        <Row label="Problème résolu" value={problem} />
      </dl>

      {(idea.clarity_short_pitch || idea.clarity_solution) && (
        <dl className="mt-2 border-t border-brand-light pt-3">
          {idea.clarity_short_pitch && (
            <Row label="Pitch court" value={idea.clarity_short_pitch} />
          )}
          {idea.clarity_solution && (
            <Row label="Solution" value={idea.clarity_solution} />
          )}
        </dl>
      )}

      {(idea.clarity_country || idea.clarity_language) && (
        <div className="mt-3 flex flex-wrap items-center gap-2">
          {idea.clarity_country && (
            <div className="flex items-center gap-2 rounded-xl border border-[#bfdbfe] bg-[#eff6ff] px-3 py-2">
              <span className="text-base leading-none">🌍</span>
              <div>
                <div className="text-[9px] font-bold uppercase tracking-[0.08em] text-[#1d4ed8]">
                  Zone géographique
                </div>
                <div className="flex items-center gap-1.5">
                  <span className="text-xs font-bold text-[#1e3a8a]">{idea.clarity_country}</span>
                  {idea.clarity_country_code && (
                    <span className="rounded border border-[#93c5fd] bg-white px-1 py-px font-mono text-[9px] font-bold text-[#2563eb]">
                      {idea.clarity_country_code}
                    </span>
                  )}
                </div>
              </div>
            </div>
          )}
          {idea.clarity_language && (
            <div className="rounded-xl border border-brand-border bg-brand-light px-3 py-2">
              <div className="text-[9px] font-bold uppercase tracking-[0.08em] text-brand">Langue</div>
              <div className="text-xs font-bold text-brand-darker">{idea.clarity_language}</div>
            </div>
          )}
        </div>
      )}
    </>
  );

  if (embedded) {
    return <div className="bi-card bi-fade-up">{body}</div>;
  }

  return (
    <section className="rounded-xl border border-brand-border bg-white p-5 shadow-card">
      {body}
    </section>
  );
}
