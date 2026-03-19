import {
  CLARITY_SCORE_MIN_DISPLAY,
  CLARITY_SCORE_MIN_PIPELINE,
} from "../constants";

export default function ClarifiedBlock({ data, score }) {
  if (!data) return null;

  const messageText = (data.message || "").trim();

  // ── Score insuffisant → bloc warning ────────────────
  if (score < CLARITY_SCORE_MIN_DISPLAY) {
    return (
      <div className="overflow-hidden rounded-[14px] border border-[#FAC775] bg-white shadow-[0_4px_16px_rgba(239,159,39,0.1)] animate-[slideUp_0.35s_ease_forwards]">
        <div className="flex items-center justify-between border-b border-[#FAC775] bg-[#FAEEDA] px-[18px] py-3">
          <div className="flex items-center gap-2">
            <div className="h-[7px] w-[7px] rounded-full bg-[#EF9F27]" />
            <span className="text-[11px] font-bold uppercase tracking-[0.07em] text-[#854F0B]">
              Idée insuffisamment claire
            </span>
          </div>
          <div className="flex items-center gap-2">
            <div className="h-[6px] w-20 overflow-hidden rounded-full bg-[#FAC775]">
              <div
                style={{
                  height: "100%",
                  width: `${score}%`,
                }}
                className="rounded-full bg-[#EF9F27]"
              />
            </div>
            <span className="text-sm font-extrabold text-[#854F0B]">
              {score}
            </span>
            <span className="text-[11px] text-[#EF9F27]">
              /100
            </span>
          </div>
        </div>

        <div className="flex flex-col gap-3 px-[18px] py-4">
          <div className="flex items-start gap-3">
            <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full border border-[#FAC775] bg-[#FAEEDA]">
              <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                <circle
                  cx="8"
                  cy="8"
                  r="6"
                  stroke="#EF9F27"
                  strokeWidth="1.3"
                />
                <path
                  d="M8 5v3.5M8 10.5v.5"
                  stroke="#EF9F27"
                  strokeWidth="1.4"
                  strokeLinecap="round"
                />
              </svg>
            </div>
            <div>
              <div className="mb-1.5 text-[13px] font-bold text-[#854F0B]">
                Votre idée nécessite plus de précisions
              </div>
              <div className="text-xs leading-[1.6] text-[#633806]">
                Le score de clarté est de {score}/100. Pour lancer le pipeline,
                votre idée doit atteindre un score minimum de{" "}
                {CLARITY_SCORE_MIN_PIPELINE}/100. Revenez en arrière et précisez
                les dimensions manquantes.
              </div>
            </div>
          </div>

            {messageText && (
              <div className="rounded-xl border border-[#e8e4ff] bg-[#f8f7ff] px-[14px] py-[10px] text-xs font-semibold leading-[1.6] text-gray-700">
                {messageText}
              </div>
            )}

          {/* Dimensions manquantes */}
          <div className="grid grid-cols-3 gap-2">
            {[
              { label: "Problème", ok: !!data.problem, value: data.problem },
              {
                label: "Cible",
                ok: !!data.target_users,
                value: data.target_users,
              },
              {
                label: "Solution",
                ok: !!data.solution_description,
                value: data.solution_description,
              },
            ].map(({ label, ok, value }) => (
              <div
                key={label}
                className={`rounded-[10px] p-[10px] ${ok ? "border border-[#9FE1CB] bg-[#f0fdf4]" : "border border-[#fecaca] bg-[#fff5f5]"}`}
              >
                <div className={`mb-1 text-[9px] font-bold uppercase tracking-[0.07em] ${ok ? "text-[#1D9E75]" : "text-rose-600"}`}>
                  {ok ? "✓" : "✗"} {label}
                </div>
                <div className={`text-[11px] ${ok ? "font-normal text-gray-700" : "font-semibold text-rose-600"}`}>
                  {ok ? (value || "").slice(0, 40) + "..." : "Non renseigné"}
                </div>
              </div>
            ))}
          </div>

          <div className="rounded-[10px] border border-[#FAC775] bg-[#fff9f0] px-[14px] py-[10px] text-xs text-[#854F0B]">
            Le lancement du pipeline est désactivé. Score minimum requis :{" "}
            <strong>{CLARITY_SCORE_MIN_PIPELINE}/100</strong>
          </div>
        </div>
      </div>
    );
  }

  // ── Score suffisant → affichage normal ──────────────
  const scoreLabel =
    score >= 90
      ? { text: "Excellent", color: "#085041", bg: "#f0fdf4", border: "#9FE1CB" }
      : score >= CLARITY_SCORE_MIN_PIPELINE
        ? { text: "Très bien", color: "#1D9E75", bg: "#f0fdf4", border: "#9FE1CB" }
        : { text: "Acceptable", color: "#854F0B", bg: "#FAEEDA", border: "#FAC775" };

  return (
    <div className="overflow-hidden rounded-[14px] border border-[#AFA9EC] bg-white shadow-[0_4px_20px_rgba(124,58,237,0.1)] animate-[slideUp_0.35s_ease_forwards]">
      {/* Header avec score */}
      <div className="flex items-center justify-between border-b border-[#AFA9EC] bg-gradient-to-br from-[#f0eeff] to-[#fafafe] px-[18px] py-3">
        <div className="flex items-center gap-2">
          <div className="h-[7px] w-[7px] rounded-full bg-[#7F77DD]" />
          <span className="text-[11px] font-bold uppercase tracking-[0.07em] text-[#3C3489]">
            Idée structurée
          </span>
        </div>
        <div className="flex items-center gap-[10px]">
          <div className="flex items-center gap-1.5">
            <div className="h-[6px] w-[90px] overflow-hidden rounded-full bg-[#e8e4ff]">
              <div
                style={{
                  height: "100%",
                  width: `${score}%`,
                  transition: "width 1s ease",
                }}
                className={`rounded-full ${
                  score >= CLARITY_SCORE_MIN_PIPELINE
                    ? "bg-gradient-to-r from-[#7F77DD] to-[#1D9E75]"
                    : "bg-gradient-to-r from-[#7F77DD] to-[#EF9F27]"
                }`}
              />
            </div>
            <span className="text-base font-extrabold" style={{ color: scoreLabel.color }}>
              {score}
            </span>
            <span className="text-[11px] text-[#AFA9EC]">/100</span>
          </div>
          <div className="rounded-full border px-[10px] py-[3px] text-[10px] font-bold" style={{ background: scoreLabel.bg, borderColor: scoreLabel.border, color: scoreLabel.color }}>
            {scoreLabel.text} ✓
          </div>
        </div>
      </div>

      <div className="flex flex-col gap-3 px-[18px] py-4">
        {data.short_pitch && (
          <div className="border-l-[3px] border-l-[#7F77DD] bg-[#f8f7ff] px-4 py-3 text-sm font-semibold italic leading-[1.5] text-[#534AB7]">
            "{data.short_pitch}"
          </div>
        )}

        {messageText && (
          <div className="rounded-xl border border-[#e8e4ff] bg-[#f8f7ff] px-[14px] py-[10px] text-xs font-semibold leading-[1.6] text-gray-700">
            {messageText}
          </div>
        )}

        <div className="grid grid-cols-3 gap-2">
          <div className="rounded-xl border border-[#e8e4ff] bg-[#f8f7ff] p-3">
            <div className="mb-1.5 text-[9px] font-bold uppercase tracking-[0.08em] text-[#7F77DD]">
              Ce que c&apos;est
            </div>
            <div className="text-xs leading-[1.5] text-gray-700">
              {data.solution_description || "—"}
            </div>
          </div>
          <div className="rounded-xl border border-[#9FE1CB] bg-[#f0fdf4] p-3">
            <div className="mb-1.5 text-[9px] font-bold uppercase tracking-[0.08em] text-[#1D9E75]">
              Pour qui ?
            </div>
            <div className="text-xs font-semibold leading-[1.5] text-gray-700">
              {data.target_users || "—"}
            </div>
          </div>
          <div className="rounded-xl border border-[#FAC775] bg-[#FAEEDA] p-3">
            <div className="mb-1.5 text-[9px] font-bold uppercase tracking-[0.08em] text-[#854F0B]">
              Secteur
            </div>
            <div className="text-xs font-bold text-gray-700">
              {data.sector || "—"}
            </div>
          </div>
        </div>

        <div className="rounded-xl border border-[#fecaca] bg-[#fff5f5] px-[14px] py-3">
          <div className="mb-1.5 text-[9px] font-bold uppercase tracking-[0.08em] text-rose-600">
            Problème résolu
          </div>
          <div className="text-xs leading-[1.6] text-gray-700">
            {data.problem || "—"}
          </div>
        </div>
      </div>
    </div>
  );
}
