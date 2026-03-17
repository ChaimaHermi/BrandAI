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
import { ChatMessage } from "@/agents/shared/components/ChatMessage";
import { TypingIndicator } from "@/agents/shared/components/TypingIndicator";
import { AgentAvatar } from "@/agents/shared/components/AgentAvatar";
import { AgentStatusBar } from "@/agents/shared/components/AgentStatusBar";
import { useClarifierChat } from "@/agents/clarifier/hooks/useClarifierChat";
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
  const [inputText, setInputText] = useState("");
  const [isAtBottom, setIsAtBottom] = useState(true);
  const {
    messages,
    isStreaming,
    clarityScore,
    isReady,
    isRefused,
    agentSteps,
    startConversation,
    sendAnswer,
  } = useClarifierChat(idea, token);
  const messagesEndRef = useRef(null);
  const messagesContainerRef = useRef(null);

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

  useEffect(() => {
    if (idea && idea.status === "pending") {
      startConversation();
    }
  }, [idea?.id]);

  useEffect(() => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [messages]);

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
  const handleSend = (event) => {
    event.preventDefault();
    if (!inputText.trim() || isStreaming) return;
    sendAnswer(inputText.trim());
    setInputText("");
  };
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
                  <AgentAvatar agentType="idea_clarifier" size={24} />
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
                  <AgentAvatar agentType="idea_enhancer" size={22} />
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
                  <AgentAvatar agentType="market_analysis" size={22} />
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
                  <AgentAvatar agentType="brand_identity" size={22} />
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
                  <AgentAvatar agentType="content_creator" size={22} />
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
                  <AgentAvatar agentType="website_builder" size={22} />
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
                  <AgentAvatar agentType="optimizer" size={22} />
                  <span className="text-[11px] text-[#4B5563]">Optimizer</span>
                </div>
                <Badge variant="waiting" className="text-[10px]">
                  En attente
                </Badge>
              </div>
            </div>
          </div>

          <div className="mt-2">
            {isRefused ? (
              <Button
                variant="primary"
                fullWidth
                disabled
                className="gap-1.5 py-2 text-xs cursor-not-allowed bg-red-500 opacity-70 hover:bg-red-500"
              >
                ✗ Pipeline bloqué — idée refusée
              </Button>
            ) : (
              <>
                <Button
                  variant="primary"
                  fullWidth
                  disabled={!isReady || isStreaming}
                  className="gap-1.5 py-2 text-xs"
                >
                  <HiOutlineRocketLaunch className="h-3.5 w-3.5" />
                  {isReady
                    ? "Lancer le pipeline complet"
                    : `Affiner encore (${clarityScore || 0}/100)`}
                </Button>
                {!isReady && (
                  <p className="mt-1 text-[10px] text-[#9CA3AF]">
                    Disponible une fois la clarté de l&apos;idée ≥ 80/100.
                  </p>
                )}
              </>
            )}
          </div>
        </aside>

        <main className="flex-1 flex flex-col min-h-0 min-w-0 h-full overflow-hidden bg-white rounded-xl border border-[#E5E7EB] shadow-sm">
          <header className="p-4 border-b border-[#E5E7EB] shrink-0">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <AgentAvatar agentType="idea_clarifier" size={32} />
                <div>
                  <p className="text-sm font-semibold text-[#111827]">
                    Idea Clarifier Agent
                  </p>
                  <p className="text-[11px] text-[#6B7280]">
                    Clarifie votre idée pas à pas avant de lancer tout le
                    pipeline.
                  </p>
                </div>
              </div>
              <Badge className="text-[10px]">IA</Badge>
            </div>
          </header>

          <AgentStatusBar steps={agentSteps} />

          <div className="relative flex-1 flex flex-col min-h-0 overflow-hidden">
            <div
              ref={messagesContainerRef}
              className="flex-1 overflow-y-auto p-4 space-y-2 min-h-0"
              onScroll={() => {
                const el = messagesContainerRef.current;
                if (!el) return;
                const atBottom =
                  el.scrollTop + el.clientHeight >= el.scrollHeight - 32;
                setIsAtBottom(atBottom);
              }}
            >
              {messages.length === 0 && (
                <div className="flex min-h-[200px] flex-col items-center justify-center text-center text-xs text-[#6B7280]">
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
                <ChatMessage key={msg.id} message={msg} user={user} />
              ))}

              {isStreaming && !messages.some((m) => m.isStreaming) && (
                <TypingIndicator />
              )}

              <div ref={messagesEndRef} />
            </div>

            {!isAtBottom && messages.length > 0 && (
              <button
                type="button"
                onClick={() =>
                  messagesEndRef.current?.scrollIntoView({
                    behavior: "smooth",
                  })
                }
                className="absolute bottom-20 right-6 rounded-full bg-white/90 px-3 py-1 text-[11px] font-medium text-[#4B5563] shadow-md ring-1 ring-[#E5E7EB] hover:bg-[#F3F4F6]"
              >
                Revenir en bas
              </button>
            )}

            <div className="border-t border-[#E5E7EB] p-4 bg:white shrink-0">
              <form onSubmit={handleSend}>
                <div className="rounded-lg border border-[#E5E7EB] bg-[#F9FAFB] px-3 py-1">
                  <textarea
                    value={inputText}
                    onChange={(e) => setInputText(e.target.value)}
                    placeholder="Répondez aux questions de l'agent ou précisez votre idée…"
                    className="w-full min-h-[10px] max-h-[30px] resize-none border-none bg-transparent text-sm px-3 py-1 text-[#111827] outline-none placeholder:text-[#9CA3AF]"
                    onKeyDown={(e) => {
                      if (e.key === "Enter" && !e.shiftKey) {
                        e.preventDefault();
                        handleSend(e);
                      }
                    }}
                    disabled={isStreaming}
                  />
                  <div className="mt-1 flex items-center justify-between">
                    <p className="text-[10px] text-[#9CA3AF]">
                      Entrée = envoyer · Shift+Entrée = nouvelle ligne
                    </p>
                    <button
                      type="submit"
                      disabled={isStreaming}
                      className="h-9 px-4 text-sm rounded-lg bg-purple-600 text-white hover:bg-purple-700 transition disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      Envoyer
                    </button>
                  </div>
                </div>
              </form>
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}

