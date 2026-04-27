import { useEffect, useRef } from "react";
import { FiGlobe, FiCpu } from "react-icons/fi";
import { ChatMessage } from "./ChatMessage";
import { ChatInput } from "./ChatInput";

const PHASE_LABEL = {
  idle: "Initialisation",
  loading_context: "Chargement du contexte…",
  context_ready: "Contexte prêt",
  describing: "Création du concept…",
  description_ready: "Concept prêt",
  generating: "Génération du HTML…",
  ready: "Site prêt",
  revising: "Modification en cours…",
  deploying: "Déploiement Vercel…",
  deployed: "Site en ligne",
  error: "Erreur",
};

const PHASE_INDEX = {
  idle: 0,
  loading_context: 1,
  context_ready: 1,
  describing: 2,
  description_ready: 2,
  generating: 3,
  ready: 3,
  revising: 3,
  deploying: 4,
  deployed: 5,
  error: 0,
};

function PhaseHeader({ phase, isBusy }) {
  const label = PHASE_LABEL[phase] || "—";
  const idx = PHASE_INDEX[phase] || 0;
  const total = 5;
  return (
    <div className="flex items-center gap-3 border-b border-brand-border bg-white px-4 py-3">
      <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-gradient-to-br from-brand to-brand-dark text-white shadow-pill">
        <FiGlobe size={14} />
      </span>
      <div className="min-w-0 flex-1">
        <p className="text-xs font-extrabold text-ink">Website Builder</p>
        <p className="flex items-center gap-1.5 text-2xs text-ink-subtle">
          {isBusy && (
            <FiCpu size={10} className="animate-spin text-brand" />
          )}
          {label} · Étape {Math.max(1, idx)}/{total}
        </p>
      </div>
      <div className="flex items-center gap-1.5">
        <div className="h-[5px] w-20 overflow-hidden rounded-full bg-brand-light">
          <div
            className="h-full rounded-full bg-gradient-to-r from-brand to-brand-dark transition-[width] duration-500"
            style={{ width: `${(idx / total) * 100}%` }}
          />
        </div>
        <span className="text-2xs font-bold text-brand-dark">
          {Math.round((idx / total) * 100)}%
        </span>
      </div>
    </div>
  );
}

function TypingBubble() {
  return (
    <div className="flex items-start gap-2">
      <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-gradient-to-br from-brand to-brand-dark text-white shadow-pill">
        <FiGlobe size={13} />
      </span>
      <div className="rounded-2xl rounded-tl-md border border-brand-border bg-white px-4 py-3 shadow-card">
        <div className="flex items-center gap-1.5">
          <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-brand [animation-delay:-0.3s]" />
          <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-brand [animation-delay:-0.15s]" />
          <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-brand" />
        </div>
      </div>
    </div>
  );
}

export function ChatPanel({
  phase,
  isBusy,
  canChatRevise,
  messages,
  onAction,
  onSubmit,
}) {
  const scrollRef = useRef(null);

  useEffect(() => {
    const el = scrollRef.current;
    if (!el) return;
    el.scrollTop = el.scrollHeight;
  }, [messages, isBusy]);

  return (
    <div className="flex h-full flex-col overflow-hidden rounded-2xl border border-brand-border bg-white shadow-card">
      <PhaseHeader phase={phase} isBusy={isBusy} />

      <div
        ref={scrollRef}
        className="flex-1 overflow-y-auto bg-gradient-to-b from-brand-light/20 to-white px-4 py-4"
      >
        <div className="flex flex-col gap-3">
          {messages.map((m) => (
            <ChatMessage
              key={m.id}
              msg={m}
              onAction={onAction}
              busy={isBusy}
            />
          ))}
          {isBusy && <TypingBubble />}
        </div>
      </div>

      <ChatInput
        phase={phase}
        isBusy={isBusy}
        canSubmit={canChatRevise}
        onSubmit={onSubmit}
      />
    </div>
  );
}

export default ChatPanel;
