import { Link } from "react-router-dom";

function Row({ label, value, fallback = "—" }) {
  const display =
    value != null && String(value).trim() !== ""
      ? String(value).trim()
      : null;
  return (
    <div className="border-b border-[#f3f4f6] py-3 last:border-b-0 last:pb-0">
      <dt className="text-[10px] font-bold uppercase tracking-wide text-[#6366f1]">
        {label}
      </dt>
      <dd className="mt-1 text-[13px] font-semibold leading-snug text-[#111827]">
        {display ?? fallback}
      </dd>
    </div>
  );
}

/**
 * @param {object} props
 * @param {object} props.idea
 * @param {boolean} [props.embedded] — sans bandeau d’étape (utilisé avec SectionHeader parent)
 */
export default function AboutProjectCard({ idea, embedded = false }) {
  if (!idea?.id) {
    return (
      <div className="bi-card text-[13px] text-[#6b7280]">
        Chargement de l&apos;idée…
      </div>
    );
  }

  const sector = idea.clarity_sector || idea.sector;
  const target = idea.clarity_target_users || idea.target_audience;
  const problem = idea.clarity_problem;

  const body = (
    <>
      {!embedded && (
        <div className="mb-4">
          <h2 className="text-[15px] font-bold text-[#111827]">
            À propos de votre projet
          </h2>
          <p className="mt-0.5 text-[11px] text-[#9ca3af]">
            Pré-rempli depuis votre idée clarifiée
          </p>
        </div>
      )}

      <dl>
        <Row label="Secteur" value={sector} />
        <Row label="Public cible" value={target} />
        <Row label="Problème résolu" value={problem} />
      </dl>

      {(idea.clarity_short_pitch || idea.clarity_solution) && (
        <dl className="mt-2 border-t border-[#f3f4f6] pt-3">
          {idea.clarity_short_pitch && (
            <Row label="Pitch court" value={idea.clarity_short_pitch} />
          )}
          {idea.clarity_solution && (
            <Row label="Solution" value={idea.clarity_solution} />
          )}
        </dl>
      )}

      <div className="mt-4 flex flex-wrap items-center gap-2 text-[11px] text-[#6b7280]">
        {[
          idea.clarity_country,
          idea.clarity_country_code ? `(${idea.clarity_country_code})` : null,
        ]
          .filter(Boolean)
          .join(" ")}
        {idea.clarity_language && (
          <span className="text-[#9ca3af]">
            {" "}
            · langue {idea.clarity_language}
          </span>
        )}
      </div>

      <Link
        to={`/ideas/${idea.id}/clarifier`}
        className="mt-4 inline-flex text-[12px] font-semibold text-[#6366f1] underline decoration-[#c7d2fe] underline-offset-2 hover:text-[#4f46e5]"
      >
        Modifier dans l&apos;Idea Clarifier
      </Link>
    </>
  );

  if (embedded) {
    return <div className="bi-card bi-fade-up">{body}</div>;
  }

  return (
    <section className="rounded-xl border border-[#e5e7eb] bg-white p-5 shadow-sm">
      {body}
    </section>
  );
}
