import { useState } from "react";
import {
  FiHeart, FiMessageCircle, FiSend, FiBookmark,
  FiThumbsUp, FiShare2, FiRepeat, FiMoreHorizontal,
  FiCopy, FiCheck, FiImage, FiChevronDown, FiChevronUp,
} from "react-icons/fi";
import { FaInstagram, FaFacebookF, FaLinkedinIn } from "react-icons/fa";
import { CharacterCount } from "./CharacterCount";

/* ── Seuil "Voir plus" (en caractères) ────────────────────────────────────── */
const PREVIEW_LIMIT = 240;

/* ── Méta par plateforme ──────────────────────────────────────────────────── */
const PLATFORM_META = {
  instagram: {
    Icon:        FaInstagram,
    avatarStyle: { background: "linear-gradient(135deg,#833AB4,#E1306C,#FCB045)" },
    username:    "votre_marque",
    handle:      null,
    timeLabel:   "à l'instant",
  },
  facebook: {
    Icon:        FaFacebookF,
    avatarStyle: { background: "#1877F2" },
    username:    "Votre Marque",
    handle:      null,
    timeLabel:   "À l'instant · 🌍",
  },
  linkedin: {
    Icon:        FaLinkedinIn,
    avatarStyle: { background: "#0A66C2" },
    username:    "Votre Marque",
    handle:      "Votre équipe · 1er",
    timeLabel:   "Il y a 1 h · 🌍",
  },
};

/* ── Caption avec bouton "Voir plus / Voir moins" ─────────────────────────── */
function CaptionWithReadMore({ text, prefix }) {
  const [expanded, setExpanded] = useState(false);
  const isLong = text.length > PREVIEW_LIMIT;
  const displayed = !isLong || expanded ? text : text.slice(0, PREVIEW_LIMIT).trimEnd();

  return (
    <p className="whitespace-pre-wrap text-sm leading-relaxed text-ink">
      {prefix && <span className="font-bold">{prefix} </span>}
      {displayed}
      {isLong && !expanded && (
        <>
          {"… "}
          <button
            type="button"
            onClick={() => setExpanded(true)}
            className="inline-flex items-center gap-0.5 text-sm font-semibold text-ink-muted hover:text-ink transition-colors"
          >
            Voir plus <FiChevronDown className="h-3.5 w-3.5" />
          </button>
        </>
      )}
      {isLong && expanded && (
        <>
          {" "}
          <button
            type="button"
            onClick={() => setExpanded(false)}
            className="inline-flex items-center gap-0.5 text-sm font-semibold text-ink-muted hover:text-ink transition-colors"
          >
            Voir moins <FiChevronUp className="h-3.5 w-3.5" />
          </button>
        </>
      )}
    </p>
  );
}

/* ── Actions ──────────────────────────────────────────────────────────────── */
function InstagramActions() {
  return (
    <div className="flex items-center gap-3 px-3 py-2">
      <FiHeart className="h-5 w-5 text-ink-muted" />
      <FiMessageCircle className="h-5 w-5 text-ink-muted" />
      <FiSend className="h-5 w-5 text-ink-muted" />
      <FiBookmark className="ml-auto h-5 w-5 text-ink-muted" />
    </div>
  );
}

function FacebookActions() {
  return (
    <div className="flex items-center divide-x divide-brand-border border-t border-brand-border">
      {[
        { icon: FiThumbsUp, label: "J'aime" },
        { icon: FiMessageCircle, label: "Commenter" },
        { icon: FiShare2, label: "Partager" },
      ].map(({ icon: Icon, label }) => (
        <button key={label} type="button"
          className="flex flex-1 items-center justify-center gap-1.5 py-2 text-xs font-semibold text-ink-muted transition-colors hover:bg-brand-light/30"
        >
          <Icon className="h-4 w-4" /> {label}
        </button>
      ))}
    </div>
  );
}

function LinkedInActions() {
  return (
    <div className="flex items-center divide-x divide-brand-border border-t border-brand-border">
      {[
        { icon: FiThumbsUp, label: "Soutenir" },
        { icon: FiMessageCircle, label: "Commenter" },
        { icon: FiRepeat, label: "Republier" },
        { icon: FiSend, label: "Envoyer" },
      ].map(({ icon: Icon, label }) => (
        <button key={label} type="button"
          className="flex flex-1 items-center justify-center gap-1 py-2 text-[10px] font-semibold text-ink-muted transition-colors hover:bg-brand-light/30"
        >
          <Icon className="h-3.5 w-3.5 shrink-0" />
          <span className="hidden sm:inline">{label}</span>
        </button>
      ))}
    </div>
  );
}

