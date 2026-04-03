import { useEffect, useState, useCallback, useRef } from "react";
import { useSSEStream } from "@/agents/shared/hooks/useSSEStream";
import { saveClarifierResult } from "../api/clarifier.api";
import { apiGetIdea } from "@/services/ideaApi";

const AI_URL =
  import.meta.env.VITE_AI_URL || "http://localhost:8001/api/ai";

/** Données affichées dans ClarifiedBlock, construites depuis l'idée en base. */
function mapIdeaToClarifiedBlock(idea) {
  return {
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
}

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
    geography: "",
  });
  const [clarifiedIdea, setClarifiedIdea] = useState(null);
  const [clarityScore, setClarityScore] = useState(0);
  const [isReady, setIsReady] = useState(false);
  const [refusalData, setRefusalData] = useState(null);

  const startedRef = useRef(false);
  const optionsRef = useRef(options);
  const { readSSEStream } = useSSEStream();

  useEffect(() => {
    optionsRef.current = options;
  }, [options]);

  // Assurer la synchro de la ref quand `setXaiSteps` est modifié depuis l'extérieur.
  useEffect(() => {
    xaiStepsRef.current = xaiSteps;
  }, [xaiSteps]);

  useEffect(() => {
    startedRef.current = false;
    return () => {
      startedRef.current = false;
    };
  }, [idea?.id]);

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

  const syncClarifierToServer = useCallback(
    async (payload, kind, sseExtras = {}) => {
      const saved = await saveClarifierResult(idea.id, payload, token);
      if (!saved?.success) {
        addXaiStep("error", "Échec de la sauvegarde du résultat.");
        return false;
      }
      try {
        const fresh = await apiGetIdea(idea.id, token);
        if (kind === "clarified") {
          setClarifiedIdea(mapIdeaToClarifiedBlock(fresh));
          setClarityScore(fresh.clarity_score ?? 0);
          setIsReady(true);
          setCurrentStep("clarified");
          optionsRef.current.onClarified?.(fresh);
        } else if (kind === "questions") {
          if (sseExtras.detected_sector) {
            setDetectedSector(sseExtras.detected_sector);
          }
          setQuestions(fresh.clarity_questions || []);
          setAgentMessage(fresh.clarity_agent_message || "");
          setCurrentStep("questions");
        } else if (kind === "refused") {
          setRefusalData({
            type: "refused",
            reason_category: fresh.clarity_refused_reason ?? undefined,
            message: fresh.clarity_refused_message ?? undefined,
            refusal_message: fresh.clarity_refused_message ?? undefined,
          });
          setCurrentStep("refused");
        }
        optionsRef.current.onPersisted?.();
        return true;
      } catch (err) {
        addXaiStep(
          "error",
          err?.message || "Impossible de recharger l'idée après sauvegarde.",
        );
        return false;
      }
    },
    [idea?.id, token, addXaiStep],
  );

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
              void syncClarifierToServer(
                {
                  clarity_status: "refused",
                  clarity_score: 0,
                  clarity_refused_reason: data.reason_category || "",
                  clarity_refused_message:
                    data.message || data.refusal_message || "",
                },
                "refused",
              );
              return;
            }
            if (data.type === "questions") {
              void syncClarifierToServer(
                {
                  clarity_status: "questions",
                  clarity_questions: data.questions || [],
                  clarity_agent_message: data.message || "",
                },
                "questions",
                { detected_sector: data.detected_sector },
              );
              return;
            }
            if (data.type === "clarified") {
              void syncClarifierToServer(
                {
                  clarity_status: "clarified",
                  clarity_score: data.score || 0,
                  clarity_sector: data.sector || "",
                  clarity_target_users: data.target_users || "",
                  clarity_problem: data.problem || "",
                  clarity_solution: data.solution_description || "",
                  clarity_short_pitch: data.short_pitch || "",
                  clarity_agent_message: data.message || "",
                  clarity_country: data.country ?? "",
                  clarity_country_code: (data.country_code ?? "").toUpperCase(),
                  clarity_language: data.language ?? "",
                  clarity_questions: [],
                  clarity_answers: {},
                },
                "clarified",
              );
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
  }, [
    idea,
    token,
    addXaiStep,
    readSSEStream,
    currentStep,
    resolveLoadingSteps,
    syncClarifierToServer,
  ]);

  const submitAnswers = useCallback(async () => {
    if (!idea || currentStep !== "questions") return;

    const keys = ["problem", "target", "solution", "geography"];
    const getAxis = (q, i) => {
      if (typeof q === "string") return keys[i] || null;
      return q?.axis || keys[i] || null;
    };
    const requiredAxes = Array.from(
      new Set(
        (questions || [])
          .map((q, i) => getAxis(q, i))
          .filter((a) => typeof a === "string" && a.length > 0)
      )
    );
    const axesToValidate = requiredAxes.length ? requiredAxes : keys;

    const isValid = axesToValidate.every(
      (axis) => answers[axis]?.trim().length > 3
    );
    if (!isValid) return;

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
          answer_geography: (answers.geography || "").trim(),
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
              void syncClarifierToServer(
                {
                  clarity_status: "refused",
                  clarity_score: 0,
                  clarity_refused_reason: data.reason_category || "",
                  clarity_refused_message:
                    data.message || data.refusal_message || "",
                },
                "refused",
              );
              return;
            }
            if (data.type === "clarified") {
              void syncClarifierToServer(
                {
                  clarity_status: "clarified",
                  clarity_score: data.score || 0,
                  clarity_sector: data.sector || "",
                  clarity_target_users: data.target_users || "",
                  clarity_problem: data.problem || "",
                  clarity_solution: data.solution_description || "",
                  clarity_short_pitch: data.short_pitch || "",
                  clarity_agent_message: data.message || "",
                  clarity_country: data.country ?? "",
                  clarity_country_code: (data.country_code ?? "").toUpperCase(),
                  clarity_language: data.language ?? "",
                  clarity_questions: questions || [],
                  clarity_answers: {
                    problem: answers.problem || "",
                    target: answers.target || "",
                    solution: answers.solution || "",
                    geography: answers.geography || "",
                  },
                },
                "clarified",
              );
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
    syncClarifierToServer,
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

