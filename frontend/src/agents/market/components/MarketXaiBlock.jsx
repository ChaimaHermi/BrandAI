import { XAI_STAGE_LABELS } from "../constants";

export default function MarketXaiBlock({ steps = [], isLoading = false, error = "" }) {
  if (!isLoading && steps.length === 0 && !error) return null;

  return (
    <div className="rounded-xl border border-[#d9d4ff] bg-white p-3 shadow-sm">
      <div className="mb-2 flex items-center justify-between">
        <p className="text-[11px] font-medium uppercase tracking-[0.08em] text-[#534AB7]">
          XAI Progress
        </p>
        <span className="text-[11px] font-normal text-[#7F77DD]">
          {isLoading ? "En cours..." : "Terminé"}
        </span>
      </div>

      <div className="space-y-1.5">
        {steps.map((step) => (
          <div key={step.id} className="flex items-start gap-2 text-[11px]">
            <span
              className={`mt-0.5 inline-block h-2 w-2 rounded-full ${
                step.status === "error"
                  ? "bg-rose-500"
                  : step.status === "success"
                    ? "bg-emerald-500"
                    : "bg-[#7F77DD]"
              }`}
            />
            <span className="font-normal text-[#4b4b66]">
              {XAI_STAGE_LABELS[step.stage] || step.stage || "step"}: {step.message}
            </span>
          </div>
        ))}
      </div>

      {error && (
        <div className="mt-2 rounded-lg border border-rose-200 bg-rose-50 px-2 py-1 text-[11px] font-normal text-rose-700">
          {error}
        </div>
      )}
    </div>
  );
}

