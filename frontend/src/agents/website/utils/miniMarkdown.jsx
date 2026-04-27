/**
 * Mini renderer Markdown — assez pour les résumés du backend.
 * Gère : headings (#, ##, ###), listes (-, *, 1.), gras **, italique *,
 * code inline `...`, liens [label](url), citations >, lignes vides.
 *
 * On ne tire AUCUNE dépendance externe : tout est en React natif et sûr
 * (aucune injection HTML, on construit des nodes React).
 */

import React from "react";

// ── Inline parser ────────────────────────────────────────────────────────────
// Ordre : code > link > bold > italic
const INLINE_RE = /(`[^`]+`)|(\[[^\]]+\]\([^)]+\))|(\*\*[^*]+\*\*)|(\*[^*]+\*)/g;

function renderInline(text) {
  if (!text) return null;
  const out = [];
  let lastIndex = 0;
  let match;
  let key = 0;

  INLINE_RE.lastIndex = 0;
  while ((match = INLINE_RE.exec(text)) !== null) {
    const [token] = match;
    const start = match.index;
    if (start > lastIndex) {
      out.push(text.slice(lastIndex, start));
    }

    if (token.startsWith("`") && token.endsWith("`")) {
      out.push(
        <code
          key={`c-${key++}`}
          className="rounded bg-brand-light px-1 py-0.5 font-mono text-2xs text-brand-darker"
        >
          {token.slice(1, -1)}
        </code>
      );
    } else if (token.startsWith("[")) {
      const closeBracket = token.indexOf("](");
      const label = token.slice(1, closeBracket);
      const href = token.slice(closeBracket + 2, -1);
      out.push(
        <a
          key={`a-${key++}`}
          href={href}
          target="_blank"
          rel="noopener noreferrer"
          className="text-brand underline decoration-brand/40 underline-offset-2 hover:text-brand-dark"
        >
          {label}
        </a>
      );
    } else if (token.startsWith("**")) {
      out.push(
        <strong key={`b-${key++}`} className="font-bold text-ink">
          {token.slice(2, -2)}
        </strong>
      );
    } else if (token.startsWith("*")) {
      out.push(
        <em key={`i-${key++}`} className="italic">
          {token.slice(1, -1)}
        </em>
      );
    } else {
      out.push(token);
    }
    lastIndex = start + token.length;
  }
  if (lastIndex < text.length) {
    out.push(text.slice(lastIndex));
  }
  return out;
}

// ── Block parser ─────────────────────────────────────────────────────────────
export function MiniMarkdown({ text, className = "" }) {
  if (!text) return null;

  const lines = String(text).replace(/\r\n/g, "\n").split("\n");
  const blocks = [];
  let listBuffer = null; // { ordered: bool, items: [] }
  let key = 0;

  const flushList = () => {
    if (!listBuffer) return;
    const Tag = listBuffer.ordered ? "ol" : "ul";
    blocks.push(
      <Tag
        key={`list-${key++}`}
        className={
          listBuffer.ordered
            ? "ml-5 list-decimal space-y-1 text-sm leading-relaxed text-ink"
            : "ml-5 list-disc space-y-1 text-sm leading-relaxed text-ink"
        }
      >
        {listBuffer.items.map((it, i) => (
          <li key={i}>{renderInline(it)}</li>
        ))}
      </Tag>
    );
    listBuffer = null;
  };

  for (const rawLine of lines) {
    const line = rawLine;

    if (line.trim() === "") {
      flushList();
      continue;
    }

    // Headings
    const h = line.match(/^(#{1,3})\s+(.*)$/);
    if (h) {
      flushList();
      const level = h[1].length;
      const content = h[2];
      const cls =
        level === 1
          ? "text-base font-extrabold text-ink"
          : level === 2
            ? "text-sm font-bold text-ink"
            : "text-sm font-semibold text-ink";
      const Tag = `h${level + 2}`; // h3/h4/h5 in DOM (no h1 in chat)
      blocks.push(
        <Tag key={`h-${key++}`} className={cls}>
          {renderInline(content)}
        </Tag>
      );
      continue;
    }

    // Quote
    if (line.startsWith("> ")) {
      flushList();
      blocks.push(
        <blockquote
          key={`q-${key++}`}
          className="border-l-2 border-brand-muted pl-3 text-xs italic text-ink-muted"
        >
          {renderInline(line.slice(2))}
        </blockquote>
      );
      continue;
    }

    // Unordered list
    const u = line.match(/^\s*[-*]\s+(.*)$/);
    if (u) {
      if (!listBuffer || listBuffer.ordered) {
        flushList();
        listBuffer = { ordered: false, items: [] };
      }
      listBuffer.items.push(u[1]);
      continue;
    }

    // Ordered list
    const o = line.match(/^\s*\d+\.\s+(.*)$/);
    if (o) {
      if (!listBuffer || !listBuffer.ordered) {
        flushList();
        listBuffer = { ordered: true, items: [] };
      }
      listBuffer.items.push(o[1]);
      continue;
    }

    // Paragraph (italic _meta_ via single underscore wrapper for the deployment summary)
    flushList();
    blocks.push(
      <p key={`p-${key++}`} className="text-sm leading-relaxed text-ink">
        {renderInline(line)}
      </p>
    );
  }
  flushList();

  return <div className={`flex flex-col gap-2 ${className}`}>{blocks}</div>;
}

export default MiniMarkdown;
