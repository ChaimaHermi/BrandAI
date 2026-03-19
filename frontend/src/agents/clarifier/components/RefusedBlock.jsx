import { useNavigate } from "react-router-dom";

export default function RefusedBlock({ data }) {
  const navigate = useNavigate();
  if (!data) return null;

  const categoryLabels = {
    fraud: "Fraude · fraud",
    illegal: "Activité illégale · illegal",
    harmful: "Contenu nuisible · harmful",
    default: "Non conforme · default",
  };

  const categoryLabel =
    categoryLabels[data.reason_category] || categoryLabels.default;

  const refusalText =
    (data.message || data.refusal_message || "").trim() ||
    "BrandAI ne peut pas vous accompagner dans ce type de projet.";

  return (
    <div className="overflow-hidden rounded-[14px] border border-[#fecaca] bg-white shadow-[0_4px_20px_rgba(225,29,72,0.08)] animate-[slideUp_0.35s_ease_forwards]">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-[#fecaca] bg-gradient-to-br from-[#fff5f5] to-[#fff8f8] px-[18px] py-3">
        <div className="flex items-center gap-[10px]">
          <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full border-[1.5px] border-[#fecaca] bg-[#fff5f5]">
            <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
              <path
                d="M3 3l8 8M11 3l-8 8"
                stroke="#e11d48"
                strokeWidth="1.6"
                strokeLinecap="round"
              />
            </svg>
          </div>
          <div>
            <div className="text-[13px] font-bold text-rose-600">
              Projet non conforme
            </div>
            <div className="text-[10px] font-medium text-rose-400">
              Catégorie : {categoryLabel}
            </div>
          </div>
        </div>

        {/* Badge pipeline bloqué */}
        <div className="shrink-0 rounded-full border border-[#fecaca] bg-[#fff5f5] px-3 py-1 text-[10px] font-bold text-rose-600">
          🔒 Pipeline bloqué
        </div>
      </div>

      <div className="flex flex-col gap-3 px-[18px] py-4">
        {/* Message LLM */}
        <div className="flex items-start gap-3">
          <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full border border-[#fecaca] bg-[#fff5f5]">
            <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
              <circle cx="8" cy="8" r="6" stroke="#e11d48" strokeWidth="1.3" />
              <path
                d="M8 5v4M8 11v.5"
                stroke="#e11d48"
                strokeWidth="1.4"
                strokeLinecap="round"
              />
            </svg>
          </div>
          <div className="flex-1 text-[13px] leading-[1.7] text-gray-700">
            {refusalText}
          </div>
        </div>

        {/* Ce que BrandAI peut faire */}
        <div className="rounded-[10px] border border-[#e8e4ff] bg-[#f8f7ff] px-[14px] py-3">
          <div className="mb-2 text-[10px] font-bold uppercase tracking-[0.07em] text-[#7F77DD]">
            BrandAI peut vous accompagner pour
          </div>
          <div className="flex flex-col gap-1">
            {[
              "Des projets tech, éducation, ecommerce, santé",
              "Des startups et idées innovantes légales",
              "Des marques, produits et services éthiques",
            ].map((item, i) => (
              <div key={i} className="flex gap-1.5 text-xs text-[#534AB7]">
                <span className="shrink-0">→</span>
                {item}
              </div>
            ))}
          </div>
        </div>

        {/* Bouton nouvelle idée */}
        <button
          onClick={() => navigate("/ideas/new")}
          className="flex w-full items-center justify-center gap-2 rounded-full bg-gradient-to-br from-[#7F77DD] to-[#534AB7] py-3 text-[13px] font-bold text-white shadow-[0_4px_14px_rgba(124,58,237,0.25)] transition-all duration-200 hover:-translate-y-[1px] hover:shadow-[0_6px_20px_rgba(124,58,237,0.35)]"
        >
          <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
            <path
              d="M7 2v10M2 7h10"
              stroke="white"
              strokeWidth="1.8"
              strokeLinecap="round"
            />
          </svg>
          Soumettre une nouvelle idée
        </button>
      </div>
    </div>
  );
}

