import { useState, useEffect } from "react";

export default function XaiBlock({ steps, isLoading, collapsed }) {
  const [isOpen, setIsOpen] = useState(!collapsed);

  // Si le parent change collapsed (ex: quand clarified), on synchronise l'état local
  useEffect(() => {
    setIsOpen(!collapsed);
  }, [collapsed]);

  const shouldRender = steps.length > 0 || isLoading;
  if (!shouldRender) return null;

  const effectiveCollapsed = !isOpen;

  const successCount = steps.filter((s) => s.status === "success").length;
  const hasError = steps.some((s) => s.status === "error");

  const dimStep = steps.find((s) => s.detail?.dimensions);
  const dims = dimStep?.detail?.dimensions || null;

  const secStep = steps.find((s) => s.detail?.sector);
  const sector = secStep?.detail?.sector || null;

  const scoreStep = steps.find((s) => s.detail?.score && s.detail.score > 0);
  const finalScore = scoreStep?.detail?.score || null;

  const modelStep = steps.find((s) => s.detail?.model);
  const model = modelStep?.detail?.model || null;
  const dotClass = hasError
    ? "bg-rose-600"
    : isLoading
      ? "bg-[#EF9F27] animate-[pulse_1.2s_infinite]"
      : "bg-[#1D9E75]";

  return (
    <div className="overflow-visible rounded-[14px] border border-[#9FE1CB] bg-white shadow-[0_2px_8px_rgba(29,158,117,0.08)] animate-[slideUp_0.35s_ease_forwards]">
      {/* Header */}
      <div className={`flex items-center justify-between bg-green-50 px-4 py-[10px] ${collapsed ? "border-b-0" : "border-b border-[#9FE1CB]"}`}>
        <div className="flex items-center gap-2">
          <div className={`h-[7px] w-[7px] rounded-full ${dotClass}`} />
          <span className={`text-[11px] font-bold uppercase tracking-[0.07em] ${hasError ? "text-rose-600" : "text-[#085041]"}`}>
            {isLoading
              ? "Agent thinking — XAI"
              : collapsed
              ? "Analyse XAI — terminée"
              : "Analyse XAI — terminée"}
          </span>
        </div>
        <div className="flex items-center gap-1.5">
          {!isLoading && (
            <span className="font-[var(--font-mono)] text-[11px] font-semibold text-[#1D9E75]">
              {successCount} étapes ✓
            </span>
          )}
          {/* Triangle pour plier/déplier le contenu XAI */}
          <button
            type="button"
            onClick={() => setIsOpen((v) => !v)}
            className="flex h-5 w-5 cursor-pointer items-center justify-center rounded-full border border-[#9FE1CB] bg-white p-0"
          >
            <span className={`inline-block text-[10px] text-[#1D9E75] transition-transform duration-150 ease-in-out ${isOpen ? "rotate-90" : "rotate-0"}`}>
              ▶
            </span>
          </button>
        </div>
      </div>

      {/* Steps — cachés si collapsed, scrollable si beaucoup d'éléments */}
      {!effectiveCollapsed && (
        <div className={`h-[220px] overflow-y-auto ${dims ? "border-t-0" : "border-t border-[#f0fdf4]"}`}>
          <div className={`flex flex-col gap-1 px-4 py-[10px] font-[var(--font-mono)] text-[11px] ${dims ? "border-b border-[#f0fdf4]" : "border-b-0"}`}>
            {steps.map((step) => (
              <div key={step.id} className="flex flex-col gap-0.5">
                <div
                  className={`flex gap-2 ${
                    step.status === "success"
                      ? "text-[#1D9E75]"
                      : step.status === "error"
                      ? "text-rose-600"
                      : step.status === "loading"
                      ? "text-gray-400"
                      : "text-[#534AB7]"
                  }`}
                >
                  <span className="w-[14px] shrink-0">
                    {step.status === "loading" && "●●●"}
                    {step.status === "success" && "✓"}
                    {step.status === "error" && "✗"}
                    {step.status === "info" && "→"}
                  </span>
                  <span>
                    {step.text}
                    {step.detail?.sector && ` · secteur ${step.detail.sector}`}
                    {step.detail?.confidence &&
                      ` · confiance ${step.detail.confidence}%`}
                    {step.detail?.model && ` · ${step.detail.model}`}
                    {step.detail?.elapsed_ms &&
                      ` · ${step.detail.elapsed_ms}ms`}
                  </span>
                </div>

                {step.detail?.dimensions && (
                  <div className="mt-0.5 flex gap-3 pl-[22px] text-[10px]">
                    {[
                      { k: "problem", l: "problème" },
                      { k: "target", l: "cible" },
                      { k: "solution", l: "solution" },
                    ].map(({ k, l }) => (
                      <span
                        key={k}
                        className={`font-semibold ${step.detail.dimensions[k] ? "text-[#1D9E75]" : "text-rose-600"}`}
                      >
                        {step.detail.dimensions[k] ? "✓" : "✗"} {l}
                      </span>
                    ))}
                  </div>
                )}

                {step.detail?.score > 0 && (
                  <div className={`pl-[22px] text-[10px] font-semibold ${step.detail.score >= 80 ? "text-[#1D9E75]" : "text-[#EF9F27]"}`}>
                    score : {step.detail.score}/100
                  </div>
                )}
              </div>
            ))}
          </div>

          {dims && (
            <div className="flex gap-2 bg-[#fafffe] px-4 py-[10px]">
              {[
                { k: "problem", l: "Problème" },
                { k: "target", l: "Cible" },
                { k: "solution", l: "Solution" },
              ].map(({ k, l }) => (
                <div
                  key={k}
                  className={`flex-1 rounded-lg px-[10px] py-2 text-center ${dims[k] ? "border border-[#9FE1CB] bg-[#f0fdf4]" : "border border-[#fecaca] bg-[#fff5f5]"}`}
                >
                  <div className={`mb-[3px] text-[9px] font-bold uppercase tracking-[0.07em] ${dims[k] ? "text-[#1D9E75]" : "text-rose-600"}`}>
                    {l}
                  </div>
                  <div className={`text-[11px] font-semibold ${dims[k] ? "text-[#085041]" : "text-rose-600"}`}>
                    {dims[k] ? "✓ Détecté" : "✗ Manquant"}
                  </div>
                </div>
              ))}

              {sector && (
                <div className="flex-1 rounded-lg border border-[#AFA9EC] bg-[#f0eeff] px-[10px] py-2 text-center">
                  <div className="mb-[3px] text-[9px] font-bold uppercase tracking-[0.07em] text-[#7F77DD]">
                    Secteur
                  </div>
                  <div className="text-[11px] font-bold text-[#3C3489]">
                    {sector}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
