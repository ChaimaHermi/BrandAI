import { useState, useCallback, useRef } from "react";

const AI_URL = import.meta.env.VITE_AI_URL || "http://localhost:8001/api/ai";

export function useChatStream(idea, token) {
  const [messages, setMessages] = useState([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const [clarityScore, setClarityScore] = useState(0);
  const [isReady, setIsReady] = useState(false);
  const [isRefused, setIsRefused] = useState(false);
  const [pendingQuestions, setPendingQuestions] = useState([]);
  const [clarifiedIdea, setClarifiedIdea] = useState(null);
  const [agentSteps, setAgentSteps] = useState([]);
  const streamTimerRef = useRef(null);

  const clearSteps = useCallback(() => setAgentSteps([]), []);

  const addStep = useCallback((status, text) => {
    setAgentSteps((prev) => {
      const last = prev[prev.length - 1];
      if (last && last.text === text && last.status === "loading") {
        return [...prev.slice(0, -1), { ...last, status, text }];
      }
      return [...prev, { id: Date.now() + Math.random(), status, text }];
    });
  }, []);

  const addMessage = useCallback((role, content, extra = {}) => {
    setMessages((prev) => [
      ...prev,
      {
        id: Date.now() + Math.random(),
        role,
        content,
        timestamp: new Date().toISOString(),
        ...extra,
      },
    ]);
  }, []);

  const streamText = useCallback((fullText, onComplete) => {
    if (!fullText) return;
    setIsStreaming(true);
    const msgId = Date.now() + Math.random();

    setMessages((prev) => [
      ...prev,
      {
        id: msgId,
        role: "agent",
        content: "",
        isStreaming: true,
        timestamp: new Date().toISOString(),
      },
    ]);

    let i = 0;
    const chars = fullText.split("");

    const tick = () => {
      if (i < chars.length) {
        setMessages((prev) =>
          prev.map((m) =>
            m.id === msgId ? { ...m, content: m.content + chars[i] } : m,
          ),
        );
        i += 1;
        const delay = 10 + Math.random() * 20;
        streamTimerRef.current = setTimeout(tick, delay);
      } else {
        setMessages((prev) =>
          prev.map((m) =>
            m.id === msgId ? { ...m, isStreaming: false } : m,
          ),
        );
        setIsStreaming(false);
        if (onComplete) onComplete(msgId);
      }
    };

    tick();
    return msgId;
  }, []);

  const formatAgentResponse = useCallback((result) => {
    if (result.questions && result.questions.length > 0) {
      return {
        type: "questions",
        questions: result.questions,
        text: "J'ai analysé votre idée. Pour mieux la comprendre, j'ai quelques questions :",
      };
    }

    if (result.clarified_idea && result.ready) {
      const c = result.clarified_idea;
      return {
        type: "clarified",
        clarifiedIdea: c,
        score: c.clarity_score,
        text: "Voici ce que j'ai compris de votre idée :",
        sections: {
          what: c.solution_description,
          who: c.target_users,
          problem: c.problem,
          pitch: c.short_pitch,
        },
      };
    }

    if (result.safe === false) {
      return {
        type: "refused",
        reason_category: result.reason_category,
        refusal_message:
          result.refusal_message ||
          "Ce projet ne peut pas être traité par BrandAI pour des raisons de sécurité.",
        partial_understanding: {
          what: result.partial_what ?? null,
          who: result.partial_who ?? null,
          problem: result.partial_problem ?? null,
        },
        score: 0,
        text:
          result.refusal_message ||
          "Ce projet ne peut pas être traité par BrandAI pour des raisons de sécurité.",
      };
    }

    return { type: "unknown", text: "Réponse reçue." };
  }, []);

  const startConversation = useCallback(async () => {
    if (!idea || !idea.id) return;

    clearSteps();
    addMessage("user", idea.description || "");
    addStep("loading", "Vérification de sécurité en cours...");
    setIsStreaming(true);

    try {
      const response = await fetch(`${AI_URL}/clarifier/start`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify({
          idea_id: idea.id,
          name: idea.name,
          sector: idea.sector,
          description: idea.description,
          target_audience: idea.target_audience || "",
        }),
      });

      if (!response.ok) throw new Error("Erreur serveur IA");
      const result = await response.json();
      setIsStreaming(false);

      if (!result.safe) {
        addStep("error", `✗ Projet refusé — ${result.reason_category || "default"}`);
        setIsRefused(true);
        const formatted = formatAgentResponse(result);
        setMessages((prev) => [
          ...prev,
          {
            id: Date.now() + Math.random(),
            role: "agent",
            content: formatted.text,
            isStreaming: false,
            timestamp: new Date().toISOString(),
            structured: {
              type: "refused",
              reason_category: formatted.reason_category,
              refusal_message: formatted.refusal_message,
              partial_understanding: formatted.partial_understanding || {},
              score: 0,
            },
          },
        ]);
        return;
      }

      addStep("success", "✓ Sécurité — projet conforme");
      addStep("loading", "Analyse de la description...");
      await new Promise((r) => setTimeout(r, 300));

      const formatted = formatAgentResponse(result);

      if (formatted.type === "questions") {
        addStep("info", `✓ Analyse — ${formatted.questions.length} dimension(s) manquante(s)`);
        addStep("info", `${formatted.questions.length} question(s) nécessaire(s)`);
        setPendingQuestions(formatted.questions);
        const questionText = formatted.questions
          .map((q, i) => `${i + 1}. ${q}`)
          .join("\n");
        streamText(
          `${formatted.text}\n\n${questionText}`,
          (msgId) => {
            setMessages((prev) =>
              prev.map((m) =>
                m.id === msgId
                  ? {
                      ...m,
                      structured: {
                        type: "questions",
                        questions: formatted.questions,
                      },
                    }
                  : m,
              ),
            );
          },
        );
      } else if (formatted.type === "clarified") {
        addStep("success", "✓ Analyse — description complète");
        addStep("loading", "Génération du JSON structuré...");
        await new Promise((r) => setTimeout(r, 200));
        addStep("success", "✓ JSON généré");

        const score = result.clarified_idea?.clarity_score ?? formatted.score ?? 0;
        setClarityScore(score);
        setClarifiedIdea(formatted.clarifiedIdea);
        if (score >= 80) setIsReady(true);

        streamText(
          "Voici la description structurée de votre projet :",
          (msgId) => {
            setMessages((prev) =>
              prev.map((m) =>
                m.id === msgId
                  ? {
                      ...m,
                      structured: {
                        type: "clarified",
                        ...formatted,
                        score,
                        sections: formatted.sections || {
                          what: result.clarified_idea?.solution_description,
                          who: result.clarified_idea?.target_users,
                          problem: result.clarified_idea?.problem,
                          pitch: result.clarified_idea?.short_pitch,
                        },
                      },
                    }
                  : m,
              ),
            );
          },
        );
      } else {
        streamText(formatted.text);
      }
    } catch (err) {
      setIsStreaming(false);
      addStep("error", "✗ Erreur serveur IA");
      addMessage(
        "agent",
        "Une erreur s'est produite. Vérifiez que le service IA est démarré (port 8001).",
      );
    }
  }, [idea, token, addMessage, addStep, clearSteps, streamText, formatAgentResponse]);

  const sendAnswer = useCallback(
    async (userText) => {
      if (!idea || isStreaming || !userText?.trim()) return;

      addMessage("user", userText.trim());
      setIsStreaming(true);

      const answers =
        pendingQuestions && pendingQuestions.length > 0
          ? pendingQuestions.map(() => userText.trim())
          : [userText.trim()];

      try {
        const response = await fetch(`${AI_URL}/clarifier/answer`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            ...(token ? { Authorization: `Bearer ${token}` } : {}),
          },
          body: JSON.stringify({
            idea_id: idea.id,
            name: idea.name,
            sector: idea.sector,
            description: idea.description,
            target_audience: idea.target_audience || "",
            answers,
          }),
        });

        if (!response.ok) throw new Error("Erreur serveur IA");
        const result = await response.json();

        setIsStreaming(false);
        setPendingQuestions([]);

        const formatted = formatAgentResponse(result);

        if (formatted.type === "clarified") {
          setClarityScore(formatted.score || 0);
          setClarifiedIdea(formatted.clarifiedIdea);
          if ((formatted.score || 0) >= 80) setIsReady(true);

          streamText(
            "Merci pour ces précisions ! Voici votre idée structurée :",
            (msgId) => {
              setMessages((prev) =>
                prev.map((m) =>
                  m.id === msgId
                    ? {
                        ...m,
                        structured: { type: "clarified", ...formatted },
                      }
                    : m,
                ),
              );
            },
          );
        } else if (formatted.type === "questions") {
          setPendingQuestions(formatted.questions);
          const questionText = formatted.questions
            .map((q, i) => `${i + 1}. ${q}`)
            .join("\n");
          streamText(
            `${formatted.text}\n\n${questionText}`,
            (msgId) => {
              setMessages((prev) =>
                prev.map((m) =>
                  m.id === msgId
                    ? {
                        ...m,
                        structured: {
                          type: "questions",
                          questions: formatted.questions,
                        },
                      }
                    : m,
                ),
              );
            },
          );
        } else {
          streamText(formatted.text);
        }
      } catch (err) {
        setIsStreaming(false);
        addMessage("agent", "Erreur lors du traitement. Réessayez.");
      }
    },
    [
      idea,
      token,
      isStreaming,
      pendingQuestions,
      addMessage,
      streamText,
      formatAgentResponse,
    ],
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
  };
}

export default useChatStream;

