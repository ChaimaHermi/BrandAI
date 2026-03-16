import React, { useState, useEffect, useMemo, useRef } from "react";
import { useParams, useNavigate, Link } from "react-router-dom";
import {
  HiOutlineArrowLeft,
  HiOutlineChatBubbleLeftRight,
  HiOutlineTrash,
  HiOutlineCheckCircle,
  HiOutlineLightBulb,
} from "react-icons/hi2";
import { Navbar } from "../components/layout/Navbar";
import { Card } from "../components/ui/Card";
import { Button } from "../components/ui/Button";
import { Loader } from "../components/ui/Loader";
import { Badge } from "../components/ui/Badge";
import { ChatMessage } from "../components/chat/ChatMessage";
import { TypingIndicator } from "../components/chat/TypingIndicator";
import { AgentAvatar } from "../components/chat/AgentAvatar";
import { useChatStream } from "../hooks/useChatStream";
import {
  apiGetIdea,
  apiDeleteIdea,
  getErrorMessage,
} from "../services/ideaApi";
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

export function IdeaDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { token, user } = useAuth();
  const [idea, setIdea] = useState(null);
  const [loading, setLoading] = useState(true);
  const [notFound, setNotFound] = useState(false);
  const [fetchError, setFetchError] = useState("");
  const [deleteConfirm, setDeleteConfirm] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [activeAgent, setActiveAgent] = useState("idea");
  const [descriptionExpanded, setDescriptionExpanded] = useState(false);
  const { messages, isStreaming, sendMessage } = useChatStream();
  const hasInjectedInitial = useRef(false);
  const messagesEndRef = useRef(null);

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

  const lastClarifierMessage = useMemo(
    () =>
      [...messages]
        .reverse()
        .find(
          (m) =>
            m.role === "agent" &&
            (m.agentType === "idea_clarifier" || !m.agentType),
        ),
    [messages],
  );

  const clarityScore = lastClarifierMessage?.structured?.clarity_score ?? null;
  const canLaunchPipeline = typeof clarityScore === "number" && clarityScore >= 80;

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
          <Button
            variant="outline"
            className="mt-4"
            onClick={() => navigate("/dashboard")}
          >
            Retour au tableau de bord
          </Button>
        </main>
      </div>
    );
  }

  const currentStep = 2;

  const description = idea.description || "—";
  const descriptionLong = description.length > 120;
  const handleSend = (event) => {
    event.preventDefault();
  };
  return (
    <div className="flex min-h-screen flex-col bg-white">
      <Navbar variant="app" />
      <div className="mx-auto flex w-full max-w-[1280px] flex-1 flex-col px-4 md:px-6">
        <header className="border-b border-[#E5E7EB] bg-white pb-2 pt-2">
          <div className="flex items-center justify-between gap-1">
            <Link
              to="/dashboard"
              className="flex shrink-0 items-center gap-1 text-xs font-medium text-[#6B7280] hover:text-[#7C3AED]"
              aria-label="Retour au tableau de bord"
            >
              <HiOutlineArrowLeft className="h-4 w-4" />
              Retour
            </Link>
            <div className="flex min-w-0 flex-1 flex-col items-center justify-center px-1">
              <p className="text-[11px] font-medium text-[#6B7280]">
                Étape {currentStep} sur 3
              </p>
              <div className="mt-1 w-full max-w-md">
                <StepFlow currentStep={currentStep} />
              </div>
            </div>
            <div className="w-[64px] shrink-0 sm:w-[80px]" aria-hidden />
          </div>
          <div className="mt-2 flex flex-wrap items-center gap-1.5">
            <h1 className="text-sm font-semibold text-[#111827]">
              {idea.name}
            </h1>
            <span className="rounded-full bg-[#F3F4F6] px-2 py-0.5 text-[11px] font-medium text-[#6B7280]">
              {idea.sector}
            </span>
          </div>
        </header>
        {fetchError && (
          <div className="mt-4">
            <div className="rounded-[10px] border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-600">
              {fetchError}
            </div>
          </div>
        )}
        <div className="flex min-h-0 flex-1 flex-col gap-6 py-6 lg:flex-row lg:items-start">
          <aside className="flex w-full shrink-0 flex-col gap-4 rounded-[16px] border border-[#E5E7EB] bg-[#FAFAFA] p-4 lg:w-[280px] lg:self-start">
            <div className="flex items-center gap-2">
              <div className="flex h-8 w-8 items-center justify-center rounded-xl bg-[#111827] text-xs font-bold text-white">
                BA
              </div>
              <div className="min-w-0">
                <p className="text-xs font-semibold uppercase tracking-wide text-[#6B7280]">
                  BrandAI
                </p>
                <p className="truncate text-[11px] text-[#9CA3AF]">
                  Pipeline d&apos;agents
                </p>
              </div>
            </div>

            <Card hover={false} className="border border-[#E5E7EB] bg-white p-4">
              <p className="text-xs font-medium text-[#6B7280]">Votre idée</p>
              <p className="mt-1 text-sm font-semibold text-[#111827]">
                {idea.name}
              </p>
              <Badge className="mt-1 text-[10px]">{idea.sector}</Badge>
              <p className="mt-3 text-[11px] font-medium text-[#6B7280]">
                Description soumise
              </p>
              <div className="mt-1.5 rounded-[10px] border border-[#E5E7EB] bg-[#F9FAFB] p-2.5 text-xs text-[#374151]">
                <p
                  className={
                    descriptionExpanded || !descriptionLong
                      ? "whitespace-pre-wrap break-words"
                      : "line-clamp-3 whitespace-pre-wrap break-words"
                  }
                >
                  {description}
                </p>
                {descriptionLong && (
                  <button
                    type="button"
                    onClick={() => setDescriptionExpanded((e) => !e)}
                    className="mt-1.5 text-[11px] font-medium text-[#7C3AED] hover:underline"
                  >
                    {descriptionExpanded ? "Voir moins" : "Voir plus"}
                  </button>
                )}
              </div>
              <p className="mt-3 text-[11px] text-[#6B7280]">
                Soumise le {formatDate(idea.created_at)}
              </p>
            </Card>

            <div className="mt-1 space-y-2">
              <p className="text-[11px] font-medium uppercase tracking-wide text-[#6B7280]">
                Étapes du pipeline
              </p>
              <div className="space-y-1.5 text-xs">
                <div className="flex items-center justify-between rounded-[10px] bg-[#F5F3FF] px-2.5 py-2">
                  <div className="flex items-center gap-2">
                    <AgentAvatar agentType="idea_clarifier" size={24} />
                    <span className="text-[11px] font-medium text-[#4B5563]">
                      Idea Clarifier
                    </span>
                  </div>
                  <Badge variant="violet" className="text-[10px]">
                    En cours
                  </Badge>
                </div>
                <div className="flex items-center justify-between rounded-[10px] px-2.5 py-1.5">
                  <div className="flex items-center gap-2">
                    <AgentAvatar agentType="idea_enhancer" size={22} />
                    <span className="text-[11px] text-[#4B5563]">
                      Idea Enhancer
                    </span>
                  </div>
                  <Badge variant="waiting" className="text-[10px]">
                    En attente
                  </Badge>
                </div>
                <div className="flex items-center justify-between rounded-[10px] px-2.5 py-1.5">
                  <div className="flex items-center gap-2">
                    <AgentAvatar agentType="market_analysis" size={22} />
                    <span className="text-[11px] text-[#4B5563]">
                      Market Analysis
                    </span>
                  </div>
                  <Badge variant="waiting" className="text-[10px]">
                    En attente
                  </Badge>
                </div>
                <div className="flex items-center justify-between rounded-[10px] px-2.5 py-1.5">
                  <div className="flex items-center gap-2">
                    <AgentAvatar agentType="brand_identity" size={22} />
                    <span className="text-[11px] text-[#4B5563]">
                      Brand Identity
                    </span>
                  </div>
                  <Badge variant="waiting" className="text-[10px]">
                    En attente
                  </Badge>
                </div>
                <div className="flex items-center justify-between rounded-[10px] px-2.5 py-1.5">
                  <div className="flex items-center gap-2">
                    <AgentAvatar agentType="content_creator" size={22} />
                    <span className="text-[11px] text-[#4B5563]">
                      Content Creator
                    </span>
                  </div>
                  <Badge variant="waiting" className="text-[10px]">
                    En attente
                  </Badge>
                </div>
                <div className="flex items-center justify-between rounded-[10px] px-2.5 py-1.5">
                  <div className="flex items-center gap-2">
                    <AgentAvatar agentType="website_builder" size={22} />
                    <span className="text-[11px] text-[#4B5563]">
                      Website Builder
                    </span>
                  </div>
                  <Badge variant="waiting" className="text-[10px]">
                    En attente
                  </Badge>
                </div>
                <div className="flex items-center justify-between rounded-[10px] px-2.5 py-1.5">
                  <div className="flex items-center gap-2">
                    <AgentAvatar agentType="optimizer" size={22} />
                    <span className="text-[11px] text-[#4B5563]">
                      Optimizer
                    </span>
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
                disabled={!canLaunchPipeline || isStreaming}
                className="gap-1.5 py-2 text-xs"
              >
                Lancer le pipeline complet
              </Button>
              {!canLaunchPipeline && (
                <p className="mt-1 text-[10px] text-[#9CA3AF]">
                  Disponible une fois la clarté de l&apos;idée ≥ 80/100.
                </p>
              )}
            </div>

            <div className="mt-1 border-t border-[#E5E7EB] pt-3">
              {!deleteConfirm ? (
                <Button
                  variant="outline"
                  className="w-full border-red-200 text-xs text-red-600 hover:border-red-300 hover:bg-red-50"
                  onClick={() => setDeleteConfirm(true)}
                >
                  <HiOutlineTrash className="h-3.5 w-3.5" />
                  Supprimer l&apos;idée
                </Button>
              ) : (
                <div className="rounded-[10px] border border-red-200 bg-red-50 p-3 text-xs">
                  <p className="font-medium text-red-800">
                    Êtes-vous sûr de vouloir supprimer ?
                  </p>
                  <div className="mt-2 flex gap-2">
                    <Button
                      variant="outline"
                      className="flex-1 border-red-300 text-red-600"
                      onClick={() => setDeleteConfirm(false)}
                      disabled={deleting}
                    >
                      Annuler
                    </Button>
                    <Button
                      className="flex-1 bg-red-600 text-white hover:bg-red-700"
                      onClick={handleDelete}
                      disabled={deleting}
                    >
                      {deleting ? "Suppression..." : "Supprimer"}
                    </Button>
                  </div>
                </div>
              )}
            </div>
          </aside>

          <main className="flex min-h-0 min-w-0 flex-1 flex-col rounded-[16px] border border-[#E5E7EB] bg-white">
            <div className="flex items-center justify-between border-b border-[#E5E7EB] px-4 py-3">
              <div className="flex items-center gap-3">
                <AgentAvatar agentType="idea_clarifier" size={32} />
                <div>
                  <p className="text-sm font-semibold text-[#111827]">
                    Idea Clarifier Agent
                  </p>
                  <p className="text-[11px] text-[#6B7280]">
                    Clarifie votre idée pas à pas avant de lancer tout le pipeline.
                  </p>
                </div>
              </div>
              <Badge className="text-[10px]">IA</Badge>
            </div>

            <div className="flex min-h-0 flex-1 flex-col">
              <div className="flex-1 space-y-4 overflow-y-auto px-4 py-4">
                {messages.length === 0 && (
                  <div className="flex h-full flex-col items-center justify-center text-center text-xs text-[#6B7280]">
                    <HiOutlineChatBubbleLeftRight
                      className="mb-2 h-6 w-6 text-[#9CA3AF]"
                      aria-hidden
                    />
                    <p>
                      Votre description vient d&apos;être envoyée à l&apos;agent
                      BrandAI.
                    </p>
                    <p className="mt-0.5">
                      Il va analyser votre idée puis vous poser quelques questions
                      ciblées.
                    </p>
                  </div>
                )}

                {messages.map((msg) => (
                  <ChatMessage key={msg.id} message={msg} currentUser={user} />
                ))}

                {isStreaming && <TypingIndicator />}

                <div ref={messagesEndRef} />
              </div>

              <form
                onSubmit={handleSend}
                className="border-t border-[#E5E7EB] bg-[#F9FAFB] px-4 py-3"
              >
                <div className="rounded-[12px] border border-[#E5E7EB] bg-white px-3 py-2">
                  <textarea
                    rows={2}
                    placeholder="Répondez aux questions de l’agent ou précisez votre idée…"
                    className="max-h-40 w-full resize-none border-none text-xs text-[#111827] outline-none placeholder:text-[#9CA3AF]"
                    onKeyDown={(e) => {
                      if (e.key === "Enter" && !e.shiftKey) {
                        e.preventDefault();
                        const value = e.currentTarget.value;
                        if (value.trim()) {
                          sendMessage(value, "idea_clarifier");
                          e.currentTarget.value = "";
                        }
                      }
                    }}
                    disabled={isStreaming}
                  />
                  <div className="mt-1 flex items-center justify-between">
                    <p className="text-[10px] text-[#9CA3AF]">
                      Entrée = envoyer · Shift+Entrée = nouvelle ligne
                    </p>
                    <Button
                      type="submit"
                      variant="primary"
                      className="h-7 px-3 text-[11px]"
                      disabled={isStreaming}
                    >
                      Envoyer
                    </Button>
                  </div>
                </div>
              </form>
            </div>
          </main>
        </div>
      </div>
    </div>
  );
}

export default IdeaDetail;
