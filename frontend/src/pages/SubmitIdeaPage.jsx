import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  HiOutlineLightBulb,
  HiOutlineChatBubbleLeftRight,
  HiOutlineRocketLaunch,
} from "react-icons/hi2";
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
      navigate(`/ideas/${idea.id}`);
    } catch (err) {
      setError("Une erreur est survenue. Réessayez.");
    } finally {
      setIsSubmitting(false);
    }
  };

  const charCount = description.length;
  const isReady = description.trim().length >= 20;

  return (
    <div className="h-screen flex flex-col bg-white">
      <Navbar variant="app" />
      <main className="flex-1 overflow-y-auto">
        <div className="max-w-4xl mx-auto px-6 pt-10 pb-10 space-y-8">
          {/* Stepper */}
          <div>
            <div className="flex items-center gap-0">
              <div className="flex flex-col items-center">
                <div className="flex h-8 w-8 items-center justify-center rounded-full bg-[#7C3AED] text-sm font-medium text-white">
                  1
                </div>
                <span className="mt-1.5 flex items-center gap-1 text-xs font-medium text-[#7C3AED]">
                  <HiOutlineLightBulb className="h-3.5 w-3.5" aria-hidden />
                  Votre idée
                </span>
              </div>
              <div className="h-0.5 w-8 flex-1 min-w-[24px] bg-[#E5E7EB]" />
              <div className="flex flex-col items-center">
                <div className="flex h-8 w-8 items-center justify-center rounded-full bg-[#E5E7EB] text-sm font-medium text-[#9CA3AF]">
                  2
                </div>
                <span className="mt-1.5 flex items-center gap-1 text-xs text-[#9CA3AF]">
                  <HiOutlineChatBubbleLeftRight
                    className="h-3.5 w-3.5"
                    aria-hidden
                  />
                  Affiner avec l&apos;agent
                </span>
              </div>
              <div className="h-0.5 w-8 flex-1 min-w-[24px] bg-[#E5E7EB]" />
              <div className="flex flex-col items-center">
                <div className="flex h-8 w-8 items-center justify-center rounded-full bg-[#E5E7EB] text-sm font-medium text-[#9CA3AF]">
                  3
                </div>
                <span className="mt-1.5 flex items-center gap-1 text-xs text-[#9CA3AF]">
                  <HiOutlineRocketLaunch className="h-3.5 w-3.5" aria-hidden />
                  Lancer le pipeline
                </span>
              </div>
            </div>
            <div className="mt-2">
              <span className="inline-flex rounded-full bg-[#7C3AED] px-2.5 py-0.5 text-xs font-medium text-white">
                Étape 1 sur 3
              </span>
            </div>
          </div>

          {/* Header */}
          <header className="space-y-2">
            <h1 className="text-3xl font-semibold tracking-tight text-gray-900">
              Décrivez votre idée
            </h1>
            <p className="text-sm text-gray-500 max-w-2xl">
              Parlez-nous de votre projet comme si vous l&apos;expliquiez à un
              ami. Notre agent IA va analyser votre description, détecter ce qui
              manque et vous guider pour la structurer parfaitement avant de
              lancer le pipeline.
            </p>
          </header>

          {/* Idea input */}
          <section className="space-y-3">
            <div className="space-y-2">
              <label className="block text-sm font-medium text-gray-800">
                Décrivez votre idée
              </label>
              <textarea
                value={description}
                onChange={(e) => {
                  setDescription(e.target.value);
                  setError("");
                }}
                placeholder={
                  "Décrivez votre idée librement :\n"
                  + "quel problème résout-elle ? pour qui ?\n"
                  + "comment fonctionne-t-elle ?\n\n"
                  + "Exemple : Une application qui aide les étudiants\n"
                  + "à organiser leurs révisions grâce à l'IA..."
                }
                className="w-full min-h-[140px] rounded-xl border border-gray-200 bg-white px-4 py-3 text-sm text-gray-900 placeholder:text-gray-400 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-purple-500 resize-none"
              />
            </div>

            {/* Counter */}
            <div className="flex justify-between items-center">
              <p className="text-xs text-gray-500">
                Soyez précis — notre agent s&apos;occupera du reste
              </p>
              <span
                className={`text-xs ${
                  charCount < 20 ? "text-red-500" : "text-gray-400"
                }`}
              >
                {charCount} / 500
              </span>
            </div>

            {/* Error */}
            {error && (
              <div className="rounded-md border border-red-200 bg-red-50 px-3 py-2 text-xs text-red-600">
                {error}
              </div>
            )}

            {/* Action button */}
            <div className="flex justify-center pt-2">
              <button
                onClick={handleSubmit}
                disabled={!isReady || isSubmitting}
                className={`inline-flex h-10 items-center justify-center rounded-lg px-5 text-sm font-medium text-white transition-colors ${
                  isReady && !isSubmitting
                    ? "bg-purple-600 hover:bg-purple-700"
                    : "bg-gray-200 text-gray-500 cursor-not-allowed"
                }`}
              >
                {isSubmitting ? "Analyse en cours..." : "Lancer l'analyse IA"}
              </button>
            </div>
          </section>
        </div>
      </main>
    </div>
  );
}

