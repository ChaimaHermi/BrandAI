import { useEffect } from "react";
import { useClarifierAgent } from "../hooks/useClarifierAgent";
import XaiBlock from "../components/XaiBlock";
import QuestionsBlock from "../components/QuestionsBlock";
import ClarifiedBlock from "../components/ClarifiedBlock";
import RefusedBlock from "../components/RefusedBlock";

export default function ClarifierPage({ idea, token }) {
  const {
    currentStep,
    xaiSteps,
    agentMessage,
    questions,
    answers,
    setAnswers,
    clarifiedIdea,
    clarityScore,
    isReady,
    refusalData,
    startAnalysis,
    submitAnswers,
  } = useClarifierAgent(idea, token);

  useEffect(() => {
    if (idea?.description) {
      startAnalysis();
    }
  }, [idea, startAnalysis]);

  const isLoading =
    currentStep === "analyzing" || currentStep === "answering";

  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        gap: 12,
        padding: "16px 20px",
        overflowY: "auto",
        flex: 1,
      }}
    >
      {idea?.description && (
        <div
          style={{
            background: "var(--color-background-secondary)",
            border: "0.5px solid var(--color-border-tertiary)",
            borderRadius: "var(--border-radius-md)",
            padding: "10px 14px",
          }}
        >
          <div
            style={{
              fontSize: 10,
              fontWeight: 500,
              color: "var(--color-text-secondary)",
              textTransform: "uppercase",
              letterSpacing: "0.06em",
              marginBottom: 4,
            }}
          >
            Votre idée
          </div>
          <div
            style={{
              fontSize: 13,
              color: "var(--color-text-primary)",
              lineHeight: 1.5,
            }}
          >
            {idea.description}
          </div>
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

