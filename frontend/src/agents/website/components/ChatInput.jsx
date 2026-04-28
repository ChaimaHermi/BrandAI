import { useEffect, useRef, useState } from "react";
import { FiSend } from "react-icons/fi";

const PLACEHOLDERS = {
  loading_context: "Chargement du projet…",
  context_ready: "Cliquez sur « Générer la description » au-dessus.",
  describing: "Génération du concept en cours…",
  description_ready:
    "Discute du concept (ex: « ajoute une section pricing », « hero plus minimaliste »…) puis approuve.",
  refining: "Application de tes retours sur le concept…",
  generating: "Génération du HTML en cours…",
  ready: "Décris une modification (ex: rends le hero plus sombre)",
  revising: "Application de la modification…",
  saving_edits: "Sauvegarde des modifications manuelles…",
  deploying: "Déploiement Vercel en cours…",
  deployed: "Tu peux continuer à modifier le site, je redéploierai à la demande.",
  error: "Une erreur est survenue.",
  idle: "Initialisation…",
};

export function ChatInput({ phase, isBusy, canSubmit, onSubmit }) {
  const [value, setValue] = useState("");
  const taRef = useRef(null);

  useEffect(() => {
    const el = taRef.current;
    if (!el) return;
    el.style.height = "0px";
    el.style.height = `${Math.min(el.scrollHeight, 160)}px`;
  }, [value]);

  const placeholder = PLACEHOLDERS[phase] || PLACEHOLDERS.idle;
  const disabled = !canSubmit || isBusy;

  const handleSubmit = () => {
    const v = value.trim();
    if (!v || disabled) return;
    onSubmit(v);
    setValue("");
  };

  const onKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  return (
    <div className="border-t border-brand-border bg-white px-4 py-3">
      <div
        className={`flex items-end gap-2 rounded-2xl border bg-brand-light/30 px-3 py-2 transition-colors ${
          disabled ? "border-brand-border opacity-70" : "border-brand-muted/40"
        }`}
      >
        <textarea
          ref={taRef}
          value={value}
          onChange={(e) => setValue(e.target.value)}
          onKeyDown={onKeyDown}
          rows={1}
          disabled={disabled}
          placeholder={placeholder}
          className="flex-1 resize-none bg-transparent text-sm leading-relaxed text-ink placeholder:text-ink-subtle focus:outline-none disabled:cursor-not-allowed"
        />
        <button
          type="button"
          onClick={handleSubmit}
          disabled={disabled || !value.trim()}
          className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-gradient-to-br from-brand to-brand-dark text-white shadow-btn transition-all duration-200 hover:-translate-y-px hover:shadow-btn-hover disabled:cursor-not-allowed disabled:opacity-50"
          aria-label="Envoyer"
        >
          <FiSend size={14} />
        </button>
      </div>
      <p className="mt-1.5 px-1 text-2xs text-ink-subtle">
        Entrée pour envoyer · Shift+Entrée pour un saut de ligne
      </p>
    </div>
  );
}

export default ChatInput;
