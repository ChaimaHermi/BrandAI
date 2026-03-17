import React, { useState, useEffect, useMemo, useRef } from "react";
import { useParams, useNavigate, Link } from "react-router-dom";
import {
  HiOutlineArrowLeft,
  HiOutlineChatBubbleLeftRight,
  HiOutlineCheckCircle,
  HiOutlineLightBulb,
  HiOutlineRocketLaunch,
} from "react-icons/hi2";
import { Navbar } from "@/components/layout/Navbar";
import { Card } from "@/shared/ui/Card";
import { Button } from "@/shared/ui/Button";
import { Loader } from "@/shared/ui/Loader";
import { Badge } from "@/shared/ui/Badge";
import ClarifierPage from "@/agents/clarifier/pages/ClarifierPage";
import { apiGetIdea, getErrorMessage } from "@/services/ideaApi";
import { useAuth } from "@/shared/hooks/useAuth";
import { AGENTS, TECHMENTOR_RESULTS } from "@/shared/utils/mockData";

function formatDate(d) {
  if (!d) return "—";
  const date = typeof d === "string" ? new Date(d) : d;
  return date.toLocaleDateString("fr-FR", {
    day: "numeric",
    month: "long",
    year: "numeric",
  });
}

function getMockStatuses() {
  return {
    idea: "done",
    market: "done",
    brand: "running",
    content: "waiting",
    website: "waiting",
    optimizer: "waiting",
  };
}

function buildMockResults(idea) {
  const base = { ...TECHMENTOR_RESULTS };
  if (idea) {
    const desc = idea.description || idea.name;
    const shortDesc = desc.length > 120 ? `${desc.slice(0, 120)}...` : desc;
    base.idea = {
      status: "done",
      initial: desc,
      enhanced: `${idea.name} — Idée enrichie pour le secteur ${idea.sector}. ${shortDesc} Proposition de valeur clarifiée et positionnement défini.`,
      summary: "Idée enrichie et structurée avec proposition de valeur claire.",
    };
  }
  return base;
}

function StepFlow({ currentStep }) {
  const steps = [
    { key: 1, label: "Votre idée", Icon: HiOutlineLightBulb },
    {
      key: 2,
      label: "Affiner avec l'agent",
      Icon: HiOutlineChatBubbleLeftRight,
    },
    { key: 3, label: "Lancer le pipeline", Icon: HiOutlineRocketLaunch },
  ];
  return (
    <div className="flex items-start gap-1 sm:gap-2">
      {steps.map((step, index) => {
        const isCompleted = step.key < currentStep;
        const isActive = step.key === currentStep;
        const prevCompleted = index > 0 && steps[index - 1].key < currentStep;
        const Icon = step.Icon;
        return (
          <React.Fragment key={step.key}>
            {index > 0 && (
              <div
                className={`mt-2 h-0.5 flex-1 min-w-[10px] max-w-[70px] sm:max-w-[90px] ${
                  prevCompleted ? "bg-[#7C3AED]" : "bg-[#E5E7EB]"
                }`}
                aria-hidden
              />
            )}
            <div className="flex flex-col items-center gap-0.5">
              <div
                className={`flex h-7 w-7 shrink-0 items-center justify-center rounded-full transition-colors ${
                  isCompleted
                    ? "bg-[#7C3AED] text-white"
                    : isActive
                      ? "border-2 border-[#7C3AED] bg-[#F5F3FF] text-[#7C3AED]"
                      : "border border-[#E5E7EB] bg-white text-[#9CA3AF]"
                }`}
              >
                {isCompleted ? (
                  <HiOutlineCheckCircle className="h-4 w-4" aria-hidden />
                ) : (
                  <Icon className="h-4 w-4" aria-hidden />
                )}
              </div>
              <span
                className={`max-w-[90px] text-center text-[11px] font-medium leading-tight sm:max-w-[100px] ${
                  isActive
                    ? "text-[#7C3AED]"
                    : isCompleted
                      ? "text-[#6B7280]"
                      : "text-[#9CA3AF]"
                }`}
              >
                {step.label}
              </span>
            </div>
          </React.Fragment>
        );
      })}
    </div>
  );
}

