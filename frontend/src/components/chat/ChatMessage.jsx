import React, { useState } from "react";
import { UserAvatar } from "../ui/UserAvatar";

function formatTime(ts) {
  if (!ts) return "";
  const d = new Date(ts);
  return d.toLocaleTimeString("fr-FR", {
    hour: "2-digit",
    minute: "2-digit",
  });
}

function ClarityBar({ score }) {
  if (typeof score !== "number") return null;
  const color =
    score >= 80 ? "#16A34A" : score >= 55 ? "#7C3AED" : "#DC2626";
  return (
    <div className="mt-2 flex items-center gap-2 rounded-[6px] bg-[#F9FAFB] p-2.5">
      <span className="text-[10px] font-medium text-[#6B7280]">
        Clarity Score
      </span>
      <div className="h-1.5 flex-1 overflow-hidden rounded-full bg-[#E5E7EB]">
        <div
          className="h-full rounded-full"
          style={{ width: `${score}%`, background: color }}
        />
      </div>
      <span className="text-[11px] font-semibold" style={{ color }}>
        {score}/100
      </span>
    </div>
  );
}

function Section({ label, value }) {
  if (!value) return null;
  return (
    <div className="rounded-[6px] bg-[#F9FAFB] p-2.5">
      <p className="text-[10px] font-semibold uppercase tracking-wide text-[#9CA3AF]">
        {label}
      </p>
      <p className="mt-0.5 text-[13px] text-[#111827]">→ {value}</p>
    </div>
  );
}

function ClarifiedSections({ data }) {
  const sections = data.sections || {};
  return (
    <div className="mt-3 flex flex-col gap-2">
      <Section label="Ce que vous proposez" value={sections.what} />
      <Section label="Pour qui ?" value={sections.who} />
      <Section label="Le problème résolu" value={sections.problem} />
      <ClarityBar score={data.score} />
    </div>
  );
}

function QuestionBlocks({ questions }) {
  if (!Array.isArray(questions) || questions.length === 0) return null;
  return (
    <div className="mt-3 flex flex-col gap-2">
      {questions.map((q, i) => (
        <div
          key={i}
          className="flex gap-2 rounded-[6px] bg-[#EDE9FE] p-2.5 text-[13px] text-[#111827]"
        >
          <span className="text-[11px] font-semibold text-[#4C1D95]">
            {i + 1}.
          </span>
          <span>{q}</span>
        </div>
      ))}
    </div>
  );
}

const CATEGORY_LABELS = {
  fraud: "Fraude / Arnaque",
  illegal: "Activité illégale",
  harmful: "Contenu dangereux",
  default: "Non conforme aux CGU",
};

function RefusedBlock({ data }) {
  const categoryLabel =
    CATEGORY_LABELS[data.reason_category] || CATEGORY_LABELS.default;
  const partial = data.partial_understanding || {};

  return (
    <div className="mt-3 flex flex-col gap-2">
      <div className="flex items-center gap-2 rounded-[6px] border border-red-200 bg-red-50 px-3 py-2">
        <span className="text-base text-red-500">⚠</span>
        <span className="text-sm font-medium text-red-700">Idée refusée</span>
        <span className="ml-auto rounded-full bg-red-100 px-2 py-0.5 text-[11px] text-red-600">
          {categoryLabel}
        </span>
      </div>

      {partial.what && (
        <div className="rounded-[6px] bg-[#F9FAFB] p-2.5">
          <p className="text-[10px] font-medium uppercase tracking-wide text-[#9CA3AF]">
            Ce que j&apos;ai compris
          </p>
          <p className="mt-0.5 text-[13px] text-[#374151]">
            → {partial.what}
          </p>
        </div>
      )}
      {partial.who && (
        <div className="rounded-[6px] bg-[#F9FAFB] p-2.5">
          <p className="text-[10px] font-medium uppercase tracking-wide text-[#9CA3AF]">
            Pour qui ?
          </p>
          <p className="mt-0.5 text-[13px] text-[#374151]">
            → {partial.who}
          </p>
        </div>
      )}

      <div className="flex items-center gap-2 rounded-[6px] bg-[#F9FAFB] p-2.5">
        <span className="text-[11px] text-[#6B7280]">Clarity</span>
        <div className="h-1.5 flex-1 overflow-hidden rounded-full bg-[#E5E7EB]">
          <div
            className="h-full rounded-full bg-red-400"
            style={{ width: "0%" }}
          />
        </div>
        <span className="text-[12px] font-medium text-red-500">
          0/100 — Refusé
        </span>
      </div>

      <div className="rounded-[6px] border border-red-200 bg-red-50 p-2.5">
        <p className="text-[12px] text-red-700">
          {data.refusal_message}
        </p>
      </div>

      <div className="flex items-center gap-2 rounded-[6px] border border-[#E5E7EB] bg-[#F9FAFB] px-3 py-2">
        <span className="text-red-500">✗</span>
        <div>
          <p className="text-[12px] font-medium text-[#374151]">
            Pipeline impossible
          </p>
          <p className="text-[11px] text-[#9CA3AF]">
            Objectif : 80/100 pour lancer • Statut actuel : Refusé
          </p>
        </div>
      </div>
    </div>
  );
}

