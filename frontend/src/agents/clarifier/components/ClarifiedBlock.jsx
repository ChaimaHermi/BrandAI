export default function ClarifiedBlock({ data, score }) {
  if (!data) return null;

  const scoreLabel =
    score >= 90
      ? { text: "Excellent", color: "#085041", bg: "#f0fdf4", border: "#9FE1CB" }
      : score >= 80
      ? { text: "Très bien", color: "#1D9E75", bg: "#f0fdf4", border: "#9FE1CB" }
      : score >= 60
      ? { text: "Acceptable", color: "#854F0B", bg: "#FAEEDA", border: "#FAC775" }
      : {
          text: "Incomplet",
          color: "#e11d48",
          bg: "#fff5f5",
          border: "#fecaca",
        };

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
        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
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

        <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
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
                      : score >= 60
                      ? "linear-gradient(90deg,#7F77DD,#EF9F27)"
                      : "#e11d48",
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
            <span
              style={{
                fontSize: 11,
                color: "#AFA9EC",
                fontWeight: 500,
              }}
            >
              /100
            </span>
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
        {/* Short pitch */}
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

        {/* 3 colonnes */}
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "1fr 1fr 1fr",
            gap: 8,
          }}
        >
          {/* Ce que c'est */}
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
                display: "flex",
                alignItems: "center",
                gap: 6,
                marginBottom: 8,
              }}
            >
              <div
                style={{
                  width: 18,
                  height: 18,
                  borderRadius: 5,
                  background: "#EEEDFE",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                }}
              >
                <svg width="10" height="10" viewBox="0 0 10 10" fill="none">
                  <circle
                    cx="5"
                    cy="5"
                    r="3.5"
                    stroke="#7F77DD"
                    strokeWidth="1.2"
                  />
                </svg>
              </div>
              <span
                style={{
                  fontSize: 9,
                  fontWeight: 700,
                  color: "#7F77DD",
                  textTransform: "uppercase",
                  letterSpacing: "0.08em",
                }}
              >
                Ce que c&apos;est
              </span>
            </div>
            <div
              style={{
                fontSize: 12,
                color: "#374151",
                lineHeight: 1.5,
              }}
            >
              {data.solution_description || "—"}
            </div>
          </div>

          {/* Pour qui */}
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
                display: "flex",
                alignItems: "center",
                gap: 6,
                marginBottom: 8,
              }}
            >
              <div
                style={{
                  width: 18,
                  height: 18,
                  borderRadius: 5,
                  background: "#E1F5EE",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                }}
              >
                <svg width="10" height="10" viewBox="0 0 10 10" fill="none">
                  <circle
                    cx="5"
                    cy="3.5"
                    r="1.8"
                    stroke="#1D9E75"
                    strokeWidth="1.1"
                  />
                  <path
                    d="M1.5 9c0-2 1.6-3 3.5-3s3.5 1 3.5 3"
                    stroke="#1D9E75"
                    strokeWidth="1.1"
                    strokeLinecap="round"
                  />
                </svg>
              </div>
              <span
                style={{
                  fontSize: 9,
                  fontWeight: 700,
                  color: "#1D9E75",
                  textTransform: "uppercase",
                  letterSpacing: "0.08em",
                }}
              >
                Pour qui ?
              </span>
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

          {/* Secteur */}
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
                display: "flex",
                alignItems: "center",
                gap: 6,
                marginBottom: 8,
              }}
            >
              <div
                style={{
                  width: 18,
                  height: 18,
                  borderRadius: 5,
                  background: "#FAC775",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                }}
              >
                <svg width="10" height="10" viewBox="0 0 10 10" fill="none">
                  <path
                    d="M2 5h6M5 2l3 3-3 3"
                    stroke="#854F0B"
                    strokeWidth="1.2"
                    strokeLinecap="round"
                  />
                </svg>
              </div>
              <span
                style={{
                  fontSize: 9,
                  fontWeight: 700,
                  color: "#854F0B",
                  textTransform: "uppercase",
                  letterSpacing: "0.08em",
                }}
              >
                Secteur
              </span>
            </div>
            <div
              style={{
                fontSize: 12,
                color: "#374151",
                fontWeight: 700,
              }}
            >
              {data.sector || "—"}
            </div>
          </div>
        </div>

        {/* Problème résolu */}
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
              display: "flex",
              alignItems: "center",
              gap: 6,
              marginBottom: 8,
            }}
          >
            <div
              style={{
                width: 18,
                height: 18,
                borderRadius: 5,
                background: "#fecaca",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
              }}
            >
              <svg width="10" height="10" viewBox="0 0 10 10" fill="none">
                <circle
                  cx="5"
                  cy="5"
                  r="3.5"
                  stroke="#e11d48"
                  strokeWidth="1"
                />
                <path
                  d="M3 5h4"
                  stroke="#e11d48"
                  strokeWidth="1.4"
                  strokeLinecap="round"
                />
              </svg>
            </div>
            <span
              style={{
                fontSize: 9,
                fontWeight: 700,
                color: "#e11d48",
                textTransform: "uppercase",
                letterSpacing: "0.08em",
              }}
            >
              Problème résolu
            </span>
          </div>
          <div
            style={{
              fontSize: 12,
              color: "#374151",
              lineHeight: 1.6,
            }}
          >
            {data.problem || "—"}
          </div>
        </div>

        {/* Bouton lancer pipeline */}
        <button
          type="button"
          onClick={() => {
            const path = window.location.pathname.replace("clarifier", "enhancer");
            window.location.href = path;
          }}
          style={{
            width: "100%",
            padding: "13px",
            background: "linear-gradient(135deg,#7F77DD,#534AB7)",
            color: "white",
            border: "none",
            borderRadius: 99,
            fontSize: 14,
            fontWeight: 700,
            cursor: "pointer",
            boxShadow: "0 4px 16px rgba(124,58,237,0.3)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            gap: 8,
            transition: "all 0.2s",
          }}
          onMouseOver={(e) => {
            e.currentTarget.style.boxShadow =
              "0 6px 20px rgba(124,58,237,0.4)";
            e.currentTarget.style.transform = "translateY(-1px)";
          }}
          onMouseOut={(e) => {
            e.currentTarget.style.boxShadow =
              "0 4px 16px rgba(124,58,237,0.3)";
            e.currentTarget.style.transform = "translateY(0)";
          }}
        >
          <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
            <path
              d="M3 8h10M9 4l4 4-4 4"
              stroke="white"
              strokeWidth="1.6"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          </svg>
          Lancer le pipeline complet →
        </button>
      </div>
    </div>
  );
}
