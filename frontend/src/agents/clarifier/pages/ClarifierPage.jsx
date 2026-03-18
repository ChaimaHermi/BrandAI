import { useEffect, useRef } from "react";
import { useOutletContext } from "react-router-dom";
import { useClarifierAgent } from "../hooks/useClarifierAgent";
import XaiBlock from "../components/XaiBlock";
import QuestionsBlock from "../components/QuestionsBlock";
import ClarifiedBlock from "../components/ClarifiedBlock";
import RefusedBlock from "../components/RefusedBlock";

export default function ClarifierPage() {
  const { idea, token, refetchIdea } = useOutletContext();
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
  } = useClarifierAgent(idea, token, { onPersisted: refetchIdea });

  const scheduleHideXai = (delayMs = 50000) => {
    if (xaiHideTimerRef.current) {
      clearTimeout(xaiHideTimerRef.current);
    }
    xaiHideTimerRef.current = setTimeout(() => {
      setXaiSteps([]);
    }, delayMs);
  };

  useEffect(() => {
    return () => {
      if (xaiHideTimerRef.current) {
        clearTimeout(xaiHideTimerRef.current);
      }
    };
  }, []);

  useEffect(() => {
    if (!idea) return;

    const status = idea.clarity_status;

    // ── CAS : idée déjà clarifiée ──────────────────
    if (status === "clarified" && idea.clarity_score != null) {
      // Si on vient juste de générer via SSE, `idea.clarity_*` peut être vide
      // pendant un court moment (refetch pas encore fait). Dans ce cas,
      // ne pas écraser le résultat affiché (clarifiedIdea) par des champs vides.
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
      idea.clarity_questions?.length > 0
    ) {
      setQuestions(idea.clarity_questions);
      setAgentMessage(idea.clarity_agent_message || "");
      setCurrentStep("questions");
      scheduleHideXai();
      return;
    }

    // ── CAS : nouvelle idée → lancer l'analyse ─────
    if (idea.description) {
      startAnalysis();
    }
  }, [idea]);

  const isLoading =
    currentStep === "analyzing" || currentStep === "answering";

  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        gap: 12,
        padding: "16px 20px",
        flex: 1,
        overflowY: "auto",
        minHeight: 0,
      }}
    >
      {/* Agent header */}
      <div
        style={{
          background: "white",
          border: "0.5px solid #e8e4ff",
          borderRadius: 14,
          padding: "14px 18px",
          display: "flex",
          alignItems: "center",
          gap: 12,
          boxShadow: "0 2px 8px rgba(124,58,237,0.06)",
          animation: "slideUp 0.3s ease forwards",
        }}
      >
        <div
          style={{
            width: 42,
            height: 42,
            borderRadius: "50%",
            background: "linear-gradient(135deg,#7F77DD,#534AB7)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            flexShrink: 0,
            boxShadow: "0 3px 12px rgba(124,58,237,0.3)",
          }}
        >
          <svg width="18" height="18" viewBox="0 0 18 18" fill="none">
            <circle cx="9" cy="9" r="6" stroke="white" strokeWidth="1.4" />
            <path
              d="M9 6v4M9 12v.5"
              stroke="white"
              strokeWidth="1.5"
              strokeLinecap="round"
            />
          </svg>
        </div>
        <div style={{ flex: 1 }}>
          <div
            style={{
              fontSize: 15,
              fontWeight: 800,
              color: "#1a1040",
            }}
          >
            Idea Clarifier Agent
          </div>
          <div
            style={{
              fontSize: 11,
              color: "#9ca3af",
            }}
          >
            Analyse et structure votre idée · Étape 1 sur 7
          </div>
        </div>
        <div style={{ textAlign: "right" }}>
          <div
            style={{
              fontSize: 10,
              color: "#7F77DD",
              fontWeight: 600,
              marginBottom: 5,
            }}
          >
            Progression pipeline
          </div>
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: 6,
            }}
          >
            <div
              style={{
                width: 80,
                height: 5,
                borderRadius: 99,
                background: "#f0eeff",
                overflow: "hidden",
              }}
            >
              <div
                style={{
                  height: "100%",
                  width:
                    currentStep === "clarified"
                      ? "14%"
                      : "7%",
                  background: "linear-gradient(90deg,#7F77DD,#534AB7)",
                  borderRadius: 99,
                  transition: "width 0.5s ease",
                }}
              />
            </div>
            <span
              style={{
                fontSize: 11,
                fontWeight: 700,
                color: "#534AB7",
              }}
            >
              {currentStep === "clarified" ? "14%" : "7%"}
            </span>
          </div>
        </div>
      </div>

      {/* Idée soumise */}
      {idea?.description && (
        <div
          style={{
            background: "white",
            border: "0.5px solid #e8e4ff",
            borderRadius: 12,
            padding: "12px 16px",
            display: "flex",
            gap: 10,
            alignItems: "flex-start",
            boxShadow: "0 1px 4px rgba(124,58,237,0.04)",
          }}
        >
          <div
            style={{
              width: 32,
              height: 32,
              borderRadius: 9,
              background: "#f0eeff",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              flexShrink: 0,
            }}
          >
            <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
              <path
                d="M7 1.5l1.2 3 3 .4-2.2 2.1.5 3L7 8.5l-2.5 1.5.5-3L2.8 5l3-.4L7 1.5z"
                stroke="#7F77DD"
                strokeWidth="1.1"
                strokeLinejoin="round"
              />
            </svg>
          </div>
          <div
            style={{
              flex: 1,
            }}
          >
            <div
              style={{
                fontSize: 10,
                fontWeight: 700,
                color: "#AFA9EC",
                textTransform: "uppercase",
                letterSpacing: "0.08em",
                marginBottom: 3,
              }}
            >
              Idée soumise
            </div>
            <div
              style={{
                fontSize: 13,
                fontWeight: 600,
                color: "#1a1040",
              }}
            >
              {idea.description}
            </div>
          </div>
          {xaiSteps.find((s) => s.detail?.sector) && (
            <div
              style={{
                padding: "3px 10px",
                background: "#f0eeff",
                border: "0.5px solid #AFA9EC",
                borderRadius: 99,
                fontSize: 10,
                fontWeight: 600,
                color: "#534AB7",
                flexShrink: 0,
              }}
            >
              {xaiSteps.find((s) => s.detail?.sector)?.detail.sector}
            </div>
          )}
        </div>
      )}

      <XaiBlock
        steps={xaiSteps}
        isLoading={isLoading}
        collapsed={
          currentStep === "clarified" || currentStep === "refused"
        }
      />

      {(currentStep === "questions" ||
        currentStep === "answering") && (
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
        <ClarifiedBlock data={clarifiedIdea} score={clarityScore} />
      )}

      {currentStep === "refused" && <RefusedBlock data={refusalData} />}
    </div>
  );
}

