/**
 * Utilitaires partagés de sanitisation HTML pour le Website Builder.
 * Utilisés par useWebsiteBuilder.js (stockage) et PreviewPanel.jsx (rendu iframe).
 */

const INJECTION_START = "<!-- BRANDAI_PREVIEW_INJECTION_START -->";
const INJECTION_END = "<!-- BRANDAI_PREVIEW_INJECTION_END -->";

const INJECTION_SCRIPT_TOKENS = [
  "BRANDAI_PREVIEW_READY",
  "BRANDAI_EDIT_MODE_ON",
  "BRANDAI_EDIT_MODE_OFF",
  "BRANDAI_HTML_UPDATE",
  "BRANDAI_REQUEST_HTML",
  "__brandai_edit_mode__",
  "data-brandai-editable",
  "__brandai_edit_styles__",
  "data-img-fallback",
  "isUnsafeNav",
];

const LEAKED_INJECTION_HEADS = [
  "ensureStyles",
  "removeStyles",
  "enableEditMode",
  "disableEditMode",
  "sendHtmlUpdate",
  "scheduleHtmlUpdate",
];

function removeOrphanClosingScriptTags(html) {
  let result = "";
  let i = 0;
  let openCount = 0;
  while (i < html.length) {
    if (html.substring(i, i + 8).match(/^<script\b/i)) {
      const closeIdx = html.indexOf(">", i);
      if (closeIdx < 0) { result += html.substring(i); break; }
      result += html.substring(i, closeIdx + 1);
      i = closeIdx + 1;
      openCount += 1;
      continue;
    }
    const closeMatch = html.substring(i, i + 12).match(/^<\/script\s*>/i);
    if (closeMatch) {
      if (openCount > 0) { result += closeMatch[0]; openCount -= 1; }
      i += closeMatch[0].length;
      continue;
    }
    result += html[i];
    i += 1;
  }
  return result;
}

function stripLeakedInjectionText(html) {
  if (!html) return html || "";
  let cleaned = html;
  cleaned = cleaned.replace(
    /\(\s*\(\s*\)\s*=>\s*\{[\s\S]*?\}\s*\)\s*\(\s*\)\s*;?/g,
    (match) => INJECTION_SCRIPT_TOKENS.some((s) => match.includes(s)) ? "" : match
  );
  for (const head of LEAKED_INJECTION_HEADS) {
    const re = new RegExp(`\\bconst\\s+${head}\\s*=[\\s\\S]*?\\}\\s*\\)\\s*\\(\\s*\\)\\s*;?`, "g");
    cleaned = cleaned.replace(re, (match) =>
      INJECTION_SCRIPT_TOKENS.some((s) => match.includes(s)) ? "" : match
    );
  }
  return removeOrphanClosingScriptTags(cleaned);
}

/**
 * Retire tous les artefacts injectés par le preview (scripts, styles, attributs).
 * Utilisé avant de stocker ou d'afficher le HTML.
 */
export function stripInjectionArtifacts(rawHtml) {
  if (!rawHtml || typeof rawHtml !== "string") return "";
  let cleaned = rawHtml;

  // 1) Blocs entre marqueurs explicites.
  while (true) {
    const start = cleaned.indexOf(INJECTION_START);
    if (start < 0) break;
    const end = cleaned.indexOf(INJECTION_END, start + INJECTION_START.length);
    if (end < 0) break;
    cleaned = cleaned.slice(0, start) + cleaned.slice(end + INJECTION_END.length);
  }

  // 2) Scripts d'injection orphelins (sans marqueurs).
  cleaned = cleaned.replace(/<script\b[^>]*>([\s\S]*?)<\/script\s*>/gi, (match, body) =>
    INJECTION_SCRIPT_TOKENS.some((t) => body.includes(t)) ? "" : match
  );

  // 3) Code JS d'injection qui a fuité hors <script>.
  cleaned = stripLeakedInjectionText(cleaned);

  // 4) Style d'édition oublié.
  cleaned = cleaned.replace(
    /<style[^>]*id\s*=\s*["']__brandai_edit_styles__["'][^>]*>[\s\S]*?<\/style\s*>/gi, ""
  );

  // 5) Attributs résiduels du mode édition.
  cleaned = cleaned
    .replace(/\s+contenteditable\s*=\s*["']true["']/gi, "")
    .replace(/\s+data-brandai-editable\s*=\s*["']1["']/gi, "")
    .replace(/\s+data-brandai-edit-mode\s*=\s*["']1["']/gi, "");

  // 6) Marqueurs orphelins.
  cleaned = cleaned
    .replace(/<!--\s*BRANDAI_PREVIEW_INJECTION_START\s*-->/g, "")
    .replace(/<!--\s*BRANDAI_PREVIEW_INJECTION_END\s*-->/g, "");

  // 7) Fermetures </body></html> dupliquées.
  cleaned = cleaned.replace(/(\s*<\/body>\s*<\/html>\s*){2,}/gi, "\n</body>\n</html>");

  return cleaned.trim();
}

/**
 * Normalise un HTML : retire les artefacts, enveloppe un fragment si nécessaire.
 */
export function normalizeHtml(rawHtml) {
  const raw = String(rawHtml || "");
  const sanitized = stripInjectionArtifacts(raw);
  const trimmed = (sanitized || raw).trim();
  if (!trimmed) return "";

  const lower = trimmed.toLowerCase();
  if (lower.includes("<html") && lower.includes("<body") && lower.includes("</html>")) {
    return trimmed;
  }

  return `<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Website Preview</title>
</head>
<body>
${trimmed}
</body>
</html>`;
}

export function computeHtmlStats(rawHtml) {
  const html = String(rawHtml || "");
  return {
    length: html.length,
    approx_lines: (html.match(/\n/g) || []).length + 1,
  };
}
