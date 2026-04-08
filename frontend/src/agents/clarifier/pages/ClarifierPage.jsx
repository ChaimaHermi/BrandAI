import { useEffect, useRef } from "react";
import { usePipeline } from "@/context/PipelineContext";
import { useClarifierAgent } from "../hooks/useClarifierAgent";
import XaiBlock from "../components/XaiBlock";
import QuestionsBlock from "../components/QuestionsBlock";
import ClarifiedBlock from "../components/ClarifiedBlock";
import RefusedBlock from "../components/RefusedBlock";

export default function ClarifierPage() {
  const { idea, token, refetch: refetchIdea } = usePipeline();
  const xaiHideTimerRef = useRef(null);
  const {
    currentStep,
    setCurrentStep,
    xaiSteps,
    setXaiSteps,
    agentMessage,
    setAgentMessage,
    questions,
    setQuestions,
    answers,
    setAnswers,
    clarifiedIdea,
    setClarifiedIdea,
    clarityScore,
    setClarityScore,
    isReady,
    setIsReady,
    refusalData,
    setRefusalData,
    startAnalysis,
    submitAnswers,
  } = useClarifierAgent(idea, token, {
    onPersisted: refetchIdea,
    // Clarifier ends here. Market pipeline starts only by explicit user action.
    onClarified: () => {},
  });

  const scheduleHideXai = (delayMs = 50000) => {
    if (xaiHideTimerRef.current) clearTimeout(xaiHideTimerRef.current);
    xaiHideTimerRef.current = setTimeout(() => setXaiSteps([]), delayMs);
  };

  useEffect(() => {
    return () => {
      if (xaiHideTimerRef.current) clearTimeout(xaiHideTimerRef.current);
    };
  }, []);

  useEffect(() => {
    if (!idea) return;

    const status = idea.clarity_status;

    // ── CAS : idée déjà clarifiée ──────────────────
    if (status === "clarified" && idea.clarity_score != null) {
      const hasPersistedClarifiedFields =
        !!idea.clarity_solution ||
        !!idea.clarity_target_users ||
        !!idea.clarity_problem ||
        !!idea.clarity_sector ||
        !!idea.clarity_short_pitch ||
        !!idea.clarity_agent_message;

      if (!hasPersistedClarifiedFields && clarifiedIdea) {
        setCurrentStep("clarified");
        scheduleHideXai();
        return;
      }

      const restored = {
        type: "clarified",
        message: idea.clarity_agent_message || "",
        sector: idea.clarity_sector || "",
        target_users: idea.clarity_target_users || "",
        problem: idea.clarity_problem || "",
        solution_description: idea.clarity_solution || "",
        short_pitch: idea.clarity_short_pitch || "",
        score: idea.clarity_score ?? 0,
        country: idea.clarity_country || "Non précisé",
        country_code: idea.clarity_country_code || "",
        language: idea.clarity_language || "fr",
      };
      setClarifiedIdea(restored);
      setClarityScore(idea.clarity_score ?? 0);
      setIsReady(true);
      setCurrentStep("clarified");
      scheduleHideXai();
      return;
    }

    // ── CAS : idée refusée ─────────────────────────
    if (status === "refused") {
      setRefusalData({
        type: "refused",
        reason_category: idea.clarity_refused_reason ?? undefined,
        message: idea.clarity_refused_message ?? undefined,
        refusal_message: idea.clarity_refused_message ?? undefined,
      });
      setCurrentStep("refused");
      scheduleHideXai();
      return;
    }

    // ── CAS : questions déjà générées ─────────────
    if (
      status === "questions" &&
      (idea.clarity_questions?.length > 0 ||
        (idea.clarity_agent_message && idea.clarity_agent_message.trim().length > 0))
    ) {
      setQuestions(idea.clarity_questions);
      setAgentMessage(idea.clarity_agent_message || "");
      setCurrentStep("questions");
      scheduleHideXai();
      return;
    }

    // ── CAS : nouvelle idée → lancer l'analyse ─────
    if (idea.description) startAnalysis();
  }, [idea]);

  const isLoading = currentStep === "analyzing" || currentStep === "answering";

  /* ── derived progress values ─────────────────────────────────────────── */
  const progressPct = currentStep === "clarified" ? 17 : 8;

  return (
    <div className="flex flex-1 flex-col gap-3 overflow-y-auto p-5" style={{ minHeight: 0 }}>

      {/* ── Agent header card ──────────────────────────────────────────────── */}
      <div className="flex items-center gap-3 rounded-2xl border border-brand-border bg-white px-5 py-3.5 shadow-card animate-[slideUp_0.3s_ease_forwards]">
        {/* Icon bubble */}
        <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-full bg-gradient-to-br from-brand to-brand-dark shadow-pill">
          <svg width="18" height="18" viewBox="0 0 18 18" fill="none">
            <circle cx="9" cy="9" r="6" stroke="white" strokeWidth="1.4" />
            <path d="M9 6v4M9 12v.5" stroke="white" strokeWidth="1.5" strokeLinecap="round" />
          </svg>
        </div>

        {/* Title + subtitle */}
        <div className="min-w-0 flex-1">
          <p className="text-sm font-extrabold text-ink">Idea Clarifier Agent</p>
          <p className="text-xs text-ink-subtle">Analyse et structure votre idée · Étape 1 sur 6</p>
        </div>

        {/* Mini progress */}
        <div className="text-right">
          <p className="mb-1 text-2xs font-semibold text-brand">Progression pipeline</p>
          <div className="flex items-center gap-1.5">
            <div className="h-[5px] w-20 overflow-hidden rounded-full bg-brand-light">
              <div
                className="h-full rounded-full bg-gradient-to-r from-brand to-brand-dark transition-[width] duration-500"
                style={{ width: `${progressPct}%` }}
              />
            </div>
            <span className="text-xs font-bold text-brand-dark">{progressPct}%</span>
          </div>
        </div>
      </div>

      {/* ── Idée soumise ────────────────────────────────────────────────────── */}
      {idea?.description && (
        <div className="flex items-start gap-2.5 rounded-xl border border-brand-border bg-white px-4 py-3 shadow-card">
          {/* Star icon bubble */}
          <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-[9px] bg-brand-light">
            <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
              <path
                d="M7 1.5l1.2 3 3 .4-2.2 2.1.5 3L7 8.5l-2.5 1.5.5-3L2.8 5l3-.4L7 1.5z"
                stroke="currentColor"
                strokeWidth="1.1"
                strokeLinejoin="round"
                className="text-brand"
              />
            </svg>
          </div>

          <div className="min-w-0 flex-1">
            <p className="mb-1 text-2xs font-bold uppercase tracking-widest text-brand-muted">
              Idée soumise
            </p>
            <p className="text-sm font-semibold text-ink">{idea.description}</p>
          </div>

          {/* Sector pill (shown when XAI detects sector) */}
          {xaiSteps.find((s) => s.detail?.sector) && (
            <span className="shrink-0 rounded-full border border-brand-muted bg-brand-light px-2.5 py-0.5 text-2xs font-semibold text-brand-dark">
              {xaiSteps.find((s) => s.detail?.sector)?.detail.sector}
            </span>
          )}
        </div>
      )}

      <XaiBlock
        steps={xaiSteps}
        isLoading={isLoading}
        collapsed={currentStep === "clarified" || currentStep === "refused"}
      />

      {(currentStep === "questions" || currentStep === "answering") && (
        <QuestionsBlock
          agentMessage={agentMessage}
          questions={questions}
          answers={answers}
          setAnswers={setAnswers}
          onSubmit={submitAnswers}
          isLoading={currentStep === "answering"}
        />
      )}

      {currentStep === "clarified" && (
        <>
          <ClarifiedBlock data={clarifiedIdea} score={clarityScore} />
        </>
      )}

      {currentStep === "refused" && <RefusedBlock data={refusalData} />}
    </div>
  );
}
