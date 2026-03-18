import { useState, useEffect } from "react";

export default function XaiBlock({ steps, isLoading, collapsed }) {
  const [isOpen, setIsOpen] = useState(!collapsed);

  // Si le parent change collapsed (ex: quand clarified), on synchronise l'état local
  useEffect(() => {
    setIsOpen(!collapsed);
  }, [collapsed]);

  const shouldRender = steps.length > 0 || isLoading;
  if (!shouldRender) return null;

  const effectiveCollapsed = !isOpen;

  const successCount = steps.filter((s) => s.status === "success").length;
  const hasError = steps.some((s) => s.status === "error");

  const dimStep = steps.find((s) => s.detail?.dimensions);
  const dims = dimStep?.detail?.dimensions || null;

  const secStep = steps.find((s) => s.detail?.sector);
  const sector = secStep?.detail?.sector || null;

  const scoreStep = steps.find((s) => s.detail?.score && s.detail.score > 0);
  const finalScore = scoreStep?.detail?.score || null;

  const modelStep = steps.find((s) => s.detail?.model);
  const model = modelStep?.detail?.model || null;

  return (
    <div
      style={{
        background: "white",
        border: "0.5px solid #9FE1CB",
        borderRadius: 14,
        overflow: "visible",
        boxShadow: "0 2px 8px rgba(29,158,117,0.08)",
        animation: "slideUp 0.35s ease forwards",
      }}
    >
      {/* Header */}
      <div
        style={{
          padding: "10px 16px",
          background: "#f0fdf4",
          borderBottom: collapsed ? "none" : "0.5px solid #9FE1CB",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <div
            style={{
              width: 7,
              height: 7,
              borderRadius: "50%",
              background: hasError ? "#e11d48" : isLoading ? "#EF9F27" : "#1D9E75",
              animation: isLoading ? "pulse 1.2s infinite" : "none",
            }}
          />
          <span
            style={{
              fontSize: 11,
              fontWeight: 700,
              color: hasError ? "#e11d48" : "#085041",
              textTransform: "uppercase",
              letterSpacing: "0.07em",
            }}
          >
            {isLoading
              ? "Agent thinking — XAI"
              : collapsed
              ? "Analyse XAI — terminée"
              : "Analyse XAI — terminée"}
          </span>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
          {!isLoading && (
            <span
              style={{
                fontSize: 11,
                fontFamily: "var(--font-mono)",
                color: "#1D9E75",
                fontWeight: 600,
              }}
            >
              {successCount} étapes ✓
            </span>
          )}
          {/* Triangle pour plier/déplier le contenu XAI */}
          <button
            type="button"
            onClick={() => setIsOpen((v) => !v)}
            style={{
              width: 20,
              height: 20,
              borderRadius: 999,
              border: "0.5px solid #9FE1CB",
              background: "#ffffff",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              cursor: "pointer",
              padding: 0,
            }}
          >
            <span
              style={{
                display: "inline-block",
                transform: isOpen ? "rotate(90deg)" : "rotate(0deg)",
                transition: "transform 0.15s ease",
                fontSize: 10,
                color: "#1D9E75",
              }}
            >
              ▶
            </span>
          </button>
        </div>
      </div>

      {/* Steps — cachés si collapsed, scrollable si beaucoup d'éléments */}
      {!effectiveCollapsed && (
        <div
          style={{
            height: 220,
            overflowY: "auto",
            borderTop: dims ? "none" : "0.5px solid #f0fdf4",
          }}
        >
          <div
            style={{
              padding: "10px 16px",
              fontFamily: "var(--font-mono)",
              fontSize: 11,
              display: "flex",
              flexDirection: "column",
              gap: 4,
              borderBottom: dims ? "0.5px solid #f0fdf4" : "none",
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
                        ? "#1D9E75"
                        : step.status === "error"
                        ? "#e11d48"
                        : step.status === "loading"
                        ? "#9ca3af"
                        : "#534AB7",
                  }}
                >
                  <span style={{ width: 14, flexShrink: 0 }}>
                    {step.status === "loading" && "●●●"}
                    {step.status === "success" && "✓"}
                    {step.status === "error" && "✗"}
                    {step.status === "info" && "→"}
                  </span>
                  <span>
                    {step.text}
                    {step.detail?.sector && ` · secteur ${step.detail.sector}`}
                    {step.detail?.confidence &&
                      ` · confiance ${step.detail.confidence}%`}
                    {step.detail?.model && ` · ${step.detail.model}`}
                    {step.detail?.elapsed_ms &&
                      ` · ${step.detail.elapsed_ms}ms`}
                  </span>
                </div>

                {step.detail?.dimensions && (
                  <div
                    style={{
                      paddingLeft: 22,
                      display: "flex",
                      gap: 12,
                      fontSize: 10,
                      marginTop: 2,
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
                            ? "#1D9E75"
                            : "#e11d48",
                          fontWeight: 600,
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
                      paddingLeft: 22,
                      fontSize: 10,
                      color: step.detail.score >= 80 ? "#1D9E75" : "#EF9F27",
                      fontWeight: 600,
                    }}
                  >
                    score : {step.detail.score}/100
                  </div>
                )}
              </div>
            ))}
          </div>

          {dims && (
            <div
              style={{
                padding: "10px 16px",
                background: "#fafffe",
                display: "flex",
                gap: 8,
              }}
            >
              {[
                { k: "problem", l: "Problème" },
                { k: "target", l: "Cible" },
                { k: "solution", l: "Solution" },
              ].map(({ k, l }) => (
                <div
                  key={k}
                  style={{
                    flex: 1,
                    padding: "8px 10px",
                    background: dims[k] ? "#f0fdf4" : "#fff5f5",
                    border: `0.5px solid ${
                      dims[k] ? "#9FE1CB" : "#fecaca"
                    }`,
                    borderRadius: 8,
                    textAlign: "center",
                  }}
                >
                  <div
                    style={{
                      fontSize: 9,
                      fontWeight: 700,
                      color: dims[k] ? "#1D9E75" : "#e11d48",
                      textTransform: "uppercase",
                      letterSpacing: "0.07em",
                      marginBottom: 3,
                    }}
                  >
                    {l}
                  </div>
                  <div
                    style={{
                      fontSize: 11,
                      color: dims[k] ? "#085041" : "#e11d48",
                      fontWeight: 600,
                    }}
                  >
                    {dims[k] ? "✓ Détecté" : "✗ Manquant"}
                  </div>
                </div>
              ))}

              {sector && (
                <div
                  style={{
                    flex: 1,
                    padding: "8px 10px",
                    background: "#f0eeff",
                    border: "0.5px solid #AFA9EC",
                    borderRadius: 8,
                    textAlign: "center",
                  }}
                >
                  <div
                    style={{
                      fontSize: 9,
                      fontWeight: 700,
                      color: "#7F77DD",
                      textTransform: "uppercase",
                      letterSpacing: "0.07em",
                      marginBottom: 3,
                    }}
                  >
                    Secteur
                  </div>
                  <div
                    style={{
                      fontSize: 11,
                      color: "#3C3489",
                      fontWeight: 700,
                    }}
                  >
                    {sector}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