/* ── État vide ────────────────────────────────────────────────────────────── */
function EmptyPreview({ platform, emptyHint }) {
  const meta = PLATFORM_META[platform] || PLATFORM_META.instagram;
  const { Icon, avatarStyle } = meta;
  return (
    <div className="flex flex-1 flex-col items-center justify-center gap-4 rounded-2xl border border-dashed border-brand-border px-6 py-12 text-center">
      <div className="flex h-14 w-14 items-center justify-center rounded-2xl shadow-sm" style={avatarStyle}>
        <Icon className="h-6 w-6 text-white" />
      </div>
      <div>
        <p className="text-sm font-semibold text-ink-muted">{emptyHint}</p>
        <p className="mt-1 max-w-[200px] text-xs text-ink-subtle">
          Le texte et l'image apparaîtront ici après génération.
        </p>
      </div>
    </div>
  );
}

/* ── Composant principal ──────────────────────────────────────────────────── */
export function PostPreviewPanel({ platform, caption, imageUrl, emptyHint }) {
  const [copied, setCopied] = useState(false);
  const hasCaption = (caption || "").trim().length > 0;
  const meta  = PLATFORM_META[platform] || PLATFORM_META.instagram;

  function handleCopy() {
    if (!caption) return;
    navigator.clipboard.writeText(caption).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    });
  }

  return (
    <div className="flex h-full min-h-[320px] flex-col gap-3">
      {/* Titre « Aperçu — … » géré par le parent (carte / modal) pour éviter le doublon */}

      {hasCaption && (
        <div className="flex justify-end">
          <button
            type="button"
            onClick={handleCopy}
            className="inline-flex items-center gap-1 rounded-full border border-brand-border bg-white px-2.5 py-1 text-2xs font-semibold text-ink-muted transition-all hover:border-brand-muted hover:text-brand-dark"
          >
            {copied
              ? <><FiCheck className="h-3 w-3 text-success" /> Copié</>
              : <><FiCopy className="h-3 w-3" /> Copier</>
            }
          </button>
        </div>
      )}

      {/* Contenu */}
      {!hasCaption && !imageUrl ? (
        <EmptyPreview platform={platform} emptyHint={emptyHint} />
      ) : (
        <div className="flex flex-col gap-3">
          <div className="rounded-2xl border border-brand-border bg-white shadow-card">

            {/* Header post */}
            <div className="flex items-center gap-2.5 px-3 py-3">
              <div
                className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full text-xs font-bold text-white"
                style={meta.avatarStyle}
              >
                {meta.username.slice(0, 2).toUpperCase()}
              </div>
              <div className="min-w-0 flex-1">
                <p className="text-xs font-bold text-ink leading-tight">{meta.username}</p>
                {meta.handle && (
                  <p className="text-2xs text-ink-subtle leading-tight">{meta.handle}</p>
                )}
                <p className="text-2xs text-ink-subtle leading-tight">{meta.timeLabel}</p>
              </div>
              <div className="flex items-center gap-2">
                <div className="flex h-6 w-6 items-center justify-center rounded-full" style={meta.avatarStyle}>
                  <meta.Icon className="h-3 w-3 text-white" />
                </div>
                <FiMoreHorizontal className="h-4 w-4 text-ink-subtle" />
              </div>
            </div>

            {/* Caption Facebook / LinkedIn (avant l'image) */}
            {hasCaption && platform !== "instagram" && (
              <div className="px-3 pb-3">
                <CaptionWithReadMore text={caption} />
              </div>
            )}

            {/* Image — affichage complet sans crop */}
            {imageUrl && (
              <div className="border-y border-brand-border bg-brand-light/10">
                <img
                  src={imageUrl}
                  alt="Visuel du post"
                  className="w-full h-auto"
                />
              </div>
            )}

            {/* Placeholder Instagram sans image */}
            {!imageUrl && platform === "instagram" && (
              <div className="flex h-48 items-center justify-center border-y border-dashed border-brand-border bg-brand-light/20">
                <div className="flex flex-col items-center gap-2 text-ink-subtle">
                  <FiImage className="h-8 w-8" />
                  <span className="text-xs">Image non générée</span>
                </div>
              </div>
            )}

            {/* Actions Instagram */}
            {platform === "instagram" && <InstagramActions />}

            {/* Caption Instagram (après les actions) */}
            {hasCaption && platform === "instagram" && (
              <div className="px-3 pb-3">
                <CaptionWithReadMore text={caption} prefix={meta.username} />
              </div>
            )}

            {/* Actions Facebook */}
            {platform === "facebook" && <FacebookActions />}

            {/* Actions LinkedIn */}
            {platform === "linkedin" && <LinkedInActions />}
          </div>

          {/* Compteur de caractères */}
          {hasCaption && (
            <CharacterCount text={caption} platform={platform} />
          )}
        </div>
      )}
    </div>
  );
}

export default PostPreviewPanel;
