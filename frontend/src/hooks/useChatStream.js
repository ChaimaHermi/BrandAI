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

  const addStep = useCallback((status, text, detail) => {
    setAgentSteps((prev) => {
      const last = prev[prev.length - 1];
      if (last && last.text === text && last.status === "loading") {
        return [...prev.slice(0, -1), { ...last, status, text, detail: detail ?? last.detail }];
      }
      return [...prev, { id: Date.now() + Math.random(), status, text, detail }];
    });
  }, []);

  const replaceLastLoadingStep = useCallback((status, text, detail) => {
    setAgentSteps((prev) => {
      const last = prev[prev.length - 1];
      if (last && last.status === "loading") {
        return [...prev.slice(0, -1), { id: Date.now() + Math.random(), status, text, detail }];
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
        content,
        timestamp: new Date().toISOString(),
        ...extra,
      },
    ]);
  }, []);

  const streamWords = useCallback((fullText, onComplete) => {
    if (!fullText || typeof fullText !== "string") {
      if (onComplete) onComplete(null);
      return null;
    }

    const clean = fullText
      .replace(/\bundefined\b/g, "")
      .replace(/\s{2,}/g, " ")
      .trim();

    if (!clean) {
      if (onComplete) onComplete(null);
      return null;
    }

    const words = clean.split(" ");
    const msgId = Date.now() + Math.random();

    setMessages((prev) => [
      ...prev,
      {
        id: msgId,
        role: "agent",
        content: "",
        isStreaming: true,
        timestamp: new Date(),
      },
    ]);

    let i = 0;

    const tick = () => {
      if (i < words.length) {
        const word = words[i];
        setMessages((prev) =>
          prev.map((m) =>
            m.id === msgId
              ? { ...m, content: m.content + (i === 0 ? "" : " ") + word }
              : m,
          ),
        );
        i++;
        streamTimerRef.current = setTimeout(tick, 40 + Math.random() * 40);
      } else {
        setMessages((prev) =>
          prev.map((m) =>
            m.id === msgId ? { ...m, isStreaming: false } : m,
          ),
        );
        if (onComplete) onComplete(msgId);
      }
    };

    tick();
    return msgId;
  }, []);

  const readSSEStream = useCallback(async (url, body, onEvent) => {
    const response = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });

    if (!response.ok) {
      const text = await response.text();
      throw new Error(`HTTP ${response.status}: ${text}`);
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder("utf-8");
    let buffer = "";

    const processBuffer = () => {
      const blocks = buffer.split("\n\n");
      buffer = blocks.pop() ?? "";

      for (const block of blocks) {
        const trimmed = block.trim();
        if (!trimmed) continue;

        let eventType = "message";
        let rawData = "";

        for (const line of trimmed.split("\n")) {
          if (line.startsWith("event:")) {
            eventType = line.slice(6).trim();
          } else if (line.startsWith("data:")) {
            rawData = line.slice(5).trim();
          }
        }

        if (!rawData) continue;

        const isCompleteJson =
          (rawData.startsWith("{") && rawData.endsWith("}")) ||
          (rawData.startsWith("[") && rawData.endsWith("]")) ||
          (!rawData.startsWith("{") && !rawData.startsWith("["));

        if (!isCompleteJson) {
          buffer = block + "\n\n" + buffer;
          continue;
        }

        let parsed;
        try {
          parsed = JSON.parse(rawData);
        } catch {
          parsed = rawData;
        }

        onEvent(eventType, parsed);
      }
    };

    while (true) {
      const { done, value } = await reader.read();

      if (done) {
        buffer += decoder.decode();
        if (buffer.trim()) {
          buffer += "\n\n";
          processBuffer();
        }
        break;
      }

      buffer += decoder.decode(value, { stream: true });

      if (buffer.includes("\n\n")) {
        processBuffer();
      }
    }
  }, []);

  const formatAgentResponse = useCallback((result) => {
    const rawQuestions = result.questions || [];
    const questions = rawQuestions.filter(
      (q) => q != null && String(q).trim() !== ""
    );
    if (questions.length > 0) {
      return {
        type: "questions",
        questions,
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
      const fallback =
        "Ce projet ne peut pas être traité par BrandAI pour des raisons de sécurité.";
      let raw =
        result.refusal_message != null && typeof result.refusal_message === "string"
          ? result.refusal_message
          : fallback;
      raw = String(raw).trim();
      const refusalMessage = raw
        .replace(/\s*undefined\s*$/i, "")
        .replace(/\s*null\s*$/i, "")
        .trim() || fallback;
      return {
        type: "refused",
        reason_category: result.reason_category,
        refusal_message: refusalMessage,
        partial_understanding: {
          what: result.partial_what ?? null,
          who: result.partial_who ?? null,
          problem: result.partial_problem ?? null,
        },
        score: 0,
        text: refusalMessage,
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
        setAgentSteps((prev) => {
          const rest = prev.slice(0, -1);
          return [
            ...rest,
            {
              id: Date.now() + Math.random(),
              status: "error",
              text: `✗ Projet refusé — ${result.reason_category || "sécurité"}`,
            },
          ];
        });
        setIsRefused(true);
        const formatted = formatAgentResponse(result);
        streamWords(formatted.text, (msgId) => {
          setMessages((prev) =>
            prev.map((m) =>
              m.id === msgId
                ? {
                    ...m,
                    structured: {
                      type: "refused",
                      reason_category: formatted.reason_category,
                      refusal_message: formatted.refusal_message,
                      partial_understanding: formatted.partial_understanding || {},
                      score: 0,
                    },
                  }
                : m,
            ),
          );
        });
        return;
      }

      replaceLastLoadingStep("success", "✓ Sécurité — projet conforme");
      addStep("loading", "Analyse de la description...");
      await new Promise((r) => setTimeout(r, 300));

      const formatted = formatAgentResponse(result);

      if (formatted.type === "questions") {
        replaceLastLoadingStep("info", `✓ Analyse — ${formatted.questions.length} dimension(s) manquante(s)`);
        addStep("info", `${formatted.questions.length} question(s) nécessaire(s)`, {
          question: formatted.questions?.[0] ?? null,
        });
        setPendingQuestions(formatted.questions);
        const introText = "J'ai analysé votre idée. Pour mieux la comprendre, j'ai quelques questions :";
        streamWords(
          introText,
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
        replaceLastLoadingStep("success", "✓ Analyse — description complète");
        addStep("loading", "Génération du JSON structuré...");
        await new Promise((r) => setTimeout(r, 200));
        replaceLastLoadingStep("success", "✓ JSON généré");

        const score = result.clarified_idea?.clarity_score ?? formatted.score ?? 0;
        setClarityScore(score);
        setClarifiedIdea(formatted.clarifiedIdea);
        if (score >= 80) setIsReady(true);

        const introClarified = score >= 80
          ? "Votre idée est bien structurée ! Voici ce que j'ai compris :"
          : "Voici ce que j'ai compris de votre idée :";
        streamWords(
          introClarified,
          (msgId) => {
            const sec = result.clarified_idea || {};
            const sections = formatted.sections || {
              what: sec.solution_description ?? null,
              who: sec.target_users ?? null,
              problem: sec.problem ?? null,
              pitch: sec.short_pitch ?? null,
            };
            setMessages((prev) =>
              prev.map((m) =>
                m.id === msgId
                  ? {
                      ...m,
                      structured: {
                        type: "clarified",
                        ...formatted,
                        score,
                        sections,
                      },
                    }
                  : m,
              ),
            );
          },
        );
      } else {
        const fallbackText = formatted?.text != null ? String(formatted.text) : "Réponse reçue.";
        streamWords(fallbackText);
      }
    } catch (err) {
      setIsStreaming(false);
      addStep("error", "✗ Erreur serveur IA");
      addMessage(
        "agent",
        "Une erreur s'est produite. Vérifiez que le service IA est démarré (port 8001).",
      );
    }
  }, [idea, token, addMessage, addStep, replaceLastLoadingStep, clearSteps, streamWords, formatAgentResponse]);

  const sendAnswer = useCallback(
    async (userText) => {
      if (!idea || isStreaming || !userText?.trim()) return;

      addMessage("user", userText.trim());
      setIsStreaming(true);

      const answers = [userText.trim()];

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

          streamWords(
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
          const introText = "J'ai analysé votre idée. Pour mieux la comprendre, j'ai quelques questions :";
          streamWords(
            introText,
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
          const fallbackText = formatted?.text != null ? String(formatted.text) : "Réponse reçue.";
          streamWords(fallbackText);
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
      addMessage,
      streamWords,
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
    readSSEStream,
  };
}

export default useChatStream;

