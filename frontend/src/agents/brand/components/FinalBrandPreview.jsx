import { FiDownload, FiImage, FiMessageSquare, FiDroplet } from "react-icons/fi";
import { useMemo, useState } from "react";
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
  logoPreviewTransparentUrl = null,
  /** Premier élément de logo_concepts (image_base64, svg_data, …) */
  logoConcept = null,
  /** Court texte issu du naming (description / rationale du nom choisi) */
  nameWhyText = "",
}) {
  const [variant, setVariant] = useState("with_bg");
  const canShowTransparent = Boolean(logoPreviewTransparentUrl);
  const activeLogoUrl = useMemo(() => {
    if (variant === "without_bg" && logoPreviewTransparentUrl) {
      return logoPreviewTransparentUrl;
    }
    return logoPreviewUrl;
  }, [variant, logoPreviewTransparentUrl, logoPreviewUrl]);

  let palette = null;
  if (selectedPaletteId && String(selectedPaletteId).startsWith("p-")) {
    const idx = parseInt(String(selectedPaletteId).slice(2), 10);
    if (!Number.isNaN(idx) && paletteOptions[idx]) {
      palette = paletteOptions[idx];
    }
  }
  const hexes       = palette ? swatchHexes(palette) : [];
  const paletteTitle = (palette?.palette_name || "Palette choisie").trim() || "Palette choisie";
  const paletteWhy = (palette?.palette_description || "").trim();
  const fileBase = slugifyFileBase(brandName);

  async function handleDownloadPng(target = "with_bg") {
    const urlToUse =
      target === "without_bg" ? (logoPreviewTransparentUrl || null) : (logoPreviewUrl || null);
    if (!urlToUse) return;
    try {
      const res = await fetch(urlToUse);
      const blob = await res.blob();
      const ext = blob.type.includes("png") ? "png" : blob.type.includes("jpeg") || blob.type.includes("jpg") ? "jpg" : "png";
      const suffix = target === "without_bg" ? "-transparent" : "";
      triggerBlobDownload(blob, `${fileBase}-logo${suffix}.${ext}`);
    } catch {
      const b64 =
        target === "without_bg"
          ? logoConcept?.image_base64_transparent
          : logoConcept?.image_base64;
      const mime =
        target === "without_bg"
          ? logoConcept?.image_mime_transparent || "image/png"
          : logoConcept?.image_mime || "image/png";
      if (!b64) return;
      const bin = atob(b64);
      const arr = new Uint8Array(bin.length);
      for (let i = 0; i < bin.length; i++) arr[i] = bin.charCodeAt(i);
      const suffix = target === "without_bg" ? "-transparent" : "";
      triggerBlobDownload(new Blob([arr], { type: mime }), `${fileBase}-logo${suffix}.png`);
    }
  }

  function handleDownloadSvg() {
    const svg = buildSvgForLogo(logoPreviewUrl, logoConcept);
    if (!svg) return;
    const blob = new Blob([svg], { type: "image/svg+xml;charset=utf-8" });
    triggerBlobDownload(blob, `${fileBase}-logo.svg`);
  }

  const canDownloadLogoWithBg = Boolean(logoPreviewUrl || logoConcept?.image_base64);
  const canDownloadLogoWithoutBg = Boolean(
    logoPreviewTransparentUrl || logoConcept?.image_base64_transparent,
  );

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
            {paletteWhy ? (
              <p className="mb-2 text-[11px] leading-snug text-ink-muted">{paletteWhy}</p>
            ) : null}
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
            {activeLogoUrl ? (
              <>
                <div className="mb-2 flex items-center justify-center gap-2">
                  <button
                    type="button"
                    onClick={() => setVariant("with_bg")}
                    className={`rounded-full px-3 py-1 text-xs font-semibold transition ${
                      variant === "with_bg"
                        ? "bg-brand text-white"
                        : "border border-brand-border bg-white text-ink-muted hover:bg-brand-light"
                    }`}
                  >
                    Avec fond
                  </button>
                  <button
                    type="button"
                    onClick={() => canShowTransparent && setVariant("without_bg")}
                    disabled={!canShowTransparent}
                    className={`rounded-full px-3 py-1 text-xs font-semibold transition ${
                      variant === "without_bg"
                        ? "bg-brand text-white"
                        : "border border-brand-border bg-white text-ink-muted hover:bg-brand-light"
                    } ${!canShowTransparent ? "cursor-not-allowed opacity-50" : ""}`}
                  >
                    Sans fond
                  </button>
                </div>
                <img
                  src={activeLogoUrl}
                  alt="Logo"
                  className="mx-auto max-h-48 w-auto rounded-xl border border-brand-border object-contain"
                />
                {logoConcept?.image_attribution ? (
                  <p className="mt-2 text-center text-[11px] leading-snug text-ink-subtle">
                    {logoConcept.image_attribution}
                  </p>
                ) : null}
                {(canDownloadLogoWithBg || canDownloadLogoWithoutBg) && (
                  <div className="mt-3 flex flex-wrap items-center justify-center gap-2">
                    {canDownloadLogoWithBg && (
                      <button
                        type="button"
                        onClick={() => void handleDownloadPng("with_bg")}
                        className="inline-flex items-center gap-1.5 rounded-lg border border-brand-border bg-white px-3 py-1.5 text-xs font-medium text-ink shadow-sm transition hover:bg-brand-light"
                      >
                        <FiDownload size={14} aria-hidden />
                        PNG avec fond
                      </button>
                    )}
                    {canDownloadLogoWithoutBg && (
                      <button
                        type="button"
                        onClick={() => void handleDownloadPng("without_bg")}
                        className="inline-flex items-center gap-1.5 rounded-lg border border-brand-border bg-white px-3 py-1.5 text-xs font-medium text-ink shadow-sm transition hover:bg-brand-light"
                      >
                        <FiDownload size={14} aria-hidden />
                        PNG sans fond
                      </button>
                    )}
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
