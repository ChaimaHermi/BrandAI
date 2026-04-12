import { useState, useEffect } from "react";

export default function XaiBlock({ steps, isLoading, collapsed }) {
  const [isOpen, setIsOpen] = useState(!collapsed);

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

  const dotClass = hasError
    ? "bg-rose-600"
    : isLoading
      ? "bg-[#EF9F27] animate-[pulse_1.2s_infinite]"
      : "bg-[#1D9E75]";

  return (
    <div className="overflow-hidden rounded-[14px] border border-[#9FE1CB] bg-white shadow-[0_2px_8px_rgba(29,158,117,0.08)] animate-[slideUp_0.35s_ease_forwards]">
      {/* Header */}
      <div
        className={`flex items-center justify-between bg-green-50 px-4 py-[10px] ${
          !effectiveCollapsed ? "border-b border-[#9FE1CB]" : ""
        }`}
      >
        <div className="flex items-center gap-2">
          <div className={`h-[7px] w-[7px] rounded-full ${dotClass}`} />
          <span
            className={`text-[11px] font-bold uppercase tracking-[0.07em] ${
              hasError ? "text-rose-600" : "text-[#085041]"
            }`}
          >
            {isLoading ? "Agent thinking — XAI" : "Analyse XAI — terminée"}
          </span>
        </div>
        <div className="flex items-center gap-1.5">
          {!isLoading && (
            <span className="font-[var(--font-mono)] text-[11px] font-semibold text-[#1D9E75]">
              {successCount} étapes ✓
            </span>
          )}
          {isLoading && (
            <span className="flex items-center gap-[3px] font-[var(--font-mono)] text-[11px] text-[#EF9F27]">
              <span className="animate-[bounce_0.8s_0ms_infinite] inline-block">●</span>
              <span className="animate-[bounce_0.8s_150ms_infinite] inline-block">●</span>
              <span className="animate-[bounce_0.8s_300ms_infinite] inline-block">●</span>
            </span>
          )}
          {/* Collapse toggle */}
          <button
            type="button"
            onClick={() => setIsOpen((v) => !v)}
            className="flex h-5 w-5 cursor-pointer items-center justify-center rounded-full border border-[#9FE1CB] bg-white p-0"
            aria-label={isOpen ? "Réduire XAI" : "Développer XAI"}
          >
            <span
              className={`inline-block text-[10px] text-[#1D9E75] transition-transform duration-150 ease-in-out ${
                isOpen ? "rotate-90" : "rotate-0"
              }`}
            >
              ▶
            </span>
          </button>
        </div>
      </div>

      {/* Steps — collapsible, max-height prevents blocking page */}
      {!effectiveCollapsed && (
        <div className={dims ? "border-t-0" : "border-t border-[#f0fdf4]"}>
          <div
            className={`flex flex-col gap-1 overflow-y-auto px-4 py-[10px] font-[var(--font-mono)] text-[11px] ${
              dims ? "border-b border-[#f0fdf4]" : "border-b-0"
            }`}
            style={{ maxHeight: "200px" }}
          >
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
                    {step.status === "loading" && (
                      <span className="inline-flex gap-[2px]">
                        <span className="animate-[pulse_1s_0ms_infinite]">·</span>
                        <span className="animate-[pulse_1s_200ms_infinite]">·</span>
                        <span className="animate-[pulse_1s_400ms_infinite]">·</span>
                      </span>
                    )}
                    {step.status === "success" && "✓"}
                    {step.status === "error" && "✗"}
                    {step.status === "info" && "→"}
                  </span>
                  <span>
                    {step.text}
                    {step.detail?.sector && ` · secteur ${step.detail.sector}`}
                    {step.detail?.confidence &&
                      ` · confiance ${step.detail.confidence}%`}
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
                        className={`font-semibold ${
                          step.detail.dimensions[k]
                            ? "text-[#1D9E75]"
                            : "text-rose-600"
                        }`}
                      >
                        {step.detail.dimensions[k] ? "✓" : "✗"} {l}
                      </span>
                    ))}
                  </div>
                )}

                {step.detail?.score > 0 && (
                  <div
                    className={`pl-[22px] text-[10px] font-semibold ${
                      step.detail.score >= 80
                        ? "text-[#1D9E75]"
                        : "text-[#EF9F27]"
                    }`}
                  >
                    score : {step.detail.score}/100
                  </div>
                )}
              </div>
            ))}

            {/* Skeleton rows while loading */}
            {isLoading && steps.length === 0 && (
              <>
                {[1, 2, 3].map((n) => (
                  <div key={n} className="flex gap-2 text-gray-300">
                    <span className="w-[14px] shrink-0">·</span>
                    <span
                      className="h-3 animate-pulse rounded bg-gray-100"
                      style={{ width: `${40 + n * 20}%` }}
                    />
                  </div>
                ))}
              </>
            )}
          </div>

          {dims && (
            <div className="flex flex-wrap gap-2 bg-[#fafffe] px-4 py-[10px]">
              {[
                { k: "problem", l: "Problème" },
                { k: "target", l: "Cible" },
                { k: "solution", l: "Solution" },
              ].map(({ k, l }) => (
                <div
                  key={k}
                  className={`flex min-w-[80px] flex-1 rounded-lg px-[10px] py-2 text-center ${
                    dims[k]
                      ? "border border-[#9FE1CB] bg-[#f0fdf4]"
                      : "border border-[#fecaca] bg-[#fff5f5]"
                  }`}
                >
                  <div className="w-full">
                    <div
                      className={`mb-[3px] text-[9px] font-bold uppercase tracking-[0.07em] ${
                        dims[k] ? "text-[#1D9E75]" : "text-rose-600"
                      }`}
                    >
                      {l}
                    </div>
                    <div
                      className={`text-[11px] font-semibold ${
                        dims[k] ? "text-[#085041]" : "text-rose-600"
                      }`}
                    >
                      {dims[k] ? "✓ Détecté" : "✗ Manquant"}
                    </div>
                  </div>
                </div>
              ))}

              {sector && (
                <div className="flex min-w-[80px] flex-1 rounded-lg border border-[#AFA9EC] bg-[#f0eeff] px-[10px] py-2 text-center">
                  <div className="w-full">
                    <div className="mb-[3px] text-[9px] font-bold uppercase tracking-[0.07em] text-[#7F77DD]">
                      Secteur
                    </div>
                    <div className="text-[11px] font-bold text-[#3C3489]">
                      {sector}
                    </div>
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
