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
    <div
      style={{
        background: "white",
        border: "0.5px solid #fecaca",
        borderRadius: 14,
        overflow: "hidden",
        boxShadow: "0 4px 20px rgba(225,29,72,0.08)",
        animation: "slideUp 0.35s ease forwards",
      }}
    >
      {/* Header */}
      <div
        style={{
          padding: "12px 18px",
          background: "linear-gradient(135deg,#fff5f5,#fff8f8)",
          borderBottom: "0.5px solid #fecaca",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
        }}
      >
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: 10,
          }}
        >
          <div
            style={{
              width: 32,
              height: 32,
              borderRadius: "50%",
              background: "#fff5f5",
              border: "1.5px solid #fecaca",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              flexShrink: 0,
            }}
          >
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
            <div
              style={{
                fontSize: 13,
                fontWeight: 700,
                color: "#e11d48",
              }}
            >
              Projet non conforme
            </div>
            <div
              style={{
                fontSize: 10,
                color: "#f87171",
                fontWeight: 500,
              }}
            >
              Catégorie : {categoryLabel}
            </div>
          </div>
        </div>

        {/* Badge pipeline bloqué */}
        <div
          style={{
            padding: "4px 12px",
            background: "#fff5f5",
            border: "0.5px solid #fecaca",
            borderRadius: 99,
            fontSize: 10,
            fontWeight: 700,
            color: "#e11d48",
            flexShrink: 0,
          }}
        >
          🔒 Pipeline bloqué
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
        {/* Message LLM */}
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
              background: "#fff5f5",
              border: "0.5px solid #fecaca",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              flexShrink: 0,
            }}
          >
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
          <div
            style={{
              fontSize: 13,
              color: "#374151",
              lineHeight: 1.7,
              flex: 1,
            }}
          >
            {refusalText}
          </div>
        </div>

        {/* Ce que BrandAI peut faire */}
        <div
          style={{
            background: "#f8f7ff",
            border: "0.5px solid #e8e4ff",
            borderRadius: 10,
            padding: "12px 14px",
          }}
        >
          <div
            style={{
              fontSize: 10,
              fontWeight: 700,
              color: "#7F77DD",
              textTransform: "uppercase",
              letterSpacing: "0.07em",
              marginBottom: 8,
            }}
          >
            BrandAI peut vous accompagner pour
          </div>
          <div
            style={{
              display: "flex",
              flexDirection: "column",
              gap: 4,
            }}
          >
            {[
              "Des projets tech, éducation, ecommerce, santé",
              "Des startups et idées innovantes légales",
              "Des marques, produits et services éthiques",
            ].map((item, i) => (
              <div
                key={i}
                style={{
                  fontSize: 12,
                  color: "#534AB7",
                  display: "flex",
                  gap: 6,
                }}
              >
                <span style={{ flexShrink: 0 }}>→</span>
                {item}
              </div>
            ))}
          </div>
        </div>

        {/* Bouton nouvelle idée */}
        <button
          onClick={() => navigate("/ideas/new")}
          style={{
            width: "100%",
            padding: "12px",
            background: "linear-gradient(135deg,#7F77DD,#534AB7)",
            color: "white",
            border: "none",
            borderRadius: 99,
            fontSize: 13,
            fontWeight: 700,
            cursor: "pointer",
            boxShadow: "0 4px 14px rgba(124,58,237,0.25)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            gap: 8,
            transition: "all 0.2s",
          }}
          onMouseOver={(e) => {
            e.currentTarget.style.boxShadow =
              "0 6px 20px rgba(124,58,237,0.35)";
            e.currentTarget.style.transform = "translateY(-1px)";
          }}
          onMouseOut={(e) => {
            e.currentTarget.style.boxShadow =
              "0 4px 14px rgba(124,58,237,0.25)";
            e.currentTarget.style.transform = "translateY(0)";
          }}
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

