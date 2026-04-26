import { useState } from "react";
import { FiEdit3 } from "react-icons/fi";

export default function QuestionsBlock({
  agentMessage,
  questions,
  answers,
  setAnswers,
  onSubmit,
  isLoading,
  onRewriteIdea,
}) {
  const [submitted, setSubmitted] = useState(false);

  const hasQuestions = Array.isArray(questions) && questions.length > 0;

  const keys = ["problem", "target", "solution", "geography", "budget"];

  const getAxis = (q, i) => {
    if (typeof q === "string") return keys[i] || null;
    return q?.axis || keys[i] || null;
  };

  const getText = (q) => {
    if (typeof q === "string") return q;
    return q?.text || q?.question || "";
  };

  const requiredAxes = Array.from(
    new Set(
      questions
        .map((q, i) => getAxis(q, i))
        .filter((a) => typeof a === "string" && a.length > 0)
    )
  );

  const axesToValidate = requiredAxes;
  const asksBudget = axesToValidate.includes("budget");

  const isBudgetValid =
    Number(answers.budget_min) > 0 &&
    Number(answers.budget_max) >= Number(answers.budget_min) &&
    (answers.budget_currency || "").trim().length >= 3;
  const isAxisValid = (axis) => {
    if (axis === "budget") return isBudgetValid;
    return (answers[axis] || "").trim().length > 3;
  };
  const isValid = axesToValidate.every(isAxisValid);

  const answeredCount = axesToValidate.filter(isAxisValid).length;
  const totalCount = axesToValidate.length;

  const handleSubmit = () => {
    setSubmitted(true);
    if (!isValid) return;
    onSubmit();
  };

  if (!hasQuestions && agentMessage) {
    return (
      <div className="overflow-hidden rounded-[14px] border border-[#AFA9EC] bg-white shadow-[0_4px_20px_rgba(124,58,237,0.1)] animate-[slideUp_0.35s_ease_forwards]">
        <div className="flex items-center justify-between border-b border-[#AFA9EC] bg-gradient-to-br from-[#EEEDFE] to-[#f8f7ff] px-[18px] py-3">
          <div className="flex items-center gap-[10px]">
            <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full border-[1.5px] border-[#AFA9EC] bg-[#f8f7ff]">
              <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
                <path d="M7 3.2v4.6M7 10.1v.2" stroke="#534AB7" strokeWidth="1.5" strokeLinecap="round" />
                <circle cx="7" cy="7" r="5.2" stroke="#7F77DD" strokeWidth="1.2" />
              </svg>
            </div>
            <div>
              <div className="text-[13px] font-bold text-[#3C3489]">Ajouter une idée claire</div>
              <div className="text-[10px] font-medium text-[#7F77DD]">Merci de reformuler votre projet en quelques phrases</div>
            </div>
          </div>
          <div className="shrink-0 rounded-full border border-[#AFA9EC] bg-white px-3 py-1 text-[10px] font-bold text-[#534AB7]">
            <span className="inline-flex items-center gap-1">
              <FiEdit3 size={10} />
              Reformulation requise
            </span>
          </div>
        </div>

        <div className="flex flex-col gap-3 px-[18px] py-4">
          <div className="flex items-start gap-3">
            <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full border border-[#AFA9EC] bg-[#f8f7ff]">
              <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                <circle cx="8" cy="8" r="6" stroke="#7F77DD" strokeWidth="1.3" />
                <path d="M8 5v4M8 11v.5" stroke="#534AB7" strokeWidth="1.4" strokeLinecap="round" />
              </svg>
            </div>
            <div className="flex-1 text-[13px] leading-[1.7] text-gray-700">
              {agentMessage}
            </div>
          </div>

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

          {onRewriteIdea && (
            <button
              type="button"
              onClick={onRewriteIdea}
              className="flex w-full items-center justify-center gap-2 rounded-full bg-gradient-to-br from-[#7F77DD] to-[#534AB7] py-3 text-[13px] font-bold text-white shadow-[0_4px_14px_rgba(124,58,237,0.25)] transition-all duration-200 hover:-translate-y-[1px] hover:shadow-[0_6px_20px_rgba(124,58,237,0.35)]"
            >
              <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
                <path d="M7 2v10M2 7h10" stroke="white" strokeWidth="1.8" strokeLinecap="round" />
              </svg>
              Soumettre une nouvelle idée
            </button>
          )}
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col rounded-[14px] border border-[#AFA9EC] bg-white shadow-[0_2px_12px_rgba(124,58,237,0.08)] animate-[slideUp_0.35s_ease] overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between gap-2 border-b border-[#AFA9EC] bg-gradient-to-br from-[#EEEDFE] to-[#f3f0ff] px-[14px] py-2.5">
        <div className="flex items-center gap-2">
          <div className="flex h-[18px] w-[18px] items-center justify-center rounded-full bg-gradient-to-br from-[#7F77DD] to-[#534AB7] text-[10px] font-bold text-white shadow-[0_2px_6px_rgba(124,58,237,0.3)]">
            ?
          </div>
          <span className="text-[11px] font-medium uppercase tracking-[0.06em] text-[color:var(--color-text-secondary)]">
            Questions de clarification
          </span>
        </div>
        {/* Progress badge */}
        <div className={`flex items-center gap-1 rounded-full border px-2 py-0.5 text-[10px] font-bold ${
          totalCount > 0 && answeredCount === totalCount
            ? "border-[#9FE1CB] bg-[#f0fdf4] text-[#1D9E75]"
            : "border-[#AFA9EC] bg-white text-[#534AB7]"
        }`}>
          {answeredCount}/{totalCount} rempli{totalCount > 1 ? "es" : ""}
        </div>
      </div>

      {/* Questions area — full height on desktop, scroll only on small screens */}
      <div className="flex flex-col gap-2.5 px-[14px] pb-3 pt-[12px] overflow-y-auto max-h-[72vh] lg:max-h-none lg:overflow-visible">
        {agentMessage && (
          <div className="flex items-start gap-2 rounded-xl border border-[#e8e4ff] bg-[#f8f7ff] px-3 py-2.5">
            <div className="mt-0.5 h-[6px] w-[6px] shrink-0 rounded-full bg-[#7F77DD]" />
            <div className="min-w-0 flex-1">
              <p className="m-0 text-[13px] leading-[1.6] text-[#3C3489]">
                {agentMessage}
              </p>
              {!hasQuestions && onRewriteIdea && (
                <button
                  type="button"
                  onClick={onRewriteIdea}
                  className="mt-2 inline-flex items-center gap-1.5 rounded-full border border-[#AFA9EC] bg-white px-3 py-1 text-[11px] font-semibold text-[#534AB7] transition-colors hover:bg-[#EEEDFE]"
                >
                  Ajouter votre idée
                  <svg width="10" height="10" viewBox="0 0 12 12" fill="none">
                    <path d="M2 6h8M7 3l3 3-3 3" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
                  </svg>
                </button>
              )}
            </div>
          </div>
        )}

        {hasQuestions &&
          questions.map((question, i) => {
            const axis = getAxis(question, i) || `q${i}`;
            const text = getText(question);
            if (!text) return null;
            if (axis === "budget") return null;

            const isGeo = axis === "geography";
            const isFilled = isAxisValid(axis);
            const showError = submitted && !isFilled;

            return (
              <div
                key={i}
                className={`overflow-hidden rounded-[var(--border-radius-md,10px)] border transition-colors ${
                  showError
                    ? "border-rose-400 shadow-[0_0_0_2px_rgba(225,29,72,0.08)]"
                    : isFilled
                    ? "border-[#9FE1CB]"
                    : "border-[#AFA9EC]"
                }`}
              >
                {/* Question label */}
                <div className={`flex items-start gap-2 px-3 py-2 text-xs font-medium ${
                  isFilled ? "bg-[#f0fdf4] text-[#085041]" : "bg-[#EEEDFE] text-[#3C3489]"
                }`}>
                  <span className={`mt-px flex h-4 w-4 shrink-0 items-center justify-center rounded-full text-[10px] font-bold ${
                    isFilled ? "bg-[#1D9E75] text-white" : "bg-[#7F77DD] text-white"
                  }`}>
                    {isFilled ? "✓" : i + 1}
                  </span>
                  <span className="leading-[1.5]">
                    {isGeo && <span className="mr-1">🌍</span>}
                    {text}
                  </span>
                </div>

                {/* Answer textarea */}
                <textarea
                  value={answers[axis] || ""}
                  onChange={(e) =>
                    setAnswers((prev) => ({ ...prev, [axis]: e.target.value }))
                  }
                  placeholder={
                    isGeo
                      ? "Ex: Tunisie, France, Maroc, Algérie..."
                      : "Votre réponse (min. 4 caractères)..."
                  }
                  rows={2}
                  disabled={isLoading}
                  className={`box-border w-full resize-y border-0 border-t bg-[color:var(--color-background-primary,#fff)] px-3 py-2 font-[var(--font-sans)] text-[13px] leading-[1.5] text-[color:var(--color-text-primary,#1a1040)] transition-colors focus:outline-none focus:ring-1 ${
                    showError
                      ? "border-rose-300 focus:ring-rose-300"
                      : "border-[#AFA9EC] focus:ring-[#7F77DD]"
                  } disabled:opacity-60`}
                />

                {/* Inline error */}
                {showError && (
                  <div className="bg-rose-50 px-3 py-1.5 text-[11px] text-rose-600">
                    Cette réponse est requise (min. 4 caractères)
                  </div>
                )}
              </div>
            );
          })}

        {asksBudget && (
          <div
            className={`overflow-hidden rounded-[var(--border-radius-md,10px)] border transition-colors ${
              submitted && !isBudgetValid
                ? "border-rose-400 shadow-[0_0_0_2px_rgba(225,29,72,0.08)]"
                : isBudgetValid
                ? "border-[#9FE1CB]"
                : "border-[#AFA9EC]"
            }`}
          >
            <div
              className={`flex items-start gap-2 px-3 py-2 text-xs font-medium ${
                isBudgetValid
                  ? "bg-[#f0fdf4] text-[#085041]"
                  : "bg-[#EEEDFE] text-[#3C3489]"
              }`}
            >
              <span
                className={`mt-px flex h-4 w-4 shrink-0 items-center justify-center rounded-full text-[10px] font-bold ${
                  isBudgetValid ? "bg-[#1D9E75] text-white" : "bg-[#7F77DD] text-white"
                }`}
              >
                {isBudgetValid ? "✓" : "$"}
              </span>
              <span className="leading-[1.5]">
                Budget de départ * — Minimum / Maximum / Devise
              </span>
            </div>

            <div className="grid grid-cols-1 gap-2 border-t border-[#AFA9EC] bg-white p-2.5 sm:grid-cols-2 lg:grid-cols-3">
              <input
                type="number"
                min="0"
                step="0.01"
                value={answers.budget_min ?? ""}
                onChange={(e) =>
                  setAnswers((prev) => ({ ...prev, budget_min: e.target.value }))
                }
                disabled={isLoading}
                placeholder="Minimum"
                className="box-border w-full min-w-0 rounded-md border border-[#AFA9EC] px-3 py-2 text-[13px] focus:outline-none focus:ring-1 focus:ring-[#7F77DD]"
              />
              <input
                type="number"
                min="0"
                step="0.01"
                value={answers.budget_max ?? ""}
                onChange={(e) =>
                  setAnswers((prev) => ({ ...prev, budget_max: e.target.value }))
                }
                disabled={isLoading}
                placeholder="Maximum"
                className="box-border w-full min-w-0 rounded-md border border-[#AFA9EC] px-3 py-2 text-[13px] focus:outline-none focus:ring-1 focus:ring-[#7F77DD]"
              />
              <input
                type="text"
                maxLength={6}
                value={answers.budget_currency || ""}
                onChange={(e) =>
                  setAnswers((prev) => ({
                    ...prev,
                    budget_currency: e.target.value.toUpperCase(),
                  }))
                }
                disabled={isLoading}
                placeholder="Devise (ex: EUR)"
                className="box-border w-full min-w-0 rounded-md border border-[#AFA9EC] px-3 py-2 text-[13px] uppercase focus:outline-none focus:ring-1 focus:ring-[#7F77DD]"
              />
            </div>
            {submitted && !isBudgetValid && (
              <div className="bg-rose-50 px-3 py-1.5 text-[11px] text-rose-600">
                Budget requis: minimum &gt; 0, maximum ≥ minimum, devise requise (ex: EUR).
              </div>
            )}
          </div>
        )}
      </div>

      {/* Submit button — always pinned at bottom */}
      {hasQuestions && (
        <div className="border-t border-[#AFA9EC] bg-white px-[14px] py-3">
          <button
            onClick={handleSubmit}
            disabled={isLoading}
            className={`flex w-full items-center justify-center gap-2 rounded-[var(--border-radius-md,10px)] border-0 px-5 py-[10px] text-[13px] font-semibold transition-all ${
              isValid && !isLoading
                ? "cursor-pointer bg-gradient-to-br from-[#7F77DD] to-[#534AB7] text-white shadow-[0_2px_8px_rgba(124,58,237,0.25)] hover:-translate-y-px hover:shadow-[0_4px_12px_rgba(124,58,237,0.35)]"
                : isLoading
                ? "cursor-wait bg-[#7F77DD] text-white opacity-70"
                : "cursor-pointer bg-[color:var(--color-background-secondary,#f3f0ff)] text-[#534AB7]"
            }`}
          >
            {isLoading ? (
              <>
                <span className="inline-block h-3.5 w-3.5 animate-spin rounded-full border-2 border-white border-t-transparent" />
                Analyse en cours...
              </>
            ) : (
              <>
                Envoyer mes réponses
                <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
                  <path d="M2 6h8M7 3l3 3-3 3" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" />
                </svg>
              </>
            )}
          </button>
        </div>
      )}
    </div>
  );
}
