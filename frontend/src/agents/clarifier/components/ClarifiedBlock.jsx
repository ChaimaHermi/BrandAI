export default function ClarifiedBlock({ data, score }) {
  if (!data) return null;

  const scoreColor =
    score >= 80
      ? "var(--color-text-success)"
      : score >= 55
      ? "var(--color-text-warning)"
      : "var(--color-text-danger)";

  const barColor = scoreColor;

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
          borderBottom: "0.5px solid var(--color-border-tertiary)",
          background: "var(--color-background-secondary)",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <div
            style={{
              width: 6,
              height: 6,
              borderRadius: "50%",
              background: "var(--color-text-success)",
            }}
          />
          <span
            style={{
              fontSize: 11,
              fontWeight: 500,
              color: "var(--color-text-secondary)",
              textTransform: "uppercase",
              letterSpacing: "0.06em",
            }}
          >
            Idée structurée
          </span>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <span
            style={{
              fontSize: 13,
              fontWeight: 500,
              color: scoreColor,
            }}
          >
            {score}/100
          </span>
          <div
            style={{
              width: 60,
              height: 4,
              borderRadius: 99,
              background: "var(--color-background-secondary)",
              overflow: "hidden",
            }}
          >
            <div
              style={{
                height: "100%",
                width: `${score}%`,
                background: barColor,
                borderRadius: 99,
                transition: "width 0.8s ease",
              }}
            />
          </div>
        </div>
      </div>

      <div
        style={{
          padding: "14px",
          display: "flex",
          flexDirection: "column",
          gap: 8,
        }}
      >
        {data.short_pitch && (
          <div
            style={{
              fontSize: 13,
              fontStyle: "italic",
              color: "#534AB7",
              padding: "8px 12px",
              background: "#EEEDFE",
              borderLeft: "2px solid #7F77DD",
              lineHeight: 1.5,
            }}
          >
            "{data.short_pitch}"
          </div>
        )}

        <div
          style={{
            display: "grid",
            gridTemplateColumns: "1fr 1fr",
            gap: 6,
          }}
        >
          <div
            style={{
              padding: "10px 12px",
              background: "var(--color-background-secondary)",
              borderRadius: "var(--border-radius-md)",
            }}
          >
            <div
              style={{
                fontSize: 10,
                fontWeight: 500,
                color: "#534AB7",
                textTransform: "uppercase",
                letterSpacing: "0.06em",
                marginBottom: 4,
              }}
            >
              Ce que c&apos;est
            </div>
            <div
              style={{
                fontSize: 12,
                color: "var(--color-text-primary)",
                lineHeight: 1.5,
              }}
            >
              {data.solution_description || "—"}
            </div>
          </div>
          <div
            style={{
              padding: "10px 12px",
              background: "var(--color-background-secondary)",
              borderRadius: "var(--border-radius-md)",
            }}
          >
            <div
              style={{
                fontSize: 10,
                fontWeight: 500,
                color: "#185FA5",
                textTransform: "uppercase",
                letterSpacing: "0.06em",
                marginBottom: 4,
              }}
            >
              Pour qui ?
            </div>
            <div
              style={{
                fontSize: 12,
                color: "var(--color-text-primary)",
                lineHeight: 1.5,
              }}
            >
              {data.target_users || "—"}
            </div>
          </div>
        </div>

        <div
          style={{
            padding: "10px 12px",
            background: "var(--color-background-secondary)",
            borderRadius: "var(--border-radius-md)",
          }}
        >
          <div
            style={{
              fontSize: 10,
              fontWeight: 500,
              color: "#854F0B",
              textTransform: "uppercase",
              letterSpacing: "0.06em",
              marginBottom: 4,
            }}
          >
            Problème résolu
          </div>
          <div
            style={{
              fontSize: 12,
              color: "var(--color-text-primary)",
              lineHeight: 1.5,
            }}
          >
            {data.problem || "—"}
          </div>
        </div>
      </div>
    </div>
  );
}

