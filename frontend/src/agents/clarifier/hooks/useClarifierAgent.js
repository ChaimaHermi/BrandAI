import { useState, useCallback, useRef } from "react";
import { useSSEStream } from "@/agents/shared/hooks/useSSEStream";
import { safeText } from "@/agents/shared/utils/safeText";

const AI_URL =
  import.meta.env.VITE_AI_URL || "http://localhost:8001/api/ai";

export function useClarifierAgent(idea, token) {
  const [currentStep, setCurrentStep] = useState("idle"); // idle | analyzing | questions | answering | clarified | refused
  const [xaiSteps, setXaiSteps] = useState([]);
  const [agentMessage, setAgentMessage] = useState("");
  const [questions, setQuestions] = useState([]);
  const [answers, setAnswers] = useState({
    problem: "",
    target: "",
    solution: "",
  });
  const [clarifiedIdea, setClarifiedIdea] = useState(null);
  const [clarityScore, setClarityScore] = useState(0);
  const [isReady, setIsReady] = useState(false);
  const [refusalData, setRefusalData] = useState(null);

  const startedRef = useRef(false);
  const { readSSEStream } = useSSEStream();

  const addXaiStep = useCallback((status, text, detail = {}) => {
    setXaiSteps((prev) => [
      ...prev,
      { id: Date.now() + Math.random(), status, text, detail },
    ]);
  }, []);

  const resolveLoadingSteps = useCallback(() => {
    setXaiSteps((prev) =>
      prev.map((step) =>
        step.status === "loading"
          ? {
              ...step,
              status: "success",
              text: step.text.replace(/\.\.\.$/, " — terminé"),
            }
          : step,
      ),
    );
  }, []);

  const startAnalysis = useCallback(async () => {
    if (!idea?.description || startedRef.current) return;
    startedRef.current = true;
    setCurrentStep("analyzing");
    setXaiSteps([]);

    try {
      await readSSEStream(
        `${AI_URL}/clarifier/start/stream`,
        {
          idea_id: idea.id,
          name: idea.name || "",
          sector: idea.sector || "",
          description: idea.description,
          target_audience: idea.target_audience || "",
        },
        (eventType, data) => {
          if (eventType === "step") {
            addXaiStep(data.status, data.message, {
              sector: data.sector || null,
              confidence: data.confidence || null,
              dimensions: data.dimensions || null,
              score: data.score || null,
              model: data.model || null,
              elapsed_ms: data.elapsed_ms || null,
            });
          }

          if (eventType === "result") {
            if (data.type === "refused") {
              setRefusalData(data);
              setCurrentStep("refused");
              return;
            }
            if (data.type === "questions") {
              setAgentMessage(safeText(data.message));
              setQuestions(data.questions || []);
              setCurrentStep("questions");
              return;
            }
            if (data.type === "clarified") {
              const score = data.score || 0;
              setClarityScore(score);
              setClarifiedIdea(data);
              if (score >= 55) setIsReady(true);
              setCurrentStep("clarified");
            }
          }

          if (eventType === "done") {
            resolveLoadingSteps();
            if (currentStep === "analyzing") {
              setCurrentStep("questions");
            }
          }
        },
        { headers: token ? { Authorization: `Bearer ${token}` } : {} },
      );
    } catch (err) {
      addXaiStep(
        "error",
        err.message.includes("Failed to fetch")
          ? "Service IA injoignable — vérifiez le port 8001"
          : `Erreur : ${err.message}`,
      );
      setCurrentStep("questions");
    }
  }, [idea, token, addXaiStep, readSSEStream, currentStep, resolveLoadingSteps]);

  const submitAnswers = useCallback(async () => {
    if (!idea || currentStep !== "questions") return;
    if (
      !answers.problem?.trim() ||
      !answers.target?.trim() ||
      !answers.solution?.trim()
    )
      return;

    setCurrentStep("answering");
    setXaiSteps((prev) => [
      ...prev,
      {
        id: Date.now(),
        status: "loading",
        text: "Analyse de vos réponses...",
        detail: {},
      },
    ]);

    try {
      await readSSEStream(
        `${AI_URL}/clarifier/answer/stream`,
        {
          idea_id: idea.id,
          name: idea.name || "",
          sector: idea.sector || "",
          description: idea.description,
          target_audience: idea.target_audience || "",
          answer_problem: answers.problem.trim(),
          answer_target: answers.target.trim(),
          answer_solution: answers.solution.trim(),
        },
        (eventType, data) => {
          if (eventType === "step") {
            addXaiStep(data.status, data.message, {
              score: data.score || null,
              model: data.model || null,
              elapsed_ms: data.elapsed_ms || null,
            });
          }

          if (eventType === "result") {
            if (data.type === "clarified") {
              const score = data.score || 0;
              setClarityScore(score);
              setClarifiedIdea(data);
              if (score >= 55) setIsReady(true);
              setCurrentStep("clarified");
            }
          }

          if (eventType === "done") {
            resolveLoadingSteps();
          }
        },
        { headers: token ? { Authorization: `Bearer ${token}` } : {} },
      );
    } catch (err) {
      addXaiStep("error", `Erreur : ${err.message}`);
      setCurrentStep("questions");
    }
  }, [
    idea,
    token,
    answers,
    currentStep,
    addXaiStep,
    readSSEStream,
    resolveLoadingSteps,
  ]);

  return {
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
  };
}

