import { useEffect, useState, useCallback, useRef } from "react";
import { useSSEStream } from "@/agents/shared/hooks/useSSEStream";
import { saveClarifierResult } from "../api/clarifier.api";

const AI_URL =
  import.meta.env.VITE_AI_URL || "http://localhost:8001/api/ai";

export function useClarifierAgent(idea, token, options = {}) {
  const [currentStep, setCurrentStep] = useState("idle"); // idle | analyzing | questions | answering | clarified | refused
  const [xaiSteps, setXaiSteps] = useState([]);
  const xaiStepsRef = useRef([]);
  const [agentMessage, setAgentMessage] = useState("");
  const [questions, setQuestions] = useState([]);
  const [detectedSector, setDetectedSector] = useState("");
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

  // Assurer la synchro de la ref quand `setXaiSteps` est modifié depuis l'extérieur.
  useEffect(() => {
    xaiStepsRef.current = xaiSteps;
  }, [xaiSteps]);

  const addXaiStep = useCallback((status, text, detail = {}) => {
    setXaiSteps((prev) => {
      const next = [
        ...prev,
        { id: Date.now() + Math.random(), status, text, detail },
      ];
      xaiStepsRef.current = next;
      return next;
    });
  }, []);

  const resolveLoadingSteps = useCallback(() => {
    setXaiSteps((prev) => {
      const next = prev.map((step) =>
        step.status === "loading"
          ? {
              ...step,
              status: "success",
              text: step.text.replace(/\.\.\.$/, " — terminé"),
            }
          : step,
      );
      xaiStepsRef.current = next;
      return next;
    });
  }, []);

  const startAnalysis = useCallback(async () => {
    if (!idea?.description || startedRef.current) return;
    startedRef.current = true;
    setCurrentStep("analyzing");
    setXaiSteps([]);
    xaiStepsRef.current = [];

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
              saveClarifierResult(
                idea.id,
                {
                  clarity_status: "refused",
                  clarity_score: 0,
                  clarity_refused_reason: data.reason_category || "",
                  clarity_refused_message:
                    data.message || data.refusal_message || "",
                },
                token,
              ).then(() => options.onPersisted?.());
              return;
            }
            if (data.type === "questions") {
              // Sauvegarder le secteur détecté pour le 2ème appel
              if (data.detected_sector) {
                setDetectedSector(data.detected_sector);
              }
              saveClarifierResult(
                idea.id,
                {
                  clarity_status: "questions",
                  clarity_questions: data.questions || [],
                  clarity_agent_message: data.message || "",
                },
                token,
              ).then(() => options.onPersisted?.());
              return;
            }
            if (data.type === "clarified") {
              saveClarifierResult(
                idea.id,
                {
                  clarity_status: "clarified",
                  clarity_score: data.score || 0,
                  clarity_sector: data.sector || "",
                  clarity_target_users: data.target_users || "",
                  clarity_problem: data.problem || "",
                  clarity_solution: data.solution_description || "",
                  clarity_short_pitch: data.short_pitch || "",
                  clarity_agent_message: data.message || "",
                  clarity_questions: [],
                  clarity_answers: {},
                },
                token,
              ).then(() => options.onPersisted?.());
            }
          }

          if (eventType === "done") {
            resolveLoadingSteps();
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
    setXaiSteps((prev) => {
      const next = [
        ...prev,
        {
          id: Date.now(),
          status: "loading",
          text: "Analyse de vos réponses...",
          detail: {},
        },
      ];
      xaiStepsRef.current = next;
      return next;
    });

    try {
      await readSSEStream(
        `${AI_URL}/clarifier/answer/stream`,
        {
          idea_id: idea.id,
          name: idea.name || "",
          sector: detectedSector || idea.sector || "",
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
            if (data.type === "refused") {
              saveClarifierResult(
                idea.id,
                {
                  clarity_status: "refused",
                  clarity_score: 0,
                  clarity_refused_reason: data.reason_category || "",
                  clarity_refused_message:
                    data.message || data.refusal_message || "",
                },
                token,
              ).then(() => options.onPersisted?.());
              return;
            }
            if (data.type === "clarified") {
              saveClarifierResult(
                idea.id,
                {
                  clarity_status: "clarified",
                  clarity_score: data.score || 0,
                  clarity_sector: data.sector || "",
                  clarity_target_users: data.target_users || "",
                  clarity_problem: data.problem || "",
                  clarity_solution: data.solution_description || "",
                  clarity_short_pitch: data.short_pitch || "",
                  clarity_agent_message: data.message || "",
                  clarity_questions: questions || [],
                  clarity_answers: {
                    problem: answers.problem || "",
                    target: answers.target || "",
                    solution: answers.solution || "",
                  },
                },
                token,
              ).then(() => options.onPersisted?.());
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
    questions,
    detectedSector,
    currentStep,
    addXaiStep,
    readSSEStream,
    resolveLoadingSteps,
  ]);

  return {
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
    detectedSector,
    refusalData,
    setRefusalData,
    startAnalysis,
    submitAnswers,
  };
}

