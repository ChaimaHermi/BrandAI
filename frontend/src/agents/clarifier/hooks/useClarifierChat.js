import { useState, useCallback, useRef } from "react";

const AI_URL = import.meta.env.VITE_AI_URL || "http://localhost:8001/api/ai";

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

  const readSSEStream = useCallback(async (url, body, onEvent, options = {}) => {
    const headers = {
      "Content-Type": "application/json",
      ...(options.headers || {}),
    };
    const response = await fetch(url, {
      method: "POST",
      headers,
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
          what: c?.solution_description,
          who: c?.target_users,
          problem: c?.problem,
          pitch: c?.short_pitch,
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

  const applyClarifierResult = useCallback(
    (result, options = {}) => {
      setIsStreaming(false);
      if (result.error) {
        addStep("error", result.error);
        return;
      }
      const formatted = formatAgentResponse(result);
      if (formatted.type === "refused") {
        setIsRefused(true);
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
      if (formatted.type === "questions") {
        setPendingQuestions(formatted.questions);
        const introText = "J'ai analysé votre idée. Pour mieux la comprendre, j'ai quelques questions :";
        streamWords(introText, (msgId) => {
          setMessages((prev) =>
            prev.map((m) =>
              m.id === msgId
                ? { ...m, structured: { type: "questions", questions: formatted.questions } }
                : m,
            ),
          );
        });
        return;
      }
      if (formatted.type === "clarified") {
        setPendingQuestions([]);
        const score = result.clarified_idea?.clarity_score ?? formatted.score ?? 0;
        setClarityScore(score);
        setClarifiedIdea(formatted.clarifiedIdea);
        if (score >= 80) setIsReady(true);
        const introClarified = options.fromAnswer
          ? "Merci pour ces précisions ! Voici votre idée structurée :"
          : score >= 80
            ? "Votre idée est bien structurée ! Voici ce que j'ai compris :"
            : "Voici ce que j'ai compris de votre idée :";
        streamWords(introClarified, (msgId) => {
          const sec = result.clarified_idea || {};
          const sections = formatted.sections || {
            what: sec?.solution_description ?? null,
            who: sec?.target_users ?? null,
            problem: sec?.problem ?? null,
            pitch: sec?.short_pitch ?? null,
          };
          setMessages((prev) =>
            prev.map((m) =>
              m.id === msgId
                ? { ...m, structured: { type: "clarified", ...formatted, score, sections } }
                : m,
            ),
          );
        });
        return;
      }
      streamWords(formatted?.text != null ? String(formatted.text) : "Réponse reçue.");
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
  };
}

export default useClarifierChat;

