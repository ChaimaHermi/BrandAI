export default function XaiBlock({ steps, isLoading, collapsed = false }) {
  if (!steps.length && !isLoading) return null;

  const successCount = steps.filter((step) => step.status === "success").length;
  const hasError = steps.some((step) => step.status === "error");

  const iconFor = (status) => {
    if (status === "loading") {
      return (
        <span
          style={{
            fontSize: 10,
            color: "#888780",
            animation: "pulse 1.2s infinite",
          }}
        >
          ●●●
        </span>
      );
    }
    if (status === "success") {
      return <span style={{ color: "var(--color-text-success)" }}>✓</span>;
    }
    if (status === "error") {
      return <span style={{ color: "var(--color-text-danger)" }}>✗</span>;
    }
    return <span style={{ color: "#534AB7" }}>→</span>;
  };

  return (
    <div
      style={{
        background: "var(--color-background-primary)",
        border: "0.5px solid var(--color-border-tertiary)",
        borderRadius: "var(--border-radius-lg)",
        overflow: "hidden",
        animation: "slideIn 0.3s ease",
      }}
    >
      <div
        style={{
          padding: "8px 14px",
          borderBottom: collapsed
            ? "none"
            : "0.5px solid var(--color-border-tertiary)",
          background: "var(--color-background-secondary)",
          display: "flex",
          alignItems: "center",
          gap: 8,
        }}
      >
        <div
          style={{
            width: 6,
            height: 6,
            borderRadius: "50%",
            background: hasError
              ? "var(--color-text-danger)"
              : isLoading
              ? "#EF9F27"
              : "var(--color-text-success)",
          }}
        />
        <span
          style={{
            fontSize: 11,
            fontWeight: 500,
            color: "var(--color-text-secondary)",
            textTransform: "uppercase",
            letterSpacing: "0.06em",
            flex: 1,
          }}
        >
          {isLoading ? "Agent thinking — XAI" : "Analyse — XAI"}
        </span>
        {collapsed && !isLoading && (
          <span
            style={{
              fontSize: 11,
              color: "var(--color-text-success)",
              fontFamily: "var(--font-mono)",
            }}
          >
            {successCount} étapes ✓
          </span>
        )}
      </div>

      {!collapsed && (
        <div
          style={{
            padding: "10px 14px",
            fontFamily: "var(--font-mono)",
            fontSize: 12,
            display: "flex",
            flexDirection: "column",
            gap: 4,
          }}
        >
          {steps.map((step) => (
            <div
              key={step.id}
              style={{ display: "flex", flexDirection: "column", gap: 2 }}
            >
              <div
                style={{
                  display: "flex",
                  gap: 8,
                  color:
                    step.status === "success"
                      ? "var(--color-text-success)"
                      : step.status === "error"
                      ? "var(--color-text-danger)"
                      : step.status === "loading"
                      ? "var(--color-text-secondary)"
                      : "#534AB7",
                }}
              >
                <span style={{ width: 16, flexShrink: 0 }}>
                  {iconFor(step.status)}
                </span>
                <span>
                  {step.text}
                  {step.detail?.sector && ` · ${step.detail.sector}`}
                  {step.detail?.confidence &&
                    ` · confiance ${step.detail.confidence}%`}
                  {step.detail?.model && ` · ${step.detail.model}`}
                  {step.detail?.elapsed_ms && ` · ${step.detail.elapsed_ms}ms`}
                </span>
              </div>

              {step.detail?.dimensions && (
                <div
                  style={{
                    paddingLeft: 24,
                    display: "flex",
                    gap: 12,
                    fontSize: 11,
                  }}
                >
                  {[
                    { k: "problem", l: "problème" },
                    { k: "target", l: "cible" },
                    { k: "solution", l: "solution" },
                  ].map(({ k, l }) => (
                    <span
                      key={k}
                      style={{
                        color: step.detail.dimensions[k]
                          ? "var(--color-text-success)"
                          : "var(--color-text-danger)",
                      }}
                    >
                      {step.detail.dimensions[k] ? "✓" : "✗"} {l}
                    </span>
                  ))}
                </div>
              )}

              {step.detail?.score > 0 && (
                <div
                  style={{
                    paddingLeft: 24,
                    fontSize: 11,
                    color:
                      step.detail.score >= 80
                        ? "var(--color-text-success)"
                        : "var(--color-text-warning)",
                  }}
                >
                  score : {step.detail.score}/100
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

