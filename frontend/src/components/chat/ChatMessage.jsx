import React, { useState } from "react";
import { AgentAvatar, getAgentMeta } from "./AgentAvatar";
import { UserAvatar } from "../ui/UserAvatar";
import { ClarityScore } from "./ClarityScore";
import { Badge } from "../ui/Badge";

function formatTime(dateLike) {
  if (!dateLike) return "";
  const d = typeof dateLike === "string" ? new Date(dateLike) : dateLike;
  if (Number.isNaN(d.getTime())) return "";
  return d.toLocaleTimeString("fr-FR", {
    hour: "2-digit",
    minute: "2-digit",
  });
}

function ConfidenceBadge({ level }) {
  if (!level) return null;
  let label = "Confiance moyenne";
  let classes = "bg-[#FEF3C7] text-[#B45309]";

  if (level === "high") {
    label = "Confiance élevée";
    classes = "bg-[#DCFCE7] text-[#15803D]";
  } else if (level === "low") {
    label = "Confiance faible";
    classes = "bg-red-100 text-red-600";
  }

  return (
    <span className={`inline-flex items-center rounded-full px-2 py-0.5 text-[10px] font-medium ${classes}`}>
      {label}
    </span>
  );
}

export function ChatMessage({ message, currentUser }) {
  if (!message) return null;

  const isUser = message.role === "user";

  const [showReasoning, setShowReasoning] = useState(false);

  if (isUser) {
    return (
      <div className="flex justify-end gap-2">
        <div className="flex max-w-[75%] flex-col items-end">
          <div className="rounded-2xl rounded-br-sm bg-[#7C3AED] px-4 py-2.5 text-sm text-white shadow-sm">
            <p className="whitespace-pre-wrap break-words">{message.text}</p>
          </div>
          <span className="mt-1 text-[10px] text-[#9CA3AF]">
            {formatTime(message.createdAt)}
          </span>
        </div>
        <div className="mt-0.5">
          <UserAvatar user={currentUser} size={28} />
        </div>
      </div>
    );
  }

  const agentType = message.agentType || "idea_clarifier";
  const meta = getAgentMeta(agentType);
  const structured = message.structured || {};
  const text = message.streamedText || "";

  return (
    <div className="flex items-start gap-3">
      <AgentAvatar agentType={agentType} size={32} />
      <div className="flex-1">
        <div className="flex items-center gap-2">
          <p className="text-xs font-semibold text-[#111827]">{meta.label}</p>
          <Badge variant="violet" className="text-[10px]">
            IA
          </Badge>
        </div>
        <div className="mt-1 rounded-2xl rounded-tl-sm border border-l-4 border-[#E5E7EB] bg-white px-4 py-3 text-xs text-[#111827]">
          <p className="text-[11px] font-medium text-[#4B5563]">
            Voici ce que j&apos;ai compris de votre idée :
          </p>

          <div className="mt-2 space-y-2 text-xs leading-relaxed">
            <div>
              <p className="font-semibold text-[#4B5563]">
                Ce que vous proposez
              </p>
              <p className="mt-0.5 text-[#111827]">
                {structured.understanding?.what}
              </p>
            </div>
            <div>
              <p className="font-semibold text-[#4B5563]">Pour qui ?</p>
              <p className="mt-0.5 text-[#111827]">
                {structured.understanding?.who}
              </p>
            </div>
            <div>
              <p className="font-semibold text-[#4B5563]">Le problème résolu</p>
              <p className="mt-0.5 text-[#111827]">
                {structured.understanding?.problem}
              </p>
            </div>
            {Array.isArray(structured.questions) &&
              structured.questions.length > 0 && (
                <div>
                  <p className="font-semibold text-[#4B5563]">
                    Questions de clarification
                  </p>
                  <ol className="mt-1 list-decimal space-y-0.5 pl-4 text-[#111827]">
                    {structured.questions.map((q, idx) => (
                      <li key={idx}>{q}</li>
                    ))}
                  </ol>
                </div>
              )}
          </div>

          <ClarityScore score={structured.clarity_score} />

          <div className="mt-3 rounded-[8px] bg-[#F9FAFB] p-2.5">
            <div className="flex items-center justify-between gap-2">
              <button
                type="button"
                onClick={() => setShowReasoning((v) => !v)}
                className="text-[11px] font-medium text-[#4F46E5] hover:underline"
              >
                {showReasoning ? "Masquer le raisonnement" : "Pourquoi cette réponse ?"}
              </button>
              <ConfidenceBadge level={structured.confidence} />
            </div>
            {showReasoning && (
              <div className="mt-2 text-[11px] text-[#4B5563]">
                <p>{structured.reasoning}</p>
                {Array.isArray(structured.sources_used) &&
                  structured.sources_used.length > 0 && (
                    <p className="mt-1">
                      <span className="font-medium">Données utilisées : </span>
                      {structured.sources_used.join(", ")}
                    </p>
                  )}
              </div>
            )}
          </div>

          {text && (
            <p className="mt-2 whitespace-pre-wrap text-[11px] text-[#6B7280]">
              {text}
              <span className="inline-block w-1 animate-pulse bg-[#9CA3AF] align-middle" />
            </p>
          )}
        </div>
        <span className="mt-1 inline-block text-[10px] text-[#9CA3AF]">
          {formatTime(message.createdAt)}
        </span>
      </div>
    </div>
  );
}

export default ChatMessage;

