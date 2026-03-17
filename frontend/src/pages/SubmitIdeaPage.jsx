import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  HiOutlineArrowRight,
  HiOutlineLightBulb,
  HiOutlineChatBubbleLeftRight,
  HiOutlineRocketLaunch,
} from "react-icons/hi2";
import { Navbar } from "@/components/layout/Navbar";
import { Card } from "@/shared/ui/Card";
import { Button } from "@/shared/ui/Button";
import { apiCreateIdea, getErrorMessage } from "@/services/ideaApi";
import { useAuth } from "@/shared/hooks/useAuth";

const SECTOR_OPTIONS = [
  { value: "tech", label: "Tech / SaaS" },
  { value: "ecommerce", label: "E-commerce" },
  { value: "sante", label: "Santé" },
  { value: "education", label: "Éducation" },
  { value: "finance", label: "Finance" },
  { value: "alimentation", label: "Alimentation" },
  { value: "mode", label: "Mode" },
  { value: "autre", label: "Autre" },
];

const MAX_DESC_LENGTH = 500;
const inputFocusClass =
  "w-full rounded-lg border border-[#E5E7EB] bg-white px-4 py-2.5 text-sm text-[#111827] placeholder:text-[#6B7280] focus:border-[#7C3AED] focus:outline-none focus:ring-1 focus:ring-[#7C3AED]";

