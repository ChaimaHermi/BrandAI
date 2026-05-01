import {
  FiGlobe,
  FiUser,
  FiAlertCircle,
  FiBriefcase,
  FiUsers,
  FiType,
  FiDroplet,
  FiLayers,
  FiZap,
  FiMessageSquare,
  FiCheck,
  FiLoader,
  FiClock,
  FiXCircle,
} from "react-icons/fi";
import { MiniMarkdown } from "../utils/miniMarkdown";

function PhasePill({ label }) {
  if (!label) return null;
  return (
    <span className="self-start rounded-full bg-brand-light px-2 py-0.5 text-2xs font-bold uppercase tracking-wider text-brand-darker">
      {label}
    </span>
  );
}

/**
 * Carte "XAI" affichée pendant qu'une opération SSE tourne. Liste les étapes
 * reçues et affiche un tick "live" sous l'étape en cours.
 */
function StreamCard({ msg }) {
  const steps = Array.isArray(msg.streamSteps) ? msg.streamSteps : [];
  const tick = msg.streamTick;
  const status = msg.streamStatus || "running";
  const errorMsg = msg.streamError;

  const dotIcon = (s) => {
    if (s.status === "done") {
      return <FiCheck size={11} className="text-success" />;
    }
    return <FiLoader size={11} className="animate-spin text-brand" />;
  };

  return (
    <div className="flex items-start gap-2 animate-[slideUp_0.25s_ease_forwards]">
      <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-gradient-to-br from-brand to-brand-dark text-white shadow-pill">
        <FiGlobe size={13} />
      </span>
      <div className="flex max-w-[90%] flex-col gap-2 rounded-2xl rounded-tl-md border border-brand-border bg-white px-4 py-3 shadow-card">
        <div className="flex items-center gap-2">
          <span
            className={`inline-flex h-5 w-5 items-center justify-center rounded-full ${
              status === "done"
                ? "bg-success/15 text-success"
                : status === "error"
                  ? "bg-red-100 text-red-600"
                  : "bg-brand-light text-brand-dark"
            }`}
          >
            {status === "done" ? (
              <FiCheck size={12} />
            ) : status === "error" ? (
              <FiXCircle size={12} />
            ) : (
              <FiLoader size={12} className="animate-spin" />
            )}
          </span>
          <p className="text-2xs font-extrabold uppercase tracking-wider text-brand-darker">
            {msg.streamTitle || "Opération en cours"}
          </p>
        </div>

        {steps.length === 0 && status === "running" && (
          <p className="text-xs text-ink-muted">
            Initialisation de l'agent…
          </p>
        )}

        {steps.length > 0 && (
          <ol className="flex flex-col gap-1.5">
            {steps.map((s) => (
              <li
                key={s.id}
                className={`flex items-start gap-2 rounded-md px-2 py-1.5 text-xs ${
                  s.status === "done"
                    ? "bg-success/5 text-ink"
                    : "bg-brand-light/40 text-ink"
                }`}
              >
                <span className="mt-0.5 inline-flex h-4 w-4 shrink-0 items-center justify-center">
                  {dotIcon(s)}
                </span>
                <span className="flex-1 leading-tight">
                  <span className="font-semibold">{s.label}</span>
                  {s.meta && typeof s.meta === "object" && (
                    <span className="ml-2 text-2xs text-ink-subtle">
                      {Object.entries(s.meta)
                        .filter(([, v]) => typeof v === "string" || typeof v === "number")
                        .slice(0, 4)
                        .map(([k, v]) => `${k}: ${v}`)
                        .join(" · ")}
                    </span>
                  )}
                </span>
              </li>
            ))}
          </ol>
        )}

        {status === "running" && tick && tick.label && (
          <div className="flex items-center gap-2 rounded-lg border border-brand-border bg-brand-light/20 px-2.5 py-1.5">
            <FiClock size={11} className="shrink-0 animate-pulse text-brand" />
            <span className="text-2xs italic text-ink-muted">
              {tick.label}
              {tick.elapsed > 0 ? ` · ${tick.elapsed}s` : ""}
            </span>
          </div>
        )}

        {status === "error" && errorMsg && (
          <div className="rounded-lg border border-red-200 bg-red-50 px-2.5 py-1.5">
            <p className="text-2xs font-semibold text-red-700">{errorMsg}</p>
          </div>
        )}
      </div>
    </div>
  );
}

