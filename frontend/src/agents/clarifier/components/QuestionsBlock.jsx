export default function QuestionsBlock({
  agentMessage,
  questions,
  answers,
  setAnswers,
  onSubmit,
  isLoading,
}) {
  const hasQuestions = Array.isArray(questions) && questions.length > 0;

  const keys = ["problem", "target", "solution"];

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
    <div
      style={{
        background: "white",
        border: "0.5px solid #AFA9EC",
        borderRadius: 14,
        overflow: "hidden",
        boxShadow: "0 2px 12px rgba(124,58,237,0.08)",
        animation: "slideUp 0.35s ease",
      }}
    >
      <div
        style={{
          padding: "8px 14px",
          borderBottom: "0.5px solid #AFA9EC",
          background: "linear-gradient(135deg,#EEEDFE,#f3f0ff)",
          display: "flex",
          alignItems: "center",
          gap: 8,
        }}
      >
        <div
          style={{
            width: 18,
            height: 18,
            borderRadius: "50%",
            background: "linear-gradient(135deg,#7F77DD,#534AB7)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            boxShadow: "0 2px 6px rgba(124,58,237,0.3)",
            fontSize: 10,
            fontWeight: 700,
            color: "white",
          }}
        >
          ?
        </div>
        <span
          style={{
            fontSize: 11,
            fontWeight: 500,
            color: "var(--color-text-secondary)",
            textTransform: "uppercase",
            letterSpacing: "0.06em",
          }}
        >
          Questions de clarification
        </span>
      </div>

      <div
        style={{
          padding: "14px",
          display: "flex",
          flexDirection: "column",
          gap: 12,
        }}
      >
        {agentMessage && (
          <p
            style={{
              fontSize: 13,
              color: "var(--color-text-primary)",
              lineHeight: 1.6,
              margin: 0,
            }}
          >
            {agentMessage}
          </p>
        )}

        {hasQuestions &&
          questions.map((question, i) => {
          const axis = getAxis(question, i) || `q${i}`;
          const key = axis;
          const text = getText(question);
          if (!text) return null;
          return (
            <div
              key={i}
              style={{
                border: "0.5px solid #AFA9EC",
                borderRadius: "var(--border-radius-md)",
                overflow: "hidden",
              }}
            >
              <div
                style={{
                  padding: "8px 12px",
                  background: "#EEEDFE",
                  fontSize: 12,
                  fontWeight: 500,
                  color: "#3C3489",
                }}
              >
                {i + 1}. {text}
              </div>
              <textarea
                value={answers[axis] || ""}
                onChange={(e) =>
                  setAnswers((prev) => ({ ...prev, [axis]: e.target.value }))
                }
                placeholder="Votre réponse..."
                rows={2}
                disabled={isLoading}
                style={{
                  width: "100%",
                  padding: "10px 12px",
                  fontSize: 13,
                  border: "none",
                  borderTop: "0.5px solid #AFA9EC",
                  outline: "none",
                  resize: "vertical",
                  fontFamily: "var(--font-sans)",
                  background: "var(--color-background-primary)",
                  color: "var(--color-text-primary)",
                  boxSizing: "border-box",
                  lineHeight: 1.5,
                  transition: "border-color 0.2s",
                }}
              />
            </div>
          );
        })}

        {hasQuestions && (
          <button
            onClick={onSubmit}
            disabled={!isValid || isLoading}
            style={{
              alignSelf: "flex-end",
              padding: "9px 20px",
              background:
                isValid && !isLoading
                  ? "#7F77DD"
                  : "var(--color-background-secondary)",
              color:
                isValid && !isLoading
                  ? "white"
                  : "var(--color-text-secondary)",
              border: "none",
              borderRadius: "var(--border-radius-md)",
              fontSize: 13,
              fontWeight: 500,
              cursor: isValid && !isLoading ? "pointer" : "not-allowed",
              transition: "all 0.2s",
            }}
          >
            {isLoading ? "Analyse en cours..." : "Envoyer mes réponses →"}
          </button>
        )}
      </div>
    </div>
  );
}

