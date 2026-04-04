import SectionHeader from "./SectionHeader";

function swatchHexes(palette) {
  const sw = palette?.swatches;
  if (!Array.isArray(sw)) return [];
  return sw.map((s) => s?.hex).filter(Boolean);
}

/**
 * Aperçu final du kit : nom, slogan, palette choisie, logo généré.
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
  const hexes = palette ? swatchHexes(palette) : [];
  const paletteTitle =
    (palette?.palette_name || "Palette choisie").trim() || "Palette choisie";

  return (
    <div className="bi-fade-up">
      <SectionHeader
        step={6}
        title="Aperçu final"
        sub="Récapitulatif de votre identité de marque — les choix que vous avez validés."
      />

      <div className="mx-auto max-w-lg space-y-4 rounded-2xl border border-[#e5e7eb] bg-white p-6 shadow-sm">
        <div>
          <p className="mb-1 text-[10px] font-semibold uppercase tracking-[0.1em] text-[#9ca3af]">
            Nom de marque
          </p>
          <p className="text-xl font-bold text-[#111827]">{brandName || "—"}</p>
        </div>

        <div className="border-t border-[#f3f4f6] pt-4">
          <p className="mb-1 text-[10px] font-semibold uppercase tracking-[0.1em] text-[#9ca3af]">
            Slogan
          </p>
          <p className="text-[15px] italic leading-relaxed text-[#374151]">
            {sloganText ? `« ${sloganText} »` : "—"}
          </p>
        </div>

        <div className="border-t border-[#f3f4f6] pt-4">
          <p className="mb-2 text-[10px] font-semibold uppercase tracking-[0.1em] text-[#9ca3af]">
            Palette
          </p>
          {hexes.length > 0 ? (
            <div>
              <p className="mb-2 text-sm font-medium text-[#111827]">{paletteTitle}</p>
              <div className="flex h-14 overflow-hidden rounded-lg border border-[#e5e7eb]">
                {hexes.map((c, i) => (
                  <div
                    key={i}
                    className="min-w-0 flex-1"
                    style={{ backgroundColor: c }}
                    title={c}
                  />
                ))}
              </div>
            </div>
          ) : (
            <p className="text-sm text-[#6b7280]">—</p>
          )}
        </div>

        <div className="border-t border-[#f3f4f6] pt-4">
          <p className="mb-2 text-[10px] font-semibold uppercase tracking-[0.1em] text-[#9ca3af]">
            Logo
          </p>
          {logoPreviewUrl ? (
            <img
              src={logoPreviewUrl}
              alt="Logo"
              className="mx-auto max-h-48 w-auto rounded-lg border border-[#e5e7eb] object-contain"
            />
          ) : (
            <p className="text-sm text-[#6b7280]">Aucun logo généré pour l’instant.</p>
          )}
        </div>
      </div>

      <p className="mt-6 text-center text-[12px] text-[#9ca3af]">
        Vous pouvez revenir aux étapes précédentes ou recommencer le parcours.
      </p>
    </div>
  );
}
