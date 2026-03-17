export default function RefusedBlock({ data }) {
  if (!data) return null;

  return (
    <div
      style={{
        background: "var(--color-background-danger)",
        border: "0.5px solid var(--color-border-danger)",
        borderRadius: "var(--border-radius-lg)",
        padding: "14px",
        animation: "slideIn 0.3s ease",
      }}
    >
      <div
        style={{
          fontSize: 13,
          fontWeight: 500,
          color: "var(--color-text-danger)",
          marginBottom: 6,
        }}
      >
        Projet non conforme — {data.reason_category || "sécurité"}
      </div>
      <div
        style={{
          fontSize: 12,
          color: "var(--color-text-danger)",
          lineHeight: 1.6,
        }}
      >
        {data.message || data.refusal_message}
      </div>
    </div>
  );
}