export default function IdeaPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { token, user } = useAuth();
  const [idea, setIdea] = useState(null);
  const [loading, setLoading] = useState(true);
  const [notFound, setNotFound] = useState(false);
  const [fetchError, setFetchError] = useState("");
  const [activeAgent, setActiveAgent] = useState("idea");
  const [descriptionExpanded, setDescriptionExpanded] = useState(false);

  useEffect(() => {
    if (!id || !token) return;
    let cancelled = false;
    setFetchError("");
    (async () => {
      try {
        const data = await apiGetIdea(id, token);
        if (!cancelled) {
          setIdea(data);
          setNotFound(false);
        }
      } catch (err) {
        if (!cancelled) {
          const msg = err.message || "";
          if (
            msg.includes("404") ||
            msg.toLowerCase().includes("introuvable")
          ) {
            setNotFound(true);
            setFetchError("");
          } else {
            setFetchError(getErrorMessage(err));
          }
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [id, token]);

  const statuses = useMemo(() => getMockStatuses(), []);
  const results = useMemo(() => buildMockResults(idea), [idea]);
  const currentData = results[activeAgent];
  const currentStatus = statuses[activeAgent] || "waiting";

  // L'analyse Clarifier est désormais gérée par ClarifierPage

  if (loading) {
    return (
      <div className="h-screen flex flex-col overflow-hidden bg-white">
        <Navbar variant="app" />
        <main className="flex flex-1 overflow-hidden items-center justify-center">
          <div className="max-w-[1400px] mx-auto w-full px-6 py-4">
            <Loader className="h-10 w-10" />
          </div>
        </main>
      </div>
    );
  }

  if (notFound || !idea) {
    return (
      <div className="h-screen flex flex-col overflow-hidden bg-white">
        <Navbar variant="app" />
        <main className="flex flex-1 overflow-hidden">
          <div className="max-w-[1400px] mx-auto w-full px-6 py-4 flex items-center justify-center">
            <div className="max-w-[560px] w-full text-center">
              {fetchError && (
                <div className="mb-4 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-600">
                  {fetchError}
                </div>
              )}
              <p className="text-[#6B7280]">
                {notFound
                  ? "Cette idée n'existe pas ou a été supprimée."
                  : "Nous n'avons pas pu charger cette idée."}
              </p>
              <Button
                variant="outline"
                className="mt-4"
                onClick={() => navigate("/dashboard")}
              >
                Retour au tableau de bord
              </Button>
            </div>
          </div>
        </main>
      </div>
    );
  }

  const currentStep = 2;

  const description = idea.description || "—";
  const descriptionLong = description.length > 120;
  return (
    <div className="h-screen flex flex-col overflow-hidden bg-white">
      <Navbar variant="app" />

      <div className="border-b border-[#E5E7EB]">
        <div className="max-w-[1400px] mx-auto w-full px-6 py-2 flex items-center justify-between gap-4">
          <div className="flex items-center gap-2 min-w-0">
            <p className="truncate text-xs font-medium text-[#4B5563]">
              {idea.name}
            </p>
            {idea.sector && (
              <Badge className="text-[10px] shrink-0">{idea.sector}</Badge>
            )}
          </div>
          <div className="hidden md:block">
            <StepFlow currentStep={currentStep} />
          </div>
        </div>
      </div>

      <div className="flex flex-1 gap-4 overflow-hidden max-w-[1400px] mx-auto w-full px-6 py-4 min-h-0">
        {fetchError && (
          <div className="absolute top-14 left-1/2 -translate-x-1/2 z-10 rounded-[10px] border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-600 shadow-sm">
            {fetchError}
          </div>
        )}

        <aside className="w-[300px] flex-shrink-0 h-full overflow-y-auto flex flex-col gap-3 rounded-xl border border-[#E5E7EB] bg-[#FAFAFA] p-4">
          <Link
            to="/dashboard"
            className="flex shrink-0 items-center gap-1 text-xs font-medium text-[#6B7280] hover:text-[#7C3AED]"
            aria-label="Retour au tableau de bord"
          >
            <HiOutlineArrowLeft className="h-4 w-4" />
            Retour
          </Link>

          <div className="mt-1 space-y-2">
            <p className="text-[11px] font-medium uppercase tracking-wide text-[#6B7280]">
              Étapes du pipeline
            </p>
            <div className="space-y-1.5 text-xs">
              <div className="flex items-center justify-between rounded-lg py-2 px-3 bg-[#F5F3FF]">
                <div className="flex items-center gap-2">
                  <span className="inline-flex h-6 w-6 items-center justify-center rounded-full bg-[#7C3AED]/10 text-[10px] font-semibold text-[#7C3AED]">
                    IC
                  </span>
                  <span className="text-[11px] font-medium text-[#4B5563]">
                    Idea Clarifier
                  </span>
                </div>
                <Badge variant="violet" className="text-[10px]">
                  En cours
                </Badge>
              </div>
              <div className="flex items-center justify-between rounded-lg py-2 px-3">
                <div className="flex items-center gap-2">
                  <span className="inline-flex h-6 w-6 items-center justify-center rounded-full bg-[#4B5563]/5 text-[10px] font-semibold text-[#4B5563]">
                    IE
                  </span>
                  <span className="text-[11px] text-[#4B5563]">
                    Idea Enhancer
                  </span>
                </div>
                <Badge variant="waiting" className="text-[10px]">
                  En attente
                </Badge>
              </div>
              <div className="flex items-center justify-between rounded-lg py-2 px-3">
                <div className="flex items-center gap-2">
                  <span className="inline-flex h-6 w-6 items-center justify-center rounded-full bg-[#4B5563]/5 text-[10px] font-semibold text-[#4B5563]">
                    MA
                  </span>
                  <span className="text-[11px] text-[#4B5563]">
                    Market Analysis
                  </span>
                </div>
                <Badge variant="waiting" className="text-[10px]">
                  En attente
                </Badge>
              </div>
              <div className="flex items-center justify-between rounded-lg py-2 px-3">
                <div className="flex items-center gap-2">
                  <span className="inline-flex h-6 w-6 items-center justify-center rounded-full bg-[#4B5563]/5 text-[10px] font-semibold text-[#4B5563]">
                    BI
                  </span>
                  <span className="text-[11px] text-[#4B5563]">
                    Brand Identity
                  </span>
                </div>
                <Badge variant="waiting" className="text-[10px]">
                  En attente
                </Badge>
              </div>
              <div className="flex items-center justify-between rounded-lg py-2 px-3">
                <div className="flex items-center gap-2">
                  <span className="inline-flex h-6 w-6 items-center justify-center rounded-full bg-[#4B5563]/5 text-[10px] font-semibold text-[#4B5563]">
                    CC
                  </span>
                  <span className="text-[11px] text-[#4B5563]">
                    Content Creator
                  </span>
                </div>
                <Badge variant="waiting" className="text-[10px]">
                  En attente
                </Badge>
              </div>
              <div className="flex items-center justify-between rounded-lg py-2 px-3">
                <div className="flex items-center gap-2">
                  <span className="inline-flex h-6 w-6 items-center justify-center rounded-full bg-[#4B5563]/5 text-[10px] font-semibold text-[#4B5563]">
                    WB
                  </span>
                  <span className="text-[11px] text-[#4B5563]">
                    Website Builder
                  </span>
                </div>
                <Badge variant="waiting" className="text-[10px]">
                  En attente
                </Badge>
              </div>
              <div className="flex items-center justify-between rounded-lg py-2 px-3">
                <div className="flex items-center gap-2">
                  <span className="inline-flex h-6 w-6 items-center justify-center rounded-full bg-[#4B5563]/5 text-[10px] font-semibold text-[#4B5563]">
                    OP
                  </span>
                  <span className="text-[11px] text-[#4B5563]">Optimizer</span>
                </div>
                <Badge variant="waiting" className="text-[10px]">
                  En attente
                </Badge>
              </div>
            </div>
          </div>

          <div className="mt-2">
            <Button
              variant="primary"
              fullWidth
              disabled
              className="gap-1.5 py-2 text-xs cursor-not-allowed opacity-70"
            >
              <HiOutlineRocketLaunch className="h-3.5 w-3.5" />
              Lancer le pipeline (bientôt)
            </Button>
            <p className="mt-1 text-[10px] text-[#9CA3AF]">
              Le lancement du pipeline complet sera activé après la phase de
              clarification.
            </p>
          </div>
        </aside>

        <main className="flex-1 flex flex-col min-h-0 min-w-0 h-full overflow-hidden bg-white rounded-xl border border-[#E5E7EB] shadow-sm">
          <ClarifierPage idea={idea} token={token} />
        </main>
      </div>
    </div>
  );
}

