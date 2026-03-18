export default function ClarifiedBlock({ data, score }) {
  if (!data) return null;

  // ── Score insuffisant → bloc warning ────────────────
  if (score < 55) {
    return (
      <div
        style={{
          background: "white",
          border: "0.5px solid #FAC775",
          borderRadius: 14,
          overflow: "hidden",
          boxShadow: "0 4px 16px rgba(239,159,39,0.1)",
          animation: "slideUp 0.35s ease forwards",
        }}
      >
        <div
          style={{
            padding: "12px 18px",
            background: "#FAEEDA",
            borderBottom: "0.5px solid #FAC775",
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
          }}
        >
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: 8,
            }}
          >
            <div
              style={{
                width: 7,
                height: 7,
                borderRadius: "50%",
                background: "#EF9F27",
              }}
            />
            <span
              style={{
                fontSize: 11,
                fontWeight: 700,
                color: "#854F0B",
                textTransform: "uppercase",
                letterSpacing: "0.07em",
              }}
            >
              Idée insuffisamment claire
            </span>
          </div>
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: 8,
            }}
          >
            <div
              style={{
                width: 80,
                height: 6,
                borderRadius: 99,
                background: "#FAC775",
                overflow: "hidden",
              }}
            >
              <div
                style={{
                  height: "100%",
                  width: `${score}%`,
                  background: "#EF9F27",
                  borderRadius: 99,
                }}
              />
            </div>
            <span
              style={{
                fontSize: 14,
                fontWeight: 800,
                color: "#854F0B",
              }}
            >
              {score}
            </span>
            <span
              style={{
                fontSize: 11,
                color: "#EF9F27",
              }}
            >
              /100
            </span>
          </div>
        </div>

        <div
          style={{
            padding: "16px 18px",
            display: "flex",
            flexDirection: "column",
            gap: 12,
          }}
        >
          <div
            style={{
              display: "flex",
              gap: 12,
              alignItems: "flex-start",
            }}
          >
            <div
              style={{
                width: 36,
                height: 36,
                borderRadius: "50%",
                background: "#FAEEDA",
                border: "0.5px solid #FAC775",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                flexShrink: 0,
              }}
            >
              <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                <circle
                  cx="8"
                  cy="8"
                  r="6"
                  stroke="#EF9F27"
                  strokeWidth="1.3"
                />
                <path
                  d="M8 5v3.5M8 10.5v.5"
                  stroke="#EF9F27"
                  strokeWidth="1.4"
                  strokeLinecap="round"
                />
              </svg>
            </div>
            <div>
              <div
                style={{
                  fontSize: 13,
                  fontWeight: 700,
                  color: "#854F0B",
                  marginBottom: 6,
                }}
              >
                Votre idée nécessite plus de précisions
              </div>
              <div
                style={{
                  fontSize: 12,
                  color: "#633806",
                  lineHeight: 1.6,
                }}
              >
                Le score de clarté est de {score}/100. Pour lancer le pipeline,
                votre idée doit atteindre un score minimum de 80/100. Revenez en
                arrière et précisez les dimensions manquantes.
              </div>
            </div>
          </div>

          {/* Dimensions manquantes */}
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "1fr 1fr 1fr",
              gap: 8,
            }}
          >
            {[
              { label: "Problème", ok: !!data.problem, value: data.problem },
              {
                label: "Cible",
                ok: !!data.target_users,
                value: data.target_users,
              },
              {
                label: "Solution",
                ok: !!data.solution_description,
                value: data.solution_description,
              },
            ].map(({ label, ok, value }) => (
              <div
                key={label}
                style={{
                  padding: "10px",
                  background: ok ? "#f0fdf4" : "#fff5f5",
                  border: `0.5px solid ${ok ? "#9FE1CB" : "#fecaca"}`,
                  borderRadius: 10,
                }}
              >
                <div
                  style={{
                    fontSize: 9,
                    fontWeight: 700,
                    color: ok ? "#1D9E75" : "#e11d48",
                    textTransform: "uppercase",
                    letterSpacing: "0.07em",
                    marginBottom: 4,
                  }}
                >
                  {ok ? "✓" : "✗"} {label}
                </div>
                <div
                  style={{
                    fontSize: 11,
                    color: ok ? "#374151" : "#e11d48",
                    fontWeight: ok ? 400 : 600,
                  }}
                >
                  {ok ? (value || "").slice(0, 40) + "..." : "Non renseigné"}
                </div>
              </div>
            ))}
          </div>

          <div
            style={{
              padding: "10px 14px",
              background: "#fff9f0",
              border: "0.5px solid #FAC775",
              borderRadius: 10,
              fontSize: 12,
              color: "#854F0B",
            }}
          >
            Le lancement du pipeline est désactivé. Score minimum requis :{" "}
            <strong>80/100</strong>
          </div>
        </div>
      </div>
    );
  }

  // ── Score suffisant → affichage normal ──────────────
  const scoreLabel =
    score >= 90
      ? { text: "Excellent", color: "#085041", bg: "#f0fdf4", border: "#9FE1CB" }
      : score >= 80
        ? { text: "Très bien", color: "#1D9E75", bg: "#f0fdf4", border: "#9FE1CB" }
        : { text: "Acceptable", color: "#854F0B", bg: "#FAEEDA", border: "#FAC775" };

  return (
    <div
      style={{
        background: "white",
        border: "0.5px solid #AFA9EC",
        borderRadius: 14,
        overflow: "hidden",
        boxShadow: "0 4px 20px rgba(124,58,237,0.1)",
        animation: "slideUp 0.35s ease forwards",
      }}
    >
      {/* Header avec score */}
      <div
        style={{
          padding: "12px 18px",
          background: "linear-gradient(135deg,#f0eeff,#fafafe)",
          borderBottom: "0.5px solid #AFA9EC",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
        }}
      >
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: 8,
          }}
        >
          <div
            style={{
              width: 7,
              height: 7,
              borderRadius: "50%",
              background: "#7F77DD",
            }}
          />
          <span
            style={{
              fontSize: 11,
              fontWeight: 700,
              color: "#3C3489",
              textTransform: "uppercase",
              letterSpacing: "0.07em",
            }}
          >
            Idée structurée
          </span>
        </div>
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: 10,
          }}
        >
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: 6,
            }}
          >
            <div
              style={{
                width: 90,
                height: 6,
                borderRadius: 99,
                background: "#e8e4ff",
                overflow: "hidden",
              }}
            >
              <div
                style={{
                  height: "100%",
                  width: `${score}%`,
                  background:
                    score >= 80
                      ? "linear-gradient(90deg,#7F77DD,#1D9E75)"
                      : "linear-gradient(90deg,#7F77DD,#EF9F27)",
                  borderRadius: 99,
                  transition: "width 1s ease",
                }}
              />
            </div>
            <span
              style={{
                fontSize: 16,
                fontWeight: 800,
                color: scoreLabel.color,
              }}
            >
              {score}
            </span>
            <span style={{ fontSize: 11, color: "#AFA9EC" }}>/100</span>
          </div>
          <div
            style={{
              padding: "3px 10px",
              background: scoreLabel.bg,
              border: `0.5px solid ${scoreLabel.border}`,
              borderRadius: 99,
              fontSize: 10,
              fontWeight: 700,
              color: scoreLabel.color,
            }}
          >
            {scoreLabel.text} ✓
          </div>
        </div>
      </div>

      <div
        style={{
          padding: "16px 18px",
          display: "flex",
          flexDirection: "column",
          gap: 12,
        }}
      >
        {data.short_pitch && (
          <div
            style={{
              fontSize: 14,
              fontStyle: "italic",
              color: "#534AB7",
              padding: "12px 16px",
              background: "#f8f7ff",
              borderLeft: "3px solid #7F77DD",
              fontWeight: 600,
              lineHeight: 1.5,
            }}
          >
            "{data.short_pitch}"
          </div>
        )}

        <div
          style={{
            display: "grid",
            gridTemplateColumns: "1fr 1fr 1fr",
            gap: 8,
          }}
        >
          <div
            style={{
              padding: "12px",
              background: "#f8f7ff",
              border: "0.5px solid #e8e4ff",
              borderRadius: 12,
            }}
          >
            <div
              style={{
                fontSize: 9,
                fontWeight: 700,
                color: "#7F77DD",
                textTransform: "uppercase",
                letterSpacing: "0.08em",
                marginBottom: 6,
              }}
            >
              Ce que c&apos;est
            </div>
            <div style={{ fontSize: 12, color: "#374151", lineHeight: 1.5 }}>
              {data.solution_description || "—"}
            </div>
          </div>
          <div
            style={{
              padding: "12px",
              background: "#f0fdf4",
              border: "0.5px solid #9FE1CB",
              borderRadius: 12,
            }}
          >
            <div
              style={{
                fontSize: 9,
                fontWeight: 700,
                color: "#1D9E75",
                textTransform: "uppercase",
                letterSpacing: "0.08em",
                marginBottom: 6,
              }}
            >
              Pour qui ?
            </div>
            <div
              style={{
                fontSize: 12,
                color: "#374151",
                lineHeight: 1.5,
                fontWeight: 600,
              }}
            >
              {data.target_users || "—"}
            </div>
          </div>
          <div
            style={{
              padding: "12px",
              background: "#FAEEDA",
              border: "0.5px solid #FAC775",
              borderRadius: 12,
            }}
          >
            <div
              style={{
                fontSize: 9,
                fontWeight: 700,
                color: "#854F0B",
                textTransform: "uppercase",
                letterSpacing: "0.08em",
                marginBottom: 6,
              }}
            >
              Secteur
            </div>
            <div style={{ fontSize: 12, color: "#374151", fontWeight: 700 }}>
              {data.sector || "—"}
            </div>
          </div>
        </div>

        <div
          style={{
            padding: "12px 14px",
            background: "#fff5f5",
            border: "0.5px solid #fecaca",
            borderRadius: 12,
          }}
        >
          <div
            style={{
              fontSize: 9,
              fontWeight: 700,
              color: "#e11d48",
              textTransform: "uppercase",
              letterSpacing: "0.08em",
              marginBottom: 6,
            }}
          >
            Problème résolu
          </div>
          <div style={{ fontSize: 12, color: "#374151", lineHeight: 1.6 }}>
            {data.problem || "—"}
          </div>
        </div>
      </div>
    </div>
  );
}
