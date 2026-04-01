import { useState, useCallback, useRef } from "react";
import { useSSEStream } from "@/agents/shared/hooks/useSSEStream";
import { safeText } from "@/agents/shared/utils/safeText";
import { createStreamWords } from "@/agents/shared/utils/streamWords";

const AI_URL = import.meta.env.VITE_AI_URL || "http://localhost:8001/api/ai";
// @deprecated - remplacé par useClarifierAgent

export function useClarifierChat(idea, token) {
  const [messages, setMessages] = useState([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const [clarityScore, setClarityScore] = useState(0);
  const [isReady, setIsReady] = useState(false);
  const [clarifiedIdea, setClarifiedIdea] = useState(null);
  const [isRefused, setIsRefused] = useState(false);
  const [agentSteps, setAgentSteps] = useState([]);
  const [questions, setQuestions] = useState([]);
  const [answers, setAnswers] = useState({
    problem: "",
    target: "",
    solution: "",
    geography: "",
  });

  const streamTimerRef = useRef(null);
  const startedRef = useRef(false);
  const { readSSEStream } = useSSEStream();
  const streamWords = createStreamWords(setMessages);

  const addMessage = useCallback((role, content, extra = {}) => {
    setMessages((prev) => [
      ...prev,
      {
        id: Date.now() + Math.random(),
        role,
        content,
        timestamp: new Date(),
        ...extra,
      },
    ]);
  }, []);

  const addStep = useCallback((status, text, detail = {}) => {
    setAgentSteps((prev) => [
      ...prev,
      { id: Date.now() + Math.random(), status, text, detail },
    ]);
  }, []);

  const startConversation = useCallback(async () => {
    if (!idea?.description || startedRef.current) return;
    startedRef.current = true;
    setIsStreaming(true);
    setAgentSteps([]);

    addMessage("user", idea.description);

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
            addStep(data.status, data.message, {
              dimensions: data.dimensions || null,
              sector: data.sector || null,
              confidence: data.confidence || null,
              score: data.score || null,
              model: data.model || null,
              elapsed_ms: data.elapsed_ms || null,
            });
          } else if (eventType === "result") {
            setIsStreaming(false);
            const msg = safeText(data.message);

            if (data.type === "refused") {
              setIsRefused(true);
              if (msg) streamWords(msg, null);
              return;
            }

            if (data.type === "questions") {
              setQuestions(data.questions || []);
              if (msg) {
                streamWords(msg, (msgId) => {
                  setMessages((prev) =>
                    prev.map((m) =>
                      m.id === msgId
                        ? {
                            ...m,
                            structured: {
                              type: "questions",
                              questions: data.questions || [],
                            },
                          }
                        : m,
                    ),
                  );
                });
              }
            }

            if (data.type === "clarified") {
              const score = data.score || 0;
              setClarityScore(score);
              setClarifiedIdea(data);
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
                                what: safeText(data.solution_description),
                                who: safeText(data.target_users),
                                problem: safeText(data.problem),
                                pitch: safeText(data.short_pitch),
                              },
                            },
                          }
                        : m,
                    ),
                  );
                });
              }
            }
          } else if (eventType === "done") {
            setIsStreaming(false);
          }
        },
        { headers: token ? { Authorization: `Bearer ${token}` } : {} },
      );
    } catch (err) {
      setIsStreaming(false);
      addMessage(
        "agent",
        err.message.includes("Failed to fetch")
          ? "Service IA injoignable. Vérifiez le port 8001."
          : `Erreur : ${err.message}`,
      );
    }
  }, [idea, token, addMessage, addStep, streamWords, readSSEStream]);

  const submitAnswers = useCallback(
    async (userAnswers) => {
      if (!idea || isStreaming) return;
      setIsStreaming(true);
      setAgentSteps([]);

      const summary = [
        userAnswers.problem,
        userAnswers.target,
        userAnswers.solution,
        userAnswers.geography,
      ]
        .filter(Boolean)
        .join(" • ");
      addMessage("user", summary);

      try {
        await readSSEStream(
          `${AI_URL}/clarifier/answer/stream`,
          {
            idea_id: idea.id,
            name: idea.name || "",
            sector: idea.sector || "",
            description: idea.description,
            target_audience: idea.target_audience || "",
            answer_problem: userAnswers.problem || "",
            answer_target: userAnswers.target || "",
            answer_solution: userAnswers.solution || "",
            answer_geography: userAnswers.geography || "",
          },
          (eventType, data) => {
            if (eventType === "step") {
              addStep(data.status, data.message, {
                score: data.score || null,
                model: data.model || null,
                elapsed_ms: data.elapsed_ms || null,
              });
            } else if (eventType === "result") {
              setIsStreaming(false);
              if (data.type === "clarified") {
                const score = data.score || 0;
                setClarityScore(score);
                setClarifiedIdea(data);
                if (score >= 55) setIsReady(true);
                const msg = safeText(data.message);
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
                                  what: safeText(data.solution_description),
                                  who: safeText(data.target_users),
                                  problem: safeText(data.problem),
                                  pitch: safeText(data.short_pitch),
                                },
                              },
                            }
                          : m,
                      ),
                    );
                  });
                }
              }
            } else if (eventType === "done") {
              setIsStreaming(false);
            }
          },
          { headers: token ? { Authorization: `Bearer ${token}` } : {} },
        );
      } catch (err) {
        setIsStreaming(false);
        addMessage("agent", `Erreur : ${err.message}`);
      }
    },
    [idea, isStreaming, addMessage, addStep, streamWords, readSSEStream, token],
  );

  return {
    messages,
    isStreaming,
    clarityScore,
    isReady,
    clarifiedIdea,
    isRefused,
    agentSteps,
    questions,
    answers,
    setAnswers,
    startConversation,
    submitAnswers,
  };
}

export default useClarifierChat;