export function ChatMessage({ message, user }) {
  const [xaiOpen, setXaiOpen] = useState(false);
  if (!message) return null;

  if (message.role === "user") {
    return (
      <div className="flex items-end justify-end gap-2">
        <div className="flex max-w-[75%] flex-col items-end">
          <div className="rounded-[16px_16px_4px_16px] bg-[#7C3AED] px-4 py-2.5 text-sm text-white shadow-sm">
            <p className="whitespace-pre-wrap break-words">
              {message.content}
            </p>
          </div>
          <p className="mt-1 text-[10px] text-[#9CA3AF]">
            {formatTime(message.timestamp)}
          </p>
        </div>
        <div className="mt-0.5">
          <UserAvatar user={user} size={28} />
        </div>
      </div>
    );
  }

  const structured = message.structured || {};

  return (
    <div className="flex items-end gap-2">
      <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-[10px] bg-[#7C3AED] text-xs">
        <span role="img" aria-label="clarifier">
          🔍
        </span>
      </div>
      <div className="max-w-[80%]">
        <p className="mb-1 text-[11px] font-semibold text-[#7C3AED]">
          Idea Clarifier
        </p>
        <div className="rounded-[4px_16px_16px_16px] border border-[#E5E7EB] border-l-[3px] border-l-[#7C3AED] bg-white px-4 py-3 text-sm text-[#111827]">
          <p className="whitespace-pre-wrap text-[13px]">
            {message.content}
            {message.isStreaming && (
              <span className="animate-pulse text-[#7C3AED]">▌</span>
            )}
          </p>

          {structured.type === "clarified" && !message.isStreaming && (
            <ClarifiedSections data={structured} />
          )}

          {structured.type === "questions" && !message.isStreaming && (
            <QuestionBlocks questions={structured.questions} />
          )}

          {structured.type === "refused" && !message.isStreaming && (
            <RefusedBlock data={structured} />
          )}
        </div>

        {structured.type === "clarified" && (
          <>
            <button
              type="button"
              onClick={() => setXaiOpen((v) => !v)}
              className="mt-1 inline-flex items-center gap-1 rounded border border-[#E5E7EB] bg-white px-2 py-1 text-[11px] text-[#6B7280] hover:text-[#7C3AED]"
            >
              Pourquoi cette réponse ?
            </button>
            {xaiOpen && (
              <div className="mt-1 rounded-[8px] border border-[#E5E7EB] bg-[#F9FAFB] p-3 text-[11px] text-[#6B7280]">
                <p>
                  J&apos;ai analysé votre description pour identifier clairement le
                  problème, la cible et la solution. Le score reflète à quel
                  point ces trois dimensions sont complètes.
                </p>
                <p className="mt-1">
                  <span className="font-medium">Sources utilisées :</span>{" "}
                  description soumise, secteur et nom du projet.
                </p>
              </div>
            )}
          </>
        )}

        <p className="mt-1 text-[10px] text-[#9CA3AF]">
          {formatTime(message.timestamp)}
        </p>
      </div>
    </div>
  );
}

export default ChatMessage;

