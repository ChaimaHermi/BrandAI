export default function QuestionsBlock({
  agentMessage,
  questions,
  answers,
  setAnswers,
  onSubmit,
  isLoading,
}) {
  const hasQuestions = Array.isArray(questions) && questions.length > 0;

  const keys = ["problem", "target", "solution", "geography"];

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

  const axesToValidate = requiredAxes.length ? requiredAxes : keys;
  const isValid = axesToValidate.every(
    (axis) => answers[axis]?.trim().length > 3
  );

  return (
    <div className="flex flex-col overflow-hidden rounded-[14px] border border-[#AFA9EC] bg-white shadow-[0_2px_12px_rgba(124,58,237,0.08)] animate-[slideUp_0.35s_ease]">
      <div className="flex items-center gap-2 border-b border-[#AFA9EC] bg-gradient-to-br from-[#EEEDFE] to-[#f3f0ff] px-[14px] py-2">
        <div className="flex h-[18px] w-[18px] items-center justify-center rounded-full bg-gradient-to-br from-[#7F77DD] to-[#534AB7] text-[10px] font-bold text-white shadow-[0_2px_6px_rgba(124,58,237,0.3)]">
          ?
        </div>
        <span className="text-[11px] font-medium uppercase tracking-[0.06em] text-[color:var(--color-text-secondary)]">
          Questions de clarification
        </span>
      </div>

      {/* Scrollable questions area */}
      <div className="flex flex-col gap-3 overflow-y-auto p-[14px]">
        {agentMessage && (
          <p className="m-0 text-[13px] leading-[1.6] text-[color:var(--color-text-primary)]">
            {agentMessage}
          </p>
        )}

        {hasQuestions &&
          questions.map((question, i) => {
          const axis = getAxis(question, i) || `q${i}`;
          const text = getText(question);
          if (!text) return null;
          const isGeo = axis === "geography";
          return (
            <div
              key={i}
              className="overflow-hidden rounded-[var(--border-radius-md)] border border-[#AFA9EC]"
            >
              <div className="bg-[#EEEDFE] px-3 py-2 text-xs font-medium text-[#3C3489]">
                {i + 1}. {isGeo ? "🌍 " : ""}{text}
              </div>
              <textarea
                value={answers[axis] || ""}
                onChange={(e) =>
                  setAnswers((prev) => ({ ...prev, [axis]: e.target.value }))
                }
                placeholder={
                  isGeo
                    ? "Ex: Tunisie, France, Maroc, Algérie..."
                    : "Votre réponse..."
                }
                rows={2}
                disabled={isLoading}
                className="box-border w-full resize-y border-0 border-t border-[#AFA9EC] bg-[color:var(--color-background-primary)] px-3 py-[10px] font-[var(--font-sans)] text-[13px] leading-[1.5] text-[color:var(--color-text-primary)] outline-none transition-colors"
              />
            </div>
          );
        })}
      </div>

      {/* Button pinned at the bottom — always visible */}
      {hasQuestions && (
        <div className="border-t border-[#AFA9EC] bg-white px-[14px] py-3">
          <button
            onClick={onSubmit}
            disabled={!isValid || isLoading}
            className={`w-full rounded-[var(--border-radius-md)] border-0 px-5 py-[10px] text-[13px] font-medium transition-all ${
              isValid && !isLoading
                ? "cursor-pointer bg-[#7F77DD] text-white"
                : "cursor-not-allowed bg-[color:var(--color-background-secondary)] text-[color:var(--color-text-secondary)]"
            }`}
          >
            {isLoading ? "Analyse en cours..." : "Envoyer mes réponses →"}
          </button>
        </div>
      )}
    </div>
  );
}

