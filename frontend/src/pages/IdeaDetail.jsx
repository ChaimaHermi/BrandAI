import React, { useState, useEffect, useMemo } from "react";
import { useParams, useNavigate, Link } from "react-router-dom";
import {
  HiOutlineArrowLeft,
  HiOutlineSparkles,
  HiOutlineChatBubbleLeftRight,
  HiOutlineArrowRight,
  HiOutlineTrash,
  HiOutlineCheckCircle,
  HiOutlineLightBulb,
  HiOutlineRocketLaunch,
} from "react-icons/hi2";
import { Navbar } from "../components/layout/Navbar";
import { Card } from "../components/ui/Card";
import { Button } from "../components/ui/Button";
import { Loader } from "../components/ui/Loader";
import { AgentTimeline } from "../components/agents/AgentTimeline";
import { ResultDisplay } from "../components/agents/ResultDisplay";
import { apiGetIdea, apiDeleteIdea, getErrorMessage } from "../services/ideaApi";
import { useAuth } from "../hooks/useAuth";
import { AGENTS, TECHMENTOR_RESULTS } from "../data/mockData";

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
    { key: 2, label: "Affiner avec l'agent", Icon: HiOutlineChatBubbleLeftRight },
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
                  isActive ? "text-[#7C3AED]" : isCompleted ? "text-[#6B7280]" : "text-[#9CA3AF]"
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

