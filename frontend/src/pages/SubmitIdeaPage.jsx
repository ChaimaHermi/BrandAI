import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Navbar } from "@/components/layout/Navbar";
import { useAuth } from "@/shared/hooks/useAuth";

export default function SubmitIdeaPage() {
  const [description, setDescription] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState("");
  const navigate = useNavigate();
  const { token } = useAuth();
  const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000/api";

  const handleSubmit = async () => {
    if (description.trim().length < 20) {
      setError("Décrivez votre idée en au moins 20 caractères.");
      return;
    }

    setIsSubmitting(true);
    setError("");

    try {
      const response = await fetch(`${API_URL}/ideas`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          name: "",
          description: description.trim(),
          sector: "",
          target_audience: "",
        }),
      });

      if (!response.ok) {
        throw new Error("Erreur lors de la création");
      }

      const idea = await response.json();
      navigate(`/ideas/${idea.id}/clarifier`);
    } catch (err) {
      setError("Une erreur est survenue. Réessayez.");
    } finally {
      setIsSubmitting(false);
    }
  };

  const charCount = description.length;
  const isReady = description.trim().length >= 20;

  return (
    <>
      <Navbar variant="app" />
      <div
        className="pt-20 px-6"
        style={{
          minHeight: "100vh",
          background:
            "linear-gradient(135deg,#f8f7ff 0%,#f0eeff 40%,#faf5ff 100%)",
          fontFamily: "var(--font-sans)",
        }}
      >
        <div className="max-w-3xl mx-auto w-full">
          <div
            style={{
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              padding: "2rem 0",
            }}
          >
            <div style={{ width: "100%", maxWidth: 520 }}>
              {/* Badge */}
              <div
                style={{
                  display: "flex",
                  justifyContent: "center",
                  marginBottom: 20,
                }}
              >
                <div
                  style={{
                    display: "inline-flex",
                    alignItems: "center",
                    gap: 6,
                    padding: "5px 14px",
                    background: "white",
                    border: "0.5px solid #AFA9EC",
                    borderRadius: 99,
                    boxShadow: "0 1px 4px rgba(124,58,237,0.1)",
                  }}
                >
                  <div
                    style={{
                      width: 6,
                      height: 6,
                      borderRadius: "50%",
                      background: "#7F77DD",
                    }}
                  />
                  <span
                    style={{
                      fontSize: 11,
                      color: "#534AB7",
                      fontWeight: 600,
                    }}
                  >
                    IA Générative & Agentique
                  </span>
                </div>
              </div>

              {/* Title */}
              <h1
                style={{
                  fontSize: 28,
                  fontWeight: 800,
                  color: "#1a1040",
                  textAlign: "center",
                  margin: "0 0 8px",
                  lineHeight: 1.2,
                }}
              >
                Décrivez votre idée
              </h1>
              <p
                style={{
                  fontSize: 13,
                  color: "#6b7280",
                  textAlign: "center",
                  margin: "0 0 28px",
                  lineHeight: 1.6,
                }}
              >
                Notre agent IA analyse votre description, détecte le secteur et
                vous guide pour structurer votre projet.
              </p>

              {/* Card */}
              <div
                style={{
                  background: "white",
                  borderRadius: 20,
                  border: "0.5px solid #e8e4ff",
                  padding: 28,
                  boxShadow: "0 8px 32px rgba(124,58,237,0.1)",
                }}
              >
                {/* Stepper */}
                <div
                  style={{
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    marginBottom: 24,
                  }}
                >
                  <div
                    style={{
                      display: "flex",
                      flexDirection: "column",
                      alignItems: "center",
                      gap: 4,
                    }}
                  >
                    <div
                      style={{
                        width: 30,
                        height: 30,
                        borderRadius: "50%",
                        background: "linear-gradient(135deg,#7F77DD,#534AB7)",
                        display: "flex",
                        alignItems: "center",
                        justifyContent: "center",
                        boxShadow: "0 2px 10px rgba(124,58,237,0.3)",
                      }}
                    >
                      <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
                        <path
                          d="M6 1l1 2.5 2.5.4-1.8 1.7.4 2.4L6 6.8 3.9 8l.4-2.4L2.5 3.9l2.5-.4L6 1z"
                          stroke="white"
                          strokeWidth="1"
                          strokeLinejoin="round"
                        />
                      </svg>
                    </div>
                    <span
                      style={{
                        fontSize: 9,
                        color: "#7F77DD",
                        fontWeight: 700,
                        whiteSpace: "nowrap",
                      }}
                    >
                      Votre idée
                    </span>
                  </div>
                </div>

                {/* Info pill */}
                <div
                  style={{
                    background: "#f8f7ff",
                    border: "0.5px solid #e8e4ff",
                    borderRadius: 10,
                    padding: "10px 14px",
                    marginBottom: 18,
                    display: "flex",
                    gap: 8,
                    alignItems: "flex-start",
                  }}
                >
                  <svg
                    width="14"
                    height="14"
                    viewBox="0 0 14 14"
                    fill="none"
                    style={{ flexShrink: 0, marginTop: 1 }}
                  >
                    <circle
                      cx="7"
                      cy="7"
                      r="5"
                      stroke="#7F77DD"
                      strokeWidth="1.2"
                    />
                    <path
                      d="M7 4v3.5M7 9v.5"
                      stroke="#7F77DD"
                      strokeWidth="1.3"
                      strokeLinecap="round"
                    />
                  </svg>
                  <span
                    style={{
                      fontSize: 12,
                      color: "#534AB7",
                      lineHeight: 1.6,
                    }}
                  >
                    Parlez naturellement — l&apos;IA détecte le secteur et la
                    cible automatiquement.
                  </span>
                </div>

                {/* Textarea */}
                <div style={{ marginBottom: 18 }}>
                  <label
                    style={{
                      fontSize: 12,
                      fontWeight: 700,
                      color: "#1a1040",
                      display: "block",
                      marginBottom: 6,
                    }}
                  >
                    Votre projet
                  </label>
                  <textarea
                    value={description}
                    onChange={(e) => {
                      setDescription(e.target.value);
                      setError("");
                    }}
                    placeholder="Ex: Une application qui aide les étudiants à organiser leurs révisions grâce à l'IA..."
                    rows={5}
                    style={{
                      width: "100%",
                      padding: "12px 14px",
                      fontSize: 13,
                      border: "1.5px solid #e8e4ff",
                      borderRadius: 10,
                      resize: "vertical",
                      fontFamily: "var(--font-sans)",
                      background: "#fafafe",
                      color: "#1a1040",
                      boxSizing: "border-box",
                      outline: "none",
                      lineHeight: 1.6,
                      transition: "border-color 0.2s",
                    }}
                    onFocus={(e) => {
                      e.target.style.borderColor = "#7F77DD";
                    }}
                    onBlur={(e) => {
                      e.target.style.borderColor = "#e8e4ff";
                    }}
                  />
                  <div
                    style={{
                      display: "flex",
                      justifyContent: "space-between",
                      marginTop: 5,
                    }}
                  >
                    <span
                      style={{
                        fontSize: 11,
                        color:
                          description.trim().length < 20
                            ? "#e11d48"
                            : "#1D9E75",
                      }}
                    >
                      {description.trim().length < 20
                        ? `${20 - description.trim().length} car. minimum`
                        : "Longueur correcte ✓"}
                    </span>
                    <span
                      style={{
                        fontSize: 11,
                        color: "#9ca3af",
                      }}
                    >
                      {charCount} / 500
                    </span>
                  </div>
                </div>

                {/* Error */}
                {error && (
                  <div
                    style={{
                      padding: "9px 12px",
                      background: "#fff5f5",
                      border: "0.5px solid #fecaca",
                      borderRadius: 10,
                      fontSize: 12,
                      color: "#e11d48",
                      marginBottom: 14,
                    }}
                  >
                    {error}
                  </div>
                )}

                {/* Button */}
                <button
                  type="button"
                  onClick={handleSubmit}
                  disabled={!isReady || isSubmitting}
                  style={{
                    width: "100%",
                    padding: "13px",
                    background: isReady
                      ? "linear-gradient(135deg,#7F77DD,#534AB7)"
                      : "#f3f0ff",
                    color: isReady ? "white" : "#AFA9EC",
                    border: "none",
                    borderRadius: 99,
                    fontSize: 14,
                    fontWeight: 700,
                    cursor: isReady ? "pointer" : "not-allowed",
                    boxShadow: isReady
                      ? "0 4px 16px rgba(124,58,237,0.3)"
                      : "none",
                    transition: "all 0.2s",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    gap: 8,
                  }}
                >
                  {isSubmitting ? (
                    "Création en cours..."
                  ) : (
                    <>
                      Lancer l&apos;analyse IA
                      <svg
                        width="16"
                        height="16"
                        viewBox="0 0 16 16"
                        fill="none"
                      >
                        <path
                          d="M3 8h10M9 4l4 4-4 4"
                          stroke="currentColor"
                          strokeWidth="1.6"
                          strokeLinecap="round"
                          strokeLinejoin="round"
                        />
                      </svg>
                    </>
                  )}
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </>
  );
}