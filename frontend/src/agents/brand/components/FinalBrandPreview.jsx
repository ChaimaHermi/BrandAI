import { FiDownload, FiImage, FiMessageSquare, FiDroplet } from "react-icons/fi";
import SectionHeader from "./SectionHeader";

function swatchHexes(palette) {
  const sw = palette?.swatches;
  if (!Array.isArray(sw)) return [];
  return sw.map((s) => s?.hex).filter(Boolean);
}

function slugifyFileBase(name) {
  const s = (name || "logo")
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .replace(/[^a-zA-Z0-9]+/g, "-")
    .replace(/^-|-$/g, "")
    .slice(0, 48);
  return s || "logo";
}

function triggerBlobDownload(blob, filename) {
  const a = document.createElement("a");
  const url = URL.createObjectURL(blob);
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}

/** SVG vectoriel si fourni ; sinon enveloppe SVG avec image raster intégrée (compatible outils de design). */
function buildSvgForLogo(logoPreviewUrl, logoConcept) {
  const rawSvg = (logoConcept?.svg_data || "").replace(/^\uFEFF/, "").trim();
  if (/^<\?xml/i.test(rawSvg) || /^<svg[\s>/]/i.test(rawSvg)) {
    return rawSvg;
  }
  if (!logoPreviewUrl) return "";
  const esc = logoPreviewUrl
    .replace(/&/g, "&amp;")
    .replace(/"/g, "&quot;")
    .replace(/</g, "&lt;");
  return `<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="1024" height="1024" viewBox="0 0 1024 1024">
  <image xlink:href="${esc}" href="${esc}" width="1024" height="1024" preserveAspectRatio="xMidYMid meet"/>
</svg>`;
}

/**
 * Aperçu final du kit de marque — design system brand tokens.
 */
export default function FinalBrandPreview({
  brandName,
  sloganText,
  paletteOptions,
  selectedPaletteId,
  logoPreviewUrl,
  /** Premier élément de logo_concepts (image_base64, svg_data, …) */
  logoConcept = null,
  /** Court texte issu du naming (description / rationale du nom choisi) */
  nameWhyText = "",
}) {
  let palette = null;
  if (selectedPaletteId && String(selectedPaletteId).startsWith("p-")) {
    const idx = parseInt(String(selectedPaletteId).slice(2), 10);
    if (!Number.isNaN(idx) && paletteOptions[idx]) {
      palette = paletteOptions[idx];
    }
  }
  const hexes       = palette ? swatchHexes(palette) : [];
  const paletteTitle = (palette?.palette_name || "Palette choisie").trim() || "Palette choisie";
  const fileBase = slugifyFileBase(brandName);

  async function handleDownloadPng() {
    if (!logoPreviewUrl) return;
    try {
      const res = await fetch(logoPreviewUrl);
      const blob = await res.blob();
      const ext = blob.type.includes("png") ? "png" : blob.type.includes("jpeg") || blob.type.includes("jpg") ? "jpg" : "png";
      triggerBlobDownload(blob, `${fileBase}-logo.${ext}`);
    } catch {
      const b64 = logoConcept?.image_base64;
      const mime = logoConcept?.image_mime || "image/png";
      if (!b64) return;
      const bin = atob(b64);
      const arr = new Uint8Array(bin.length);
      for (let i = 0; i < bin.length; i++) arr[i] = bin.charCodeAt(i);
      triggerBlobDownload(new Blob([arr], { type: mime }), `${fileBase}-logo.png`);
    }
  }

  function handleDownloadSvg() {
    const svg = buildSvgForLogo(logoPreviewUrl, logoConcept);
    if (!svg) return;
    const blob = new Blob([svg], { type: "image/svg+xml;charset=utf-8" });
    triggerBlobDownload(blob, `${fileBase}-logo.svg`);
  }

  const canDownloadLogo = Boolean(logoPreviewUrl || logoConcept?.image_base64);

  return (
    <div className="bi-fade-up">
      <SectionHeader
        step={6}
        title="Aperçu final"
        sub="Récapitulatif de votre identité de marque — les choix que vous avez validés."
      />

      <div className="mx-auto max-w-lg space-y-4 overflow-hidden rounded-2xl border border-brand-border bg-white shadow-card-md">
        {/* Header gradient band */}
        <div className="bg-gradient-to-br from-brand to-brand-dark px-6 py-5 text-white">
          <p className="text-2xs font-semibold uppercase tracking-widest text-white/60">
            Nom de marque
          </p>
          <p className="mt-1 text-2xl font-bold">{brandName || "—"}</p>
        </div>

        <div className="space-y-4 px-6 pb-6">
          {/* Slogan */}
          <div className="flex items-start gap-3 rounded-xl border border-brand-border bg-brand-light p-4">
            <FiMessageSquare size={16} className="mt-0.5 shrink-0 text-brand" />
            <div>
              <p className="text-2xs font-semibold uppercase tracking-widest text-brand-muted">
                Slogan
              </p>
              <p className="mt-1 text-sm italic leading-relaxed text-ink">
                {sloganText ? `« ${sloganText} »` : "—"}
              </p>
            </div>
          </div>

          {/* Palette */}
          <div>
            <div className="mb-2 flex items-center gap-2">
              <FiDroplet size={13} className="text-ink-muted" />
              <p className="text-2xs font-semibold uppercase tracking-widest text-ink-subtle">
                Palette — {paletteTitle}
              </p>
            </div>
            {hexes.length > 0 ? (
              <div className="overflow-hidden rounded-xl border border-brand-border">
                <div className="flex h-14">
                  {hexes.map((c, i) => (
                    <div
                      key={i}
                      className="min-w-0 flex-1"
                      style={{ backgroundColor: c }}
                      title={c}
                    />
                  ))}
                </div>
                <div className="flex bg-white px-2 py-2">
                  {hexes.map((c, i) => (
                    <div key={i} className="flex-1 text-center">
                      <span className="text-2xs font-mono text-ink-subtle">{c}</span>
                    </div>
                  ))}
                </div>
              </div>
            ) : (
              <p className="text-sm text-ink-muted">—</p>
            )}
          </div>

          {/* Logo */}
          <div>
            <div className="mb-2 flex items-center gap-2">
              <FiImage size={13} className="text-ink-muted" />
              <p className="text-2xs font-semibold uppercase tracking-widest text-ink-subtle">Logo</p>
            </div>
            {logoPreviewUrl ? (
              <>
                <img
                  src={logoPreviewUrl}
                  alt="Logo"
                  className="mx-auto max-h-48 w-auto rounded-xl border border-brand-border object-contain"
                />
                {canDownloadLogo && (
                  <div className="mt-3 flex flex-wrap items-center justify-center gap-2">
                    <button
                      type="button"
                      onClick={() => void handleDownloadPng()}
                      className="inline-flex items-center gap-1.5 rounded-lg border border-brand-border bg-white px-3 py-1.5 text-xs font-medium text-ink shadow-sm transition hover:bg-brand-light"
                    >
                      <FiDownload size={14} aria-hidden />
                      Télécharger PNG
                    </button>
                    <button
                      type="button"
                      onClick={handleDownloadSvg}
                      className="inline-flex items-center gap-1.5 rounded-lg border border-brand-border bg-white px-3 py-1.5 text-xs font-medium text-ink shadow-sm transition hover:bg-brand-light"
                    >
                      <FiDownload size={14} aria-hidden />
                      Télécharger SVG
                    </button>
                  </div>
                )}
              </>
            ) : (
              <div className="flex h-24 items-center justify-center rounded-xl border border-dashed border-brand-border bg-brand-light">
                <p className="text-xs text-brand-muted">Aucun logo généré pour l&apos;instant</p>
              </div>
            )}
            {(nameWhyText || "").trim() ? (
              <div className="mt-3 rounded-xl border border-brand-border/80 bg-brand-light/60 px-3 py-2.5">
                <p className="text-2xs font-semibold uppercase tracking-wide text-ink-subtle">
                  Pourquoi ce nom ?
                </p>
                <p className="mt-1.5 text-xs leading-relaxed text-ink-muted">{nameWhyText.trim()}</p>
              </div>
            ) : null}
          </div>
        </div>
      </div>

      <p className="mt-6 text-center text-xs text-ink-subtle">
        Vous pouvez revenir aux étapes précédentes ou recommencer le parcours.
      </p>
    </div>
  );
}