function ActionButtons({ actions, onAction, disabled }) {
  if (!actions || actions.length === 0) return null;
  return (
    <div className="mt-2 flex flex-wrap gap-2">
      {actions.map((a) => (
        <button
          key={a.id}
          type="button"
          disabled={disabled}
          onClick={() => onAction?.(a.id)}
          className="inline-flex items-center gap-1.5 rounded-full bg-gradient-to-br from-brand to-brand-dark px-3 py-1.5 text-xs font-semibold text-white shadow-btn transition-all duration-200 hover:-translate-y-px hover:shadow-btn-hover disabled:cursor-not-allowed disabled:opacity-50"
        >
          {a.label}
        </button>
      ))}
    </div>
  );
}

function DeploymentCard({ deployment }) {
  if (!deployment) return null;
  const url = deployment.full_url || (deployment.url ? `https://${deployment.url}` : null);
  if (!url) return null;
  return (
    <a
      href={url}
      target="_blank"
      rel="noopener noreferrer"
      className="mt-2 flex items-center gap-3 rounded-xl border border-success/30 bg-success/5 px-3 py-2.5 transition-all duration-200 hover:-translate-y-px hover:bg-success/10"
    >
      <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-success">
        <FiGlobe size={16} className="text-white" />
      </span>
      <div className="min-w-0 flex-1">
        <p className="truncate text-2xs font-bold uppercase tracking-wider text-success">
          Site en ligne
        </p>
        <p className="truncate text-xs font-semibold text-ink">{url}</p>
      </div>
      <svg width="14" height="14" viewBox="0 0 16 16" fill="none">
        <path d="M3 8h10M10 5l3 3-3 3" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" className="text-success" />
      </svg>
    </a>
  );
}

function JsonBlock({ value }) {
  if (!value || typeof value !== "object") return null;
  return (
    <div className="mt-2 overflow-hidden rounded-xl border border-brand-border bg-slate-950">
      <div className="border-b border-slate-800 bg-slate-900 px-3 py-1.5 text-2xs font-semibold text-slate-300">
        JSON
      </div>
      <pre className="max-h-72 overflow-auto px-3 py-2 text-2xs leading-relaxed text-slate-100">
        {JSON.stringify(value, null, 2)}
      </pre>
    </div>
  );
}

function TagList({ text }) {
  const items = String(text || "")
    .split(",")
    .map((s) => s.trim())
    .filter(Boolean);
  if (!items.length) return null;
  return (
    <div className="mt-1.5 flex flex-wrap gap-1.5">
      {items.map((t, idx) => (
        <span
          key={`${t}-${idx}`}
          className="rounded-full border border-brand-border bg-brand-light px-2 py-0.5 text-2xs font-semibold text-brand-darker"
        >
          {t}
        </span>
      ))}
    </div>
  );
}

