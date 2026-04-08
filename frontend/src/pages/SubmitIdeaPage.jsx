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

  /* ── Logic (unchanged) ─────────────────────────────────────────────── */
  const handleSubmit = async () => {
    if (description.trim().length < 20) {
      setError("Décrivez votre idée en au moins 20 caractères.");
      return;
    }
    setIsSubmitting(true);
    setError("");
    try {
      const res = await fetch(`${API_URL}/ideas`, {
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
      if (!res.ok) throw new Error("Erreur lors de la création");
      const idea = await res.json();
      navigate(`/ideas/${idea.id}/clarifier`);
    } catch {
      setError("Une erreur est survenue. Réessayez.");
    } finally {
      setIsSubmitting(false);
    }
  };

  const charCount = description.length;
  const isReady   = description.trim().length >= 20;
  const remaining = 20 - description.trim().length;

  return (
    <>
      <Navbar variant="app" />

      {/* Page wrapper */}
      <div className="min-h-screen bg-[image:var(--gradient-page)] pt-24 px-4">
        <div className="mx-auto flex w-full max-w-lg flex-col items-center py-8">

          {/* ── Tag pill ───────────────────────────────────────────────── */}
          <div className="mb-5 flex items-center gap-1.5 rounded-full border border-brand-border bg-white px-4 py-1.5 shadow-card">
            <span className="h-1.5 w-1.5 rounded-full bg-brand" />
            <span className="text-xs font-semibold text-brand-dark">IA Générative & Agentique</span>
          </div>

          {/* ── Heading ────────────────────────────────────────────────── */}
          <h1 className="mb-2 text-center text-4xl font-extrabold text-ink">
            Décrivez votre idée
          </h1>
          <p className="mb-8 max-w-sm text-center text-sm leading-relaxed text-ink-muted">
            Notre agent IA analyse votre description, détecte le secteur et vous guide pour structurer votre projet.
          </p>

          {/* ── Card ───────────────────────────────────────────────────── */}
          <div className="w-full rounded-3xl border border-brand-border bg-white p-7 shadow-card-lg">

            {/* Stepper indicator */}
            <div className="mb-6 flex flex-col items-center gap-1">
              <div className="flex h-9 w-9 items-center justify-center rounded-full bg-gradient-to-br from-brand to-brand-dark shadow-btn">
                <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
                  <path
                    d="M7 1.5l1.2 3 3 .4-2.2 2.1.5 3L7 8.5l-2.5 1.5.5-3L2.8 5l3-.4L7 1.5z"
                    stroke="white"
                    strokeWidth="1.1"
                    strokeLinejoin="round"
                  />
                </svg>
              </div>
              <span className="text-2xs font-bold uppercase tracking-widest text-brand">Votre idée</span>
            </div>

            {/* Info hint */}
            <div className="mb-5 flex items-start gap-2.5 rounded-xl border border-brand-border bg-brand-50 px-4 py-3">
              <svg width="15" height="15" viewBox="0 0 14 14" fill="none" className="mt-0.5 shrink-0">
                <circle cx="7" cy="7" r="5" stroke="currentColor" strokeWidth="1.2" className="text-brand" />
                <path d="M7 4v3.5M7 9v.5" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round" className="text-brand" />
              </svg>
              <p className="text-xs leading-relaxed text-brand-darker">
                Parlez naturellement — l&apos;IA détecte le secteur et la cible automatiquement.
              </p>
            </div>

            {/* Textarea */}
            <div className="mb-5">
              <label className="mb-1.5 block text-sm font-bold text-ink">
                Votre projet
              </label>
              <textarea
                value={description}
                onChange={(e) => { setDescription(e.target.value); setError(""); }}
                placeholder="Ex: Une application qui aide les étudiants à organiser leurs révisions grâce à l'IA..."
                rows={5}
                className="w-full resize-y rounded-xl border border-brand-border bg-brand-50 px-4 py-3 text-sm text-ink placeholder:text-ink-subtle focus:border-brand focus:bg-white focus:outline-none focus:ring-2 focus:ring-brand/20 transition-all duration-150"
              />
              {/* Counter */}
              <div className="mt-2 flex items-center justify-between">
                <span className={`text-xs font-medium ${isReady ? "text-success" : "text-red-500"}`}>
                  {isReady ? "Longueur correcte ✓" : `${remaining} car. minimum`}
                </span>
                <span className="text-xs text-ink-subtle">{charCount} / 500</span>
              </div>
            </div>

            {/* Error */}
            {error && (
              <div className="mb-4 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-600">
                {error}
              </div>
            )}

            {/* Submit button */}
            <button
              type="button"
              onClick={handleSubmit}
              disabled={!isReady || isSubmitting}
              className={`flex h-12 w-full items-center justify-center gap-2 rounded-full text-sm font-bold transition-all duration-200 ${
                isReady
                  ? "bg-gradient-to-br from-brand to-brand-dark text-white shadow-btn hover:shadow-btn-hover hover:-translate-y-px"
                  : "cursor-not-allowed bg-brand-light text-brand-muted"
              } disabled:opacity-60 disabled:transform-none`}
            >
              {isSubmitting ? (
                <>
                  <span className="h-5 w-5 animate-spin rounded-full border-2 border-white border-t-transparent" />
                  Création en cours…
                </>
              ) : (
                <>
                  Lancer l&apos;analyse IA
                  <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                    <path d="M3 8h10M9 4l4 4-4 4" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" />
                  </svg>
                </>
              )}
            </button>
          </div>
        </div>
      </div>
    </>
  );
}
