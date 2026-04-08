import { FiMessageSquare, FiDroplet, FiImage } from "react-icons/fi";
import SectionHeader from "./SectionHeader";

function swatchHexes(palette) {
  const sw = palette?.swatches;
  if (!Array.isArray(sw)) return [];
  return sw.map((s) => s?.hex).filter(Boolean);
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
              <img
                src={logoPreviewUrl}
                alt="Logo"
                className="mx-auto max-h-48 w-auto rounded-xl border border-brand-border object-contain"
              />
            ) : (
              <div className="flex h-24 items-center justify-center rounded-xl border border-dashed border-brand-border bg-brand-light">
                <p className="text-xs text-brand-muted">Aucun logo généré pour l&apos;instant</p>
              </div>
            )}
          </div>
        </div>
      </div>

      <p className="mt-6 text-center text-xs text-ink-subtle">
        Vous pouvez revenir aux étapes précédentes ou recommencer le parcours.
      </p>
    </div>
  );
}
