import { useState, useCallback } from "react";

// Simple incremental id for messages (local only)
let __msgId = 0;
const nextId = () => {
  __msgId += 1;
  return `m_${__msgId}_${Date.now()}`;
};

const AGENT_DEFAULT = "idea_clarifier";

function buildSimulatedClarifierResponse(userText) {
  const baseText = userText || "";
  const short =
    baseText.length > 160 ? `${baseText.slice(0, 157).trim()}...` : baseText;

  const clarityScore = Math.min(
    95,
    60 + Math.round(Math.min(baseText.length / 4, 35)),
  );

  return {
    agent: "idea_clarifier",
    understanding: {
      what:
        short ||
        "Vous décrivez une idée de projet autour de l'innovation digitale, encore à préciser.",
      who:
        "Principalement des utilisateurs ou clients qui rencontrent aujourd'hui des frictions importantes sur ce sujet.",
      problem:
        "Ils manquent de solution simple, claire et guidée pour résoudre ce problème au quotidien.",
    },
    questions: [
      "Si vous deviez résumer votre idée en une seule phrase très concrète, que diriez-vous ?",
      "Quel type de personne ou d'organisation a le plus besoin de cette solution selon vous (profil, secteur, taille...) ?",
    ],
    clarity_score: clarityScore,
    clarity_label:
      clarityScore >= 85
        ? "Très clair"
        : clarityScore >= 75
          ? "Bonne base"
          : "À préciser",
    reasoning:
      "J'ai relu plusieurs fois votre description pour extraire les éléments clés : ce que vous proposez, pour qui et quel problème vous résolvez. Ensuite, j'ai reformulé ces éléments avec des mots simples afin de vérifier que nous partageons la même compréhension. Enfin, je génère des questions ciblées uniquement sur les zones encore floues pour vous aider à clarifier sans vous noyer.",
    confidence:
      clarityScore >= 85 ? "high" : clarityScore >= 70 ? "medium" : "low",
    sources_used: [
      "nom du projet",
      "description soumise",
      "secteur d'activité",
    ],
  };
}

function renderStructuredText(structured) {
  if (!structured) return "";
  const lines = [];
  lines.push("Voici ce que j'ai compris de votre idée :");
  lines.push("");
  lines.push("[Ce que vous proposez]");
  lines.push(`→ ${structured.understanding?.what || ""}`);
  lines.push("");
  lines.push("[Pour qui ?]");
  lines.push(`→ ${structured.understanding?.who || ""}`);
  lines.push("");
  lines.push("[Le problème résolu]");
  lines.push(`→ ${structured.understanding?.problem || ""}`);
  lines.push("");
  if (Array.isArray(structured.questions) && structured.questions.length > 0) {
    lines.push("[Questions de clarification]");
    structured.questions.forEach((q, idx) => {
      lines.push(`${idx + 1}. ${q}`);
    });
    lines.push("");
  }
  if (typeof structured.clarity_score === "number") {
    lines.push(
      `[Clarity Score] ${structured.clarity_score}/100 — ${structured.clarity_label}`,
    );
  }
  return lines.join("\n");
}

export function useChatStream() {
  const [messages, setMessages] = useState([]);
  const [isStreaming, setIsStreaming] = useState(false);

  const streamText = useCallback((fullText, onChunk, onDone) => {
    const total = fullText.length;
    if (!total) {
      onDone?.();
      return;
    }

    let index = 0;

    const tick = () => {
      if (index >= total) {
        onDone?.();
        return;
      }

      const step = 1;
      index += step;
      const chunk = fullText.slice(0, index);
      onChunk(chunk);

      const delay = 20 + Math.round(Math.random() * 40);
      window.setTimeout(tick, delay);
    };

    tick();
  }, []);

  const sendMessage = useCallback(
    async (text, agentType = AGENT_DEFAULT) => {
      if (!text || !text.trim()) return;

      const now = new Date().toISOString();
      const userMessage = {
        id: nextId(),
        role: "user",
        text: text.trim(),
        createdAt: now,
      };

      setMessages((prev) => [...prev, userMessage]);
      setIsStreaming(true);

      const structured = buildSimulatedClarifierResponse(text);
      const fullText = renderStructuredText(structured);

      const agentMessageId = nextId();
      const agentBase = {
        id: agentMessageId,
        role: "agent",
        agentType,
        createdAt: new Date().toISOString(),
        structured,
        streamedText: "",
      };

      setTimeout(() => {
        setMessages((prev) => [...prev, agentBase]);

        streamText(
          fullText,
          (partial) => {
            setMessages((prev) =>
              prev.map((m) =>
                m.id === agentMessageId ? { ...m, streamedText: partial } : m,
              ),
            );
          },
          () => {
            setIsStreaming(false);
          },
        );
      }, 800);
    },
    [streamText],
  );

  return { messages, isStreaming, sendMessage };
}

export default useChatStream;

