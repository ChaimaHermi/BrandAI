import { useState, useCallback, useRef } from "react";
import { useSSEStream } from "@/agents/shared/hooks/useSSEStream";
import { createStreamWords } from "@/agents/shared/utils/streamWords";
import { safeText } from "@/agents/shared/utils/safeText";

const AI_URL = import.meta.env.VITE_AI_URL || "http://localhost:8001/api/ai";

// Copie exacte de useChatStream (logique pré-existante),
// avec factorisation de readSSEStream, streamWords et safeText.
export function useClarifierChat(idea, token) {
  const [messages, setMessages] = useState([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const [clarityScore, setClarityScore] = useState(0);
  const [isReady, setIsReady] = useState(false);
  const [isRefused, setIsRefused] = useState(false);
  const [pendingQuestions, setPendingQuestions] = useState([]);
  const [clarifiedIdea, setClarifiedIdea] = useState(null);
  const [agentSteps, setAgentSteps] = useState([]);
  const streamTimerRef = useRef(null);

  const { readSSEStream } = useSSEStream();
  const streamWords = createStreamWords(setMessages);

  const clearSteps = useCallback(() => setAgentSteps([]), []);

  const addStep = useCallback((status, text, detail = {}) => {
    setAgentSteps((prev) => [
      ...prev,
      { id: Date.now() + Math.random(), status, text, detail },
    ]);
  }, []);

  const replaceLastLoadingStep = useCallback((status, text, detail) => {
    setAgentSteps((prev) => {
      const last = prev[prev.length - 1];
      if (last && last.status === "loading") {
        return [
          ...prev.slice(0, -1),
          { id: Date.now() + Math.random(), status, text, detail },
        ];
      }
      return [...prev, { id: Date.now() + Math.random(), status, text, detail }];
    });
  }, []);

  const addMessage = useCallback((role, content, extra = {}) => {
    setMessages((prev) => [
      ...prev,
      {
        id: Date.now() + Math.random(),
        role,
        content: safeText(content, ""),
        timestamp: new Date().toISOString(),
        ...extra,
      },
    ]);
  }, []);

  const formatAgentResponse = useCallback((result) => {
    const rawQuestions = result.questions || [];
    const questions = rawQuestions.filter(
      (q) => q != null && String(q).trim() !== "",
    );

    if (result.type === "questions" || questions.length > 0) {
      return {
        type: "questions",
        questions,
      };
    }

    if (result.type === "clarified") {
      return {
        type: "clarified",
        clarifiedIdea: result,
        score: result.score,
        sections: {
          what: result?.solution_description,
          who: result?.target_users,
          problem: result?.problem,
          pitch: result?.short_pitch,
        },
      };
    }

    if (result.type === "refused" || result.safe === false) {
      const msg = safeText(result.refusal_message || result.message);
      return {
        type: "refused",
        reason_category: result.reason_category,
        refusal_message: msg,
        partial_understanding: {
          what: result.partial_what ?? null,
          who: result.partial_who ?? null,
          problem: result.partial_problem ?? null,
        },
        score: 0,
      };
    }

    return { type: "unknown" };
  }, []);

  const applyClarifierResult = useCallback(
    (result, options = {}) => {
      setIsStreaming(false);
      if (result.error) {
        addStep("error", result.error);
        return;
      }
      const formatted = formatAgentResponse(result);
      // Type refused
      if (formatted.type === "refused") {
        setIsRefused(true);
        const msg = safeText(result.refusal_message || result.message);
        if (msg) {
          streamWords(msg, (msgId) => {
            setMessages((prev) =>
              prev.map((m) =>
                m.id === msgId
                  ? {
                      ...m,
                      structured: {
                        type: "refused",
                        reason_category: formatted.reason_category,
                        refusal_message: formatted.refusal_message,
                        partial_understanding:
                          formatted.partial_understanding || {},
                        score: 0,
                      },
                    }
                  : m,
              ),
            );
          });
        }
        return;
      }

      // Type questions
      if (result.type === "questions") {
        const msg = safeText(result.message);
        if (msg) {
          streamWords(msg, (msgId) => {
            setMessages((prev) =>
              prev.map((m) =>
                m.id === msgId
                  ? {
                      ...m,
                      structured: {
                        type: "questions",
                        questions: result.questions || [],
                      },
                    }
                  : m,
              ),
            );
          });
        }
        setPendingQuestions(result.questions || []);
        setClarityScore(result.score || 0);
        return;
      }

      // Type off_topic
      if (result.type === "off_topic") {
        const msg = safeText(result.message);
        if (msg) {
          streamWords(msg, () => {
            if (result.repeat_question) {
              setTimeout(() => {
                setMessages((prev) => [
                  ...prev,
                  {
                    id: Date.now() + Math.random(),
                    role: "agent",
                    content: result.repeat_question,
                    isStreaming: false,
                    timestamp: new Date(),
                    structured: {
                      type: "questions",
                      questions: [result.repeat_question],
                    },
                  },
                ]);
                setPendingQuestions([result.repeat_question]);
              }, 1000);
            }
          });
        }
        return;
      }

      // Type clarified
      if (result.type === "clarified") {
        const score = result.score || 0;
        const msg = safeText(result.message);

        setClarityScore(score);
        setClarifiedIdea(result);
        if (score >= 55) setIsReady(true);

        if (msg) {
          streamWords(msg, (msgId) => {
            setMessages((prev) =>
              prev.map((m) =>
                m.id === msgId
                  ? {
                      ...m,
                      structured: {
                        type: "clarified",
                        score,
                        sections: {
                          what: safeText(result.solution_description),
                          who: safeText(result.target_users),
                          problem: safeText(result.problem),
                          pitch: safeText(result.short_pitch),
                        },
                      },
                    }
                  : m,
              ),
            );
          });
        }
        return;
      }

      // Fallback
      const fallbackMsg = safeText(result.message || "Réponse reçue.");
      if (fallbackMsg) {
        streamWords(fallbackMsg, null);
      }
    },
    [addStep, formatAgentResponse, streamWords],
  );

  const handleSSEEvent = useCallback(
    (eventType, data, options = {}) => {
      if (eventType === "step") {
        const detail = {
          sector: data.sector ?? null,
          confidence: data.confidence ?? null,
          dimensions: data.dimensions ?? null,
          score: data.score ?? null,
          model: data.model ?? null,
          elapsed_ms: data.elapsed_ms ?? null,
        };
        if (data.status !== "loading") {
          setAgentSteps((prev) => {
            const last = prev[prev.length - 1];
            if (last && last.status === "loading") {
              return [
                ...prev.slice(0, -1),
                {
                  id: Date.now() + Math.random(),
                  status: data.status,
                  text: data.message,
                  detail,
                },
              ];
            }
            return [
              ...prev,
              {
                id: Date.now() + Math.random(),
                status: data.status,
                text: data.message,
                detail,
              },
            ];
          });
        } else {
          addStep(data.status, data.message, detail);
        }
      } else if (eventType === "result") {
        addStep("success", "Analyse terminée ✓");
        applyClarifierResult(data, options);
      }
    },
    [addStep, applyClarifierResult],
  );

  const startConversation = useCallback(async () => {
    if (!idea || !idea.id) return;

    clearSteps();
    addMessage("user", idea.description || "");
    setIsStreaming(true);

    try {
      await readSSEStream(
        `${AI_URL}/clarifier/start/stream`,
        {
          idea_id: idea.id,
          name: idea.name,
          sector: idea.sector,
          description: idea.description,
          target_audience: idea.target_audience || "",
        },
        (eventType, data) => handleSSEEvent(eventType, data, {}),
        { headers: token ? { Authorization: `Bearer ${token}` } : {} },
      );
    } catch (err) {
      setIsStreaming(false);
      addStep("error", "✗ Erreur serveur IA");
      addMessage(
        "agent",
        "Une erreur s'est produite. Vérifiez que le service IA est démarré (port 8001).",
      );
    }
  }, [idea, token, addMessage, addStep, clearSteps, readSSEStream, handleSSEEvent]);

  const sendAnswer = useCallback(
    async (userText) => {
      if (!idea || isStreaming || !userText?.trim()) return;

      addMessage("user", userText.trim());
      setIsStreaming(true);
      setPendingQuestions([]);

      const answers = [userText.trim()];

      try {
        await readSSEStream(
          `${AI_URL}/clarifier/answer/stream`,
          {
            idea_id: idea.id,
            name: idea.name,
            sector: idea.sector,
            description: idea.description,
            target_audience: idea.target_audience || "",
            answers,
          },
          (eventType, data) => handleSSEEvent(eventType, data, { fromAnswer: true }),
          { headers: token ? { Authorization: `Bearer ${token}` } : {} },
        );
      } catch (err) {
        setIsStreaming(false);
        addMessage("agent", "Erreur lors du traitement. Réessayez.");
      }
    },
    [idea, token, isStreaming, addMessage, readSSEStream, handleSSEEvent],
  );

  return {
    messages,
    isStreaming,
    clarityScore,
    isReady,
    isRefused,
    clarifiedIdea,
    pendingQuestions,
    agentSteps,
    startConversation,
    sendAnswer,
    readSSEStream,
  };
}

export default useClarifierChat;