export default function SubmitIdeaPage() {
  const [name, setName] = useState("");
  const [sector, setSector] = useState("");
  const [targetAudience, setTargetAudience] = useState("");
  const [description, setDescription] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const navigate = useNavigate();
  const { token } = useAuth();

  const nameValid = name.trim().length >= 2;
  const descValid = description.trim().length >= 20;
  const canSubmit = nameValid && sector && descValid && !loading;

  const handleDescriptionChange = (e) => {
    const v = e.target.value;
    if (v.length <= MAX_DESC_LENGTH) setDescription(v);
    setError("");
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!canSubmit || !token) return;
    setError("");
    setLoading(true);
    try {
      const data = await apiCreateIdea(
        {
          name: name.trim(),
          sector,
          target_audience: targetAudience.trim() || undefined,
          description: description.trim(),
        },
        token,
      );
      navigate(`/ideas/${data.id}`, { replace: true });
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  const descCount = description.length;
  const descNearLimit = descCount > 450;

  return (
    <div className="h-screen flex flex-col overflow-hidden bg-white">
      <Navbar variant="app" />
      <main className="flex flex-1 overflow-hidden">
        <div className="mx-auto w-full max-w-[1400px] px-6 py-4 flex flex-1 items-center justify-center">
          <div className="w-full max-w-[700px] bg-white rounded-xl border border-[#E5E7EB] shadow-sm p-6 space-y-4">
            <h1 className="text-xl font-semibold text-[#111827]">Nouvelle idée</h1>

            <div className="flex items-center gap-0">
              <div className="flex flex-col items-center">
                <div
                  className="flex h-8 w-8 items-center justify-center rounded-full bg-[#7C3AED] text-sm font-medium text-white"
                  aria-hidden
                >
                  1
                </div>
                <span className="mt-1.5 flex items-center gap-1 text-xs font-medium text-[#7C3AED]">
                  <HiOutlineLightBulb className="h-3.5 w-3.5" aria-hidden />
                  Votre idée
                </span>
              </div>
              <div className="h-0.5 w-8 flex-1 min-w-[24px] bg-[#E5E7EB]" />
              <div className="flex flex-col items-center">
                <div
                  className="flex h-8 w-8 items-center justify-center rounded-full bg-[#E5E7EB] text-sm font-medium text-[#9CA3AF]"
                  aria-hidden
                >
                  2
                </div>
                <span className="mt-1.5 flex items-center gap-1 text-xs text-[#9CA3AF]">
                  <HiOutlineChatBubbleLeftRight className="h-3.5 w-3.5" aria-hidden />
                  Affiner avec l&apos;agent
                </span>
              </div>
              <div className="h-0.5 w-8 flex-1 min-w-[24px] bg-[#E5E7EB]" />
              <div className="flex flex-col items-center">
                <div
                  className="flex h-8 w-8 items-center justify-center rounded-full bg-[#E5E7EB] text-sm font-medium text-[#9CA3AF]"
                  aria-hidden
                >
                  3
                </div>
                <span className="mt-1.5 flex items-center gap-1 text-xs text-[#9CA3AF]">
                  <HiOutlineRocketLaunch className="h-3.5 w-3.5" aria-hidden />
                  Lancer le pipeline
                </span>
              </div>
            </div>

            <div>
              <span className="inline-flex rounded-full bg-[#7C3AED] px-2.5 py-0.5 text-xs font-medium text:white">
                Étape 1 sur 3
              </span>
            </div>

            <form onSubmit={handleSubmit} className="flex flex-col space-y-4">
              <div>
                <label
                  htmlFor="idea-name"
                  className="mb-1.5 block text-sm font-medium text-[#111827]"
                >
                  Nom de votre idée
                </label>
                <input
                  id="idea-name"
                  type="text"
                  value={name}
                  onChange={(e) => {
                    setName(e.target.value);
                    setError("");
                  }}
                  placeholder="Ex : EcoShop, TechMentor..."
                  className={inputFocusClass}
                />
                <p className="mt-1 text-xs text-[#6B7280]">
                  Donnez un nom court et mémorable
                </p>
                {name.trim().length > 0 && name.trim().length < 2 && (
                  <p className="mt-0.5 text-xs text-red-500">
                    Minimum 2 caractères
                  </p>
                )}
              </div>

              <div className="grid gap-4 sm:grid-cols-2">
                <div>
                  <label
                    htmlFor="idea-sector"
                    className="mb-1.5 block text-sm font-medium text-[#111827]"
                  >
                    Secteur
                  </label>
                  <select
                    id="idea-sector"
                    value={sector}
                    onChange={(e) => {
                      setSector(e.target.value);
                      setError("");
                    }}
                    className={inputFocusClass}
                  >
                    <option value="">Sélectionner</option>
                    {SECTOR_OPTIONS.map((s) => (
                      <option key={s.value} value={s.value}>
                        {s.label}
                      </option>
                    ))}
                  </select>
                </div>
                <div>
                  <label
                    htmlFor="idea-audience"
                    className="mb-1.5 block text-sm font-medium text-[#111827]"
                  >
                    Public cible
                  </label>
                  <input
                    id="idea-audience"
                    type="text"
                    value={targetAudience}
                    onChange={(e) => setTargetAudience(e.target.value)}
                    placeholder="Ex : étudiants, PME, entrepreneurs..."
                    className={inputFocusClass}
                  />
                </div>
              </div>

              <div>
                <label
                  htmlFor="idea-desc"
                  className="mb-1.5 block text-sm font-medium text-[#111827]"
                >
                  Description de votre idée
                </label>
                <textarea
                  id="idea-desc"
                  value={description}
                  onChange={handleDescriptionChange}
                  placeholder="Décrivez votre idée : quel problème résout-elle ? pour qui ? comment ?"
                  className={`resize-none h-[120px] ${inputFocusClass}`}
                />
                <div className="mt-1 flex items-center justify-between gap-2">
                  <p className="text-xs text-[#6B7280]">
                    Minimum 20 caractères · Soyez précis, l&apos;agent s&apos;en chargera
                  </p>
                  <span
                    className={`text-xs tabular-nums ${
                      descNearLimit ? "text-amber-600" : "text-[#6B7280]"
                    }`}
                  >
                    {descCount} / {MAX_DESC_LENGTH}
                  </span>
                </div>
                {description.trim().length > 0 &&
                  description.trim().length < 20 && (
                    <p className="mt-0.5 text-xs text-red-500">
                      Minimum 20 caractères
                    </p>
                  )}
              </div>

              {error && (
                <div className="rounded-[8px] border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-600">
                  {error}
                </div>
              )}

              <Button
                type="submit"
                variant="primary"
                fullWidth
                disabled={!canSubmit}
                className="gap-2 h-9 px-4 text-sm rounded-lg"
              >
                {loading ? (
                  <>
                    <span
                      className="inline-block h-5 w-5 animate-spin rounded-full border-2 border-white border-t-transparent"
                      aria-hidden
                    />
                    Sauvegarde en cours...
                  </>
                ) : (
                  <>
                    Soumettre mon idée
                    <HiOutlineArrowRight className="h-5 w-5" />
                  </>
                )}
              </Button>
            </form>
          </div>
        </div>
      </main>
    </div>
  );
}