function DescriptionStructuredCard({ data }) {
  if (!data || typeof data !== "object") return null;
  const sections = Array.isArray(data.sections) ? data.sections : [];
  const animations = Array.isArray(data.animations) ? data.animations : [];
  const hasCore = data.hero_concept || sections.length || animations.length;
  if (!hasCore) return null;

  return (
    <div className="mt-2 rounded-xl border border-brand-border bg-white p-3">
      <p className="mb-2 text-2xs font-extrabold uppercase tracking-wider text-brand-darker">
        Concept du site
      </p>

      {data.hero_concept && (
        <div className="rounded-lg border border-brand-border bg-brand-light/20 p-2.5">
          <p className="text-2xs font-semibold uppercase tracking-wider text-ink-subtle">Hero concept</p>
          <p className="mt-1 text-xs leading-relaxed text-ink">{data.hero_concept}</p>
        </div>
      )}

      {data.visual_style && (
        <div className="mt-3 rounded-lg border border-brand-border bg-white p-2.5">
          <p className="inline-flex items-center gap-1 text-2xs font-semibold uppercase tracking-wider text-ink-subtle">
            <FiLayers size={11} />
            Style visuel
          </p>
          <TagList text={data.visual_style} />
        </div>
      )}

      {sections.length > 0 && (
        <div className="mt-3">
          <p className="mb-1.5 text-2xs font-semibold uppercase tracking-wider text-ink-subtle">
            Sections proposées
          </p>
          <div className="space-y-2">
            {sections.map((s, idx) => (
              <div key={`${s?.id || "sec"}-${idx}`} className="rounded-lg border border-brand-border bg-white p-2.5">
                <p className="text-xs font-bold text-ink">
                  {s?.title || s?.id || `Section ${idx + 1}`}
                </p>
                {s?.purpose && <p className="mt-1 text-xs text-ink-muted">{s.purpose}</p>}
                {Array.isArray(s?.key_elements) && s.key_elements.length > 0 && (
                  <ul className="mt-1.5 ml-4 list-disc space-y-0.5 text-2xs text-ink">
                    {s.key_elements.map((el, i) => (
                      <li key={i}>{el}</li>
                    ))}
                  </ul>
                )}
                {s?.creative_touch && (
                  <p className="mt-1.5 rounded-md bg-brand-light/40 px-2 py-1 text-2xs text-ink">
                    {s.creative_touch}
                  </p>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {animations.length > 0 && (
        <div className="mt-3 rounded-lg border border-brand-border bg-white p-2.5">
          <p className="inline-flex items-center gap-1 text-2xs font-semibold uppercase tracking-wider text-ink-subtle">
            <FiZap size={11} />
            Animations
          </p>
          <ul className="mt-1.5 ml-4 list-decimal space-y-0.5 text-2xs text-ink">
            {animations.map((a, i) => (
              <li key={i}>{a}</li>
            ))}
          </ul>
        </div>
      )}

      {(data.typography_pairing || data.tone_of_voice || data.user_summary) && (
        <div className="mt-3 space-y-2">
          {data.typography_pairing && (
            <div className="rounded-lg border border-brand-border bg-white p-2.5">
              <p className="text-2xs font-semibold uppercase tracking-wider text-ink-subtle">Typographie</p>
              <p className="mt-1 text-2xs text-ink">{data.typography_pairing}</p>
            </div>
          )}
          {data.tone_of_voice && (
            <div className="rounded-lg border border-brand-border bg-white p-2.5">
              <p className="text-2xs font-semibold uppercase tracking-wider text-ink-subtle">Ton de voix</p>
              <p className="mt-1 text-2xs text-ink">{data.tone_of_voice}</p>
            </div>
          )}
          {data.user_summary && (
            <div className="rounded-lg border border-brand-border bg-brand-light/20 p-2.5">
              <p className="inline-flex items-center gap-1 text-2xs font-semibold uppercase tracking-wider text-ink-subtle">
                <FiMessageSquare size={11} />
                Résumé final
              </p>
              <p className="mt-1 text-xs leading-relaxed text-ink">{data.user_summary}</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// eslint-disable-next-line no-unused-vars
function ContextItem({ icon: IconComp, label, value }) {
  if (!value) return null;
  return (
    <div className="flex items-start gap-2 rounded-lg border border-brand-border bg-brand-light/30 px-2.5 py-2">
      <span className="mt-0.5 text-brand">
        <IconComp size={12} />
      </span>
      <div className="min-w-0">
        <p className="text-2xs font-semibold uppercase tracking-wider text-ink-subtle">{label}</p>
        <p className="mt-0.5 break-words text-xs font-medium text-ink">{value}</p>
      </div>
    </div>
  );
}

function ColorSwatch({ name, hex }) {
  if (!hex) return null;
  return (
    <div className="flex items-center gap-1.5 rounded-full border border-brand-border bg-white px-2 py-1">
      <span
        className="h-3 w-3 rounded-full border border-black/10"
        style={{ backgroundColor: hex }}
        title={hex}
      />
      <span className="text-2xs font-semibold text-ink">{name}</span>
    </div>
  );
}

function ContextCard({ context }) {
  if (!context || typeof context !== "object") return null;
  const rawLogo = context.raw_logo && typeof context.raw_logo === "object" ? context.raw_logo : null;
  const rawSvgData =
    rawLogo && typeof rawLogo.svg_data === "string" && rawLogo.svg_data.trim().startsWith("<svg")
      ? rawLogo.svg_data.trim()
      : null;
  const svgDataUrl = rawSvgData
    ? `data:image/svg+xml;base64,${btoa(unescape(encodeURIComponent(rawSvgData)))}`
    : null;
  const logoUrl = context.logo_url || svgDataUrl || null;

  return (
    <div className="mt-2 rounded-xl border border-brand-border bg-white p-3">
      <p className="mb-2 text-2xs font-extrabold uppercase tracking-wider text-brand-darker">
        Résumé Projet
      </p>
      <div className="grid gap-2 md:grid-cols-2">
        <ContextItem
          icon={FiBriefcase}
          label="Projet"
          value={context.project_name || context.brand_name}
        />
        <ContextItem
          icon={FiUsers}
          label="Cible"
          value={context.target_audience}
        />
        <ContextItem
          icon={FiType}
          label="Style visuel"
          value={context.visual_style}
        />
        <ContextItem
          icon={FiType}
          label="Polices"
          value={`${context.title_font || "Titre"} / ${context.body_font || "Corps"}`}
        />
        <ContextItem
          icon={FiType}
          label="Slogan"
          value={context.slogan}
        />
        <ContextItem
          icon={FiType}
          label="Pitch Clarifier"
          value={context.short_pitch}
        />
      </div>

      <div className="mt-3 rounded-lg border border-brand-border bg-brand-light/20 p-2.5">
        <p className="mb-1 text-2xs font-semibold uppercase tracking-wider text-ink-subtle">
          Solution proposée (Clarifier)
        </p>
        <p className="text-xs leading-relaxed text-ink">
          {context.description_brief || "Non disponible"}
        </p>
      </div>

      <div className="mt-3">
        <p className="mb-1.5 inline-flex items-center gap-1 text-2xs font-semibold uppercase tracking-wider text-ink-subtle">
          <FiDroplet size={11} />
          Palette
        </p>
        <div className="flex flex-wrap gap-1.5">
          <ColorSwatch name="Primary" hex={context.primary_color} />
          <ColorSwatch name="Secondary" hex={context.secondary_color} />
          <ColorSwatch name="Accent" hex={context.accent_color} />
          <ColorSwatch name="Background" hex={context.background_color} />
          <ColorSwatch name="Text" hex={context.text_color} />
        </div>
      </div>

      <div className="mt-3 rounded-lg border border-brand-border bg-white p-2.5">
        <p className="mb-1 text-2xs font-semibold uppercase tracking-wider text-ink-subtle">
          Logo
        </p>
        {logoUrl ? (
          <div className="flex items-center gap-2">
            <div className="flex h-12 w-12 items-center justify-center overflow-hidden rounded-lg border border-brand-border bg-white">
              <img
                src={logoUrl}
                alt={context.brand_name || "Logo"}
                className="max-h-full max-w-full object-contain"
                loading="lazy"
                referrerPolicy="no-referrer"
              />
            </div>
            {String(logoUrl).startsWith("http") ? (
              <a
                href={logoUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="text-2xs font-semibold text-brand underline decoration-brand/40 underline-offset-2 hover:text-brand-dark"
              >
                Ouvrir le logo
              </a>
            ) : (
              <span className="text-2xs font-semibold text-ink-subtle">Logo SVG (base locale)</span>
            )}
          </div>
        ) : (
          <p className="text-xs text-ink-subtle">Aucun logo disponible</p>
        )}
      </div>
    </div>
  );
}

export function ChatMessage({ msg, onAction, busy }) {
  if (msg.role === "system") {
    const isError = msg.kind === "error";
    return (
      <div
        className={`mx-auto max-w-[90%] rounded-lg border px-3 py-2 text-2xs ${
          isError
            ? "border-red-200 bg-red-50 text-red-700"
            : "border-brand-border bg-brand-light/50 text-ink-muted"
        }`}
      >
        <div className="flex items-center gap-2">
          {isError && <FiAlertCircle className="h-3.5 w-3.5 shrink-0" />}
          <span className="break-words">{msg.content}</span>
        </div>
      </div>
    );
  }

  if (msg.role === "user") {
    return (
      <div className="flex items-end justify-end gap-2 animate-[slideUp_0.25s_ease_forwards]">
        <div className="max-w-[85%] rounded-2xl rounded-br-md bg-gradient-to-br from-brand to-brand-dark px-4 py-2.5 shadow-pill">
          <p className="whitespace-pre-wrap break-words text-sm text-white">
            {msg.content}
          </p>
        </div>
        <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-brand-light text-brand-darker">
          <FiUser size={13} />
        </span>
      </div>
    );
  }

  if (msg.kind === "stream") {
    return <StreamCard msg={msg} />;
  }

  const isDescriptionJsonCard = msg.title === "Description complète (JSON)";

  // bot
  return (
    <div className="flex items-start gap-2 animate-[slideUp_0.25s_ease_forwards]">
      <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-gradient-to-br from-brand to-brand-dark text-white shadow-pill">
        <FiGlobe size={13} />
      </span>
      <div className="flex max-w-[85%] flex-col gap-1.5 rounded-2xl rounded-tl-md border border-brand-border bg-white px-4 py-2.5 shadow-card">
        <PhasePill label={msg.title} />
        <MiniMarkdown text={msg.content} />
        <ContextCard context={msg.context} />
        {isDescriptionJsonCard ? (
          <DescriptionStructuredCard data={msg.json} />
        ) : (
          <JsonBlock value={msg.json} />
        )}
        <DeploymentCard deployment={msg.deployment} />
        <ActionButtons actions={msg.actions} onAction={onAction} disabled={busy} />
      </div>
    </div>
  );
}

export default ChatMessage;