export function IdeaDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { token } = useAuth();
  const [idea, setIdea] = useState(null);
  const [loading, setLoading] = useState(true);
  const [notFound, setNotFound] = useState(false);
  const [fetchError, setFetchError] = useState("");
  const [deleteConfirm, setDeleteConfirm] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [showPipeline, setShowPipeline] = useState(false);
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
          if (msg.includes("404") || msg.toLowerCase().includes("introuvable")) {
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
    return () => { cancelled = true; };
  }, [id, token]);

  // Hooks must be called unconditionally (before any early return)
  const statuses = useMemo(() => getMockStatuses(), []);
  const results = useMemo(() => buildMockResults(idea), [idea]);
  const currentData = results[activeAgent];
  const currentStatus = statuses[activeAgent] || "waiting";

  const handleDelete = async () => {
    if (!id || !token) return;
    setDeleting(true);
    try {
      await apiDeleteIdea(id, token);
      navigate("/dashboard", { replace: true });
    } catch (err) {
      setDeleting(false);
      setFetchError(getErrorMessage(err));
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-white">
        <Navbar variant="app" />
        <main className="flex min-h-[60vh] items-center justify-center">
          <Loader className="h-10 w-10" />
        </main>
      </div>
    );
  }

  if (notFound || !idea) {
    return (
      <div className="min-h-screen bg-white">
        <Navbar variant="app" />
        <main className="mx-auto max-w-[560px] px-4 py-12 text-center">
          {fetchError && (
            <div className="mb-4 rounded-[8px] border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-600">
              {fetchError}
            </div>
          )}
          <p className="text-[#6B7280]">
            {notFound
              ? "Cette idée n'existe pas ou a été supprimée."
              : "Nous n'avons pas pu charger cette idée."}
          </p>
          <Button variant="outline" className="mt-4" onClick={() => navigate("/dashboard")}>
            Retour au tableau de bord
          </Button>
        </main>
      </div>
    );
  }

  const isPending = idea.status === "pending";

  // ─── STATE 2: running or done — placeholder ─────────────────────────────
  if (idea.status === "running" || idea.status === "done") {
    return (
      <div className="min-h-screen bg-white">
        <Navbar variant="app" />
        <main className="flex min-h-[60vh] flex-col items-center justify-center px-4 py-12">
          <Loader className="h-12 w-12 text-[#7C3AED]" />
          <p className="mt-4 font-medium text-[#111827]">Pipeline en cours d&apos;exécution...</p>
          <p className="mt-1 text-sm text-[#6B7280]">Les agents travaillent sur votre projet</p>
        </main>
      </div>
    );
  }

  if (idea.status === "error") {
    return (
      <div className="min-h-screen bg-white">
        <Navbar variant="app" />
        <main className="flex min-h-[60vh] flex-col items-center justify-center px-4 py-12 text-center">
          <p className="font-medium text-[#111827]">Une erreur s&apos;est produite lors du pipeline</p>
          <p className="mt-1 text-sm text-[#6B7280]">Veuillez réessayer ou contacter le support.</p>
          <Button variant="outline" className="mt-4" onClick={() => navigate("/dashboard")}>
            Retour au tableau de bord
          </Button>
        </main>
      </div>
    );
  }

  const currentStep = showPipeline ? 3 : 2;

  const description = idea.description || "—";
  const descriptionLong = description.length > 120;
  const renderLeftColumn = () => (
    <aside className="flex w-full shrink-0 flex-col gap-4 rounded-[10px] border border-[#E5E7EB] bg-[#FAFAFA] p-4 lg:w-[300px] lg:self-start">
      <Card hover={false} className="border border-[#E5E7EB] bg-white p-5">
        <h2 className="text-sm font-semibold uppercase tracking-wide text-[#6B7280]">Votre idée</h2>
        <p className="mt-2 font-semibold text-[#111827]">{idea.name}</p>
        <p className="mt-0.5 text-sm text-[#6B7280]">{idea.sector}</p>
        <p className="mt-3 text-xs text-[#6B7280]">Public cible:</p>
        <p className="mt-0.5 text-sm text-[#111827]">{idea.target_audience || "—"}</p>
        <hr className="my-4 border-[#E5E7EB]" />
        <p className="text-xs font-medium text-[#6B7280]">Description soumise:</p>
        <div className="mt-1.5 rounded-[10px] border border-[#E5E7EB] bg-[#F9FAFB] p-3 text-sm text-[#374151]">
          <p className={descriptionExpanded || !descriptionLong ? "whitespace-pre-wrap break-words" : "line-clamp-3 whitespace-pre-wrap break-words"}>
            {description}
          </p>
          {descriptionLong && (
            <button
              type="button"
              onClick={() => setDescriptionExpanded((e) => !e)}
              className="mt-2 text-xs font-medium text-[#7C3AED] hover:underline"
            >
              {descriptionExpanded ? "Voir moins" : "Voir plus"}
            </button>
          )}
        </div>
        <hr className="my-4 border-[#E5E7EB]" />
        <p className="text-xs text-[#6B7280]">Soumise le {formatDate(idea.created_at)}</p>
        <hr className="my-4 border-[#E5E7EB]" />
        {!deleteConfirm ? (
          <Button
            variant="outline"
            className="w-full border-red-200 text-red-600 hover:border-red-300 hover:bg-red-50"
            onClick={() => setDeleteConfirm(true)}
          >
            <HiOutlineTrash className="h-4 w-4" />
            Supprimer
          </Button>
        ) : (
          <div className="rounded-[10px] border border-red-200 bg-red-50 p-3 text-sm">
            <p className="font-medium text-red-800">Êtes-vous sûr ?</p>
            <div className="mt-2 flex gap-2">
              <Button variant="outline" className="flex-1 border-red-300 text-red-600" onClick={() => setDeleteConfirm(false)} disabled={deleting}>
                Annuler
              </Button>
              <Button className="flex-1 bg-red-600 text-white hover:bg-red-700" onClick={handleDelete} disabled={deleting}>
                {deleting ? "Suppression..." : "Supprimer"}
              </Button>
            </div>
          </div>
        )}
      </Card>
    </aside>
  );

  // ─── STATE 1b: pending + showPipeline — vue pipeline statique ────────────
  if (showPipeline) {
    return (
      <div className="flex min-h-screen flex-col bg-white">
        <Navbar variant="app" />
        <div className="mx-auto flex w-full max-w-[1280px] flex-1 flex-col px-4 md:px-6">
          <header className="border-b border-[#E5E7EB] bg-white pb-2 pt-2">
            <div className="flex items-center justify-between gap-1">
              <Link to="/dashboard" className="flex shrink-0 items-center gap-1 text-xs font-medium text-[#6B7280] hover:text-[#7C3AED]">
                <HiOutlineArrowLeft className="h-4 w-4" />
                Retour
              </Link>
              <div className="flex min-w-0 flex-1 flex-col items-center justify-center px-1">
                <p className="text-[11px] font-medium text-[#6B7280]">Étape {currentStep} sur 3</p>
                <div className="mt-1 w-full max-w-md">
                  <StepFlow currentStep={currentStep} />
                </div>
              </div>
              <button
                type="button"
                onClick={() => setShowPipeline(false)}
                className="shrink-0 text-xs font-medium text-[#6B7280] hover:text-[#7C3AED]"
              >
                Retour à l&apos;agent
              </button>
            </div>
            <div className="mt-2 flex flex-wrap items-center gap-1.5">
              <h1 className="text-sm font-semibold text-[#111827]">{idea.name}</h1>
              <span className="rounded-full bg-[#EDE9FE] px-2 py-0.5 text-[11px] font-medium text-[#7C3AED]">Pipeline</span>
            </div>
          </header>
          {fetchError && (
            <div className="mt-4">
              <div className="rounded-[10px] border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-600">{fetchError}</div>
            </div>
          )}
          <div className="flex min-h-0 flex-1 flex-col gap-6 py-6 lg:flex-row lg:items-start">
            <aside className="flex w-full shrink-0 flex-col rounded-[10px] border border-[#E5E7EB] bg-[#FAFAFA] p-3 lg:w-[280px] lg:self-start">
              <p className="mb-2 text-[11px] font-medium uppercase tracking-wider text-[#6B7280]">Agents du pipeline</p>
              <AgentTimeline agents={AGENTS} agentStatuses={statuses} activeId={activeAgent} onSelect={setActiveAgent} />
            </aside>
            <main className="min-h-0 min-w-0 flex-1 overflow-auto">
              <ResultDisplay agentId={activeAgent} data={currentData} status={currentStatus} />
            </main>
          </div>
        </div>
      </div>
    );
  }

  // ─── STATE 1a: pending — chat interface ─────────────────────────────────
  return (
    <div className="flex min-h-screen flex-col bg-white">
      <Navbar variant="app" />
      <div className="mx-auto flex w-full max-w-[1280px] flex-1 flex-col px-4 md:px-6">
        <header className="border-b border-[#E5E7EB] bg-white pb-2 pt-2">
          <div className="flex items-center justify-between gap-1">
            <Link to="/dashboard" className="flex shrink-0 items-center gap-1 text-xs font-medium text-[#6B7280] hover:text-[#7C3AED]" aria-label="Retour au tableau de bord">
              <HiOutlineArrowLeft className="h-4 w-4" />
              Retour
            </Link>
            <div className="flex min-w-0 flex-1 flex-col items-center justify-center px-1">
              <p className="text-[11px] font-medium text-[#6B7280]">Étape {currentStep} sur 3</p>
              <div className="mt-1 w-full max-w-md">
                <StepFlow currentStep={currentStep} />
              </div>
            </div>
            <div className="w-[64px] shrink-0 sm:w-[80px]" aria-hidden />
          </div>
          <div className="mt-2 flex flex-wrap items-center gap-1.5">
            <h1 className="text-sm font-semibold text-[#111827]">{idea.name}</h1>
            <span className="rounded-full bg-[#F3F4F6] px-2 py-0.5 text-[11px] font-medium text-[#6B7280]">{idea.sector}</span>
          </div>
        </header>
        {fetchError && (
          <div className="mt-4">
            <div className="rounded-[10px] border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-600">{fetchError}</div>
          </div>
        )}
        <div className="flex min-h-0 flex-1 flex-col gap-6 py-6 lg:flex-row lg:items-start">
          {renderLeftColumn()}
          <main className="flex min-h-0 min-w-0 flex-1 flex-col gap-6 overflow-auto">
            <Card hover={false} className="shrink-0 border border-[#E5E7EB] bg-white p-4">
              <div className="flex items-center gap-2">
                <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-lg bg-[#7C3AED] text-white">
                  <HiOutlineSparkles className="h-3.5 w-3.5" aria-hidden />
                </span>
                <div className="min-w-0">
                  <h3 className="text-sm font-semibold text-[#111827]">Idea Enhancer Agent</h3>
                  <p className="text-xs text-[#6B7280]">Posez vos questions pour affiner votre idée</p>
                </div>
              </div>
              <div className="relative mt-3 min-h-[180px] rounded-[8px] border border-[#E5E7EB] bg-[#F9FAFB]">
                <div className="flex min-h-[180px] flex-col items-center justify-center px-3 py-4 text-center">
                  <HiOutlineChatBubbleLeftRight className="h-6 w-6 text-[#9CA3AF]" aria-hidden />
                  <p className="mt-1.5 text-xs font-medium text-[#374151]">L&apos;agent est prêt à affiner votre idée</p>
                  <p className="mt-0.5 text-[11px] text-[#6B7280]">Il analysera votre description et vous posera des questions</p>
                </div>
                <div className="absolute inset-0 flex flex-col items-center justify-center rounded-[8px] bg-white/80 backdrop-blur-[2px]" aria-hidden>
                  <p className="text-center text-sm font-medium text-[#374151]">Disponible après intégration de l&apos;agent IA</p>
                  <p className="mt-0.5 text-[11px] text-[#6B7280]">En cours de développement — Sprint 2</p>
                </div>
              </div>
              <div className="mt-3 flex items-center gap-2 border-t border-[#E5E7EB] pt-2.5">
                <input
                  type="text"
                  placeholder="Votre message..."
                  disabled
                  className="min-w-0 flex-1 rounded-[8px] border border-[#E5E7EB] bg-[#F3F4F6] px-3 py-2 text-xs text-[#9CA3AF] placeholder:text-[#9CA3AF] cursor-not-allowed"
                />
                <button type="button" disabled className="flex h-8 w-8 shrink-0 items-center justify-center rounded-[8px] bg-[#E5E7EB] text-[#9CA3AF] cursor-not-allowed" aria-label="Envoyer">
                  <HiOutlineArrowRight className="h-4 w-4" />
                </button>
              </div>
            </Card>
            <section className="shrink-0 rounded-[10px] border border-[#E5E7EB] bg-[#FAFAFA] p-4">
              <h3 className="text-xs font-semibold text-[#111827]">Étape suivante</h3>
              <p className="mt-0.5 text-[11px] text-[#6B7280]">
                Analyse de marché · identité de marque · contenus · site web · stratégie marketing
              </p>
              <Button
                variant="primary"
                fullWidth
                className="mt-3 gap-1.5 py-2.5 text-sm"
                onClick={() => setShowPipeline(true)}
              >
                <HiOutlineRocketLaunch className="h-4 w-4" />
                Lancer le pipeline IA
              </Button>
            </section>
          </main>
        </div>
      </div>
    </div>
  );
}

export default IdeaDetail;
