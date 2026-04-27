import {
  CLARITY_SCORE_MIN_DISPLAY,
  CLARITY_SCORE_MIN_PIPELINE,
} from "../constants";

function truncate(str, max = 60) {
  const s = (str || "").trim();
  return s.length > max ? s.slice(0, max) + "…" : s;
}

export default function ClarifiedBlock({ data, score }) {
  if (!data) return null;

  const messageText = (data.message || "").trim();
  const hasCountry = !!data.country && data.country !== "Non précisé";
  const hasBudget =
    data.budget_min !== undefined ||
    data.budget_max !== undefined ||
    !!data.budget_currency;

  // ── Score insuffisant → bloc warning ────────────────
  if (score < CLARITY_SCORE_MIN_DISPLAY) {
    return (
      <div className="overflow-hidden rounded-[14px] border border-[#FAC775] bg-white shadow-[0_4px_16px_rgba(239,159,39,0.1)] animate-[slideUp_0.35s_ease_forwards]">
        <div className="flex flex-wrap items-center justify-between gap-2 border-b border-[#FAC775] bg-[#FAEEDA] px-[18px] py-3">
          <div className="flex items-center gap-2">
            <div className="h-[7px] w-[7px] shrink-0 rounded-full bg-[#EF9F27]" />
            <span className="text-[11px] font-bold uppercase tracking-[0.07em] text-[#854F0B]">
              Idée insuffisamment claire
            </span>
          </div>
          <div className="flex items-center gap-2">
            <div className="h-[6px] w-20 overflow-hidden rounded-full bg-[#FAC775]">
              <div
                style={{ width: `${score}%`, transition: "width 1s ease" }}
                className="h-full rounded-full bg-[#EF9F27]"
              />
            </div>
            <span className="text-sm font-extrabold text-[#854F0B]">{score}</span>
            <span className="text-[11px] text-[#EF9F27]">/100</span>
          </div>
        </div>

        <div className="flex flex-col gap-3 px-[18px] py-4">
          <div className="flex items-start gap-3">
            <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full border border-[#FAC775] bg-[#FAEEDA]">
              <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                <circle cx="8" cy="8" r="6" stroke="#EF9F27" strokeWidth="1.3" />
                <path d="M8 5v3.5M8 10.5v.5" stroke="#EF9F27" strokeWidth="1.4" strokeLinecap="round" />
              </svg>
            </div>
            <div className="min-w-0 flex-1">
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

          {hasCountry && (
            <div className="flex items-center gap-3 rounded-xl border border-[#bfdbfe] bg-[#eff6ff] px-4 py-3">
              <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full border border-[#93c5fd] bg-white text-base shadow-[0_1px_4px_rgba(59,130,246,0.15)]">
                🌍
              </div>
              <div className="min-w-0 flex-1">
                <div className="mb-0.5 text-[9px] font-bold uppercase tracking-[0.08em] text-[#1d4ed8]">
                  Zone géographique
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-sm font-bold text-[#1e3a8a]">{data.country}</span>
                  {data.country_code && (
                    <span className="rounded-md border border-[#93c5fd] bg-white px-1.5 py-0.5 font-[var(--font-mono)] text-[10px] font-bold text-[#2563eb]">
                      {data.country_code}
                    </span>
                  )}
                </div>
              </div>
            </div>
          )}

          {/* Dimensions — responsive 1→3 cols */}
          <div className="grid grid-cols-1 gap-2 sm:grid-cols-3">
            {[
              { label: "Problème", ok: !!data.problem, value: data.problem },
              { label: "Cible", ok: !!data.target_users, value: data.target_users },
              { label: "Solution", ok: !!data.solution_description, value: data.solution_description },
            ].map(({ label, ok, value }) => (
              <div
                key={label}
                className={`rounded-[10px] p-[10px] ${
                  ok
                    ? "border border-[#9FE1CB] bg-[#f0fdf4]"
                    : "border border-[#fecaca] bg-[#fff5f5]"
                }`}
              >
                <div
                  className={`mb-1 text-[9px] font-bold uppercase tracking-[0.07em] ${
                    ok ? "text-[#1D9E75]" : "text-rose-600"
                  }`}
                >
                  {ok ? "✓" : "✗"} {label}
                </div>
                <div
                  className={`text-[11px] ${
                    ok ? "font-normal text-gray-700" : "font-semibold text-rose-600"
                  }`}
                >
                  {ok ? truncate(value, 50) : "Non renseigné"}
                </div>
              </div>
            ))}
          </div>

          {hasBudget && (
            <div className="rounded-[10px] border border-[#bbf7d0] bg-[#f0fdf4] px-[14px] py-[10px] text-xs text-[#166534]">
              <div className="mb-1 text-[9px] font-bold uppercase tracking-[0.07em]">
                Budget de départ
              </div>
              <div>
                Min: <strong>{data.budget_min ?? "—"}</strong> · Max: <strong>{data.budget_max ?? "—"}</strong> · Devise: <strong>{data.budget_currency || "—"}</strong>
              </div>
            </div>
          )}

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
      <div className="flex flex-wrap items-center justify-between gap-2 border-b border-[#AFA9EC] bg-gradient-to-br from-[#f0eeff] to-[#fafafe] px-[18px] py-3">
        <div className="flex items-center gap-2">
          <div className="h-[7px] w-[7px] shrink-0 rounded-full bg-[#7F77DD]" />
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
          <div
            className="rounded-full border px-[10px] py-[3px] text-[10px] font-bold"
            style={{
              background: scoreLabel.bg,
              borderColor: scoreLabel.border,
              color: scoreLabel.color,
            }}
          >
            {scoreLabel.text} ✓
          </div>
        </div>
      </div>

      <div className="flex flex-col gap-3 px-[18px] py-4">
        {data.short_pitch && (
          <div className="border-l-[3px] border-l-[#7F77DD] bg-[#f8f7ff] px-4 py-3 text-sm font-semibold italic leading-[1.5] text-[#534AB7]">
            &ldquo;{data.short_pitch}&rdquo;
          </div>
        )}

        {messageText && (
          <div className="rounded-xl border border-[#e8e4ff] bg-[#f8f7ff] px-[14px] py-[10px] text-xs font-semibold leading-[1.6] text-gray-700">
            {messageText}
          </div>
        )}

        {/* Info cards — 1 col on small, 3 on medium+ */}
        <div className="grid grid-cols-1 gap-2 sm:grid-cols-3">
          <div className="rounded-xl border border-[#e8e4ff] bg-[#f8f7ff] p-3">
            <div className="mb-1.5 flex items-center gap-1 text-[9px] font-bold uppercase tracking-[0.08em] text-[#7F77DD]">
              <svg width="10" height="10" viewBox="0 0 10 10" fill="none">
                <path d="M1.5 8.5l7-7M5 1.5h3v3" stroke="#7F77DD" strokeWidth="1.3" strokeLinecap="round" strokeLinejoin="round"/>
              </svg>
              Solution proposée
            </div>
            <div className="text-xs leading-[1.5] text-gray-700">
              {data.solution_description || "—"}
            </div>
          </div>
          <div className="rounded-xl border border-[#9FE1CB] bg-[#f0fdf4] p-3">
            <div className="mb-1.5 flex items-center gap-1 text-[9px] font-bold uppercase tracking-[0.08em] text-[#1D9E75]">
              <svg width="10" height="10" viewBox="0 0 10 10" fill="none">
                <circle cx="5" cy="3.5" r="1.8" stroke="#1D9E75" strokeWidth="1.2"/>
                <path d="M1.5 8.5c0-1.93 1.57-3.5 3.5-3.5s3.5 1.57 3.5 3.5" stroke="#1D9E75" strokeWidth="1.2" strokeLinecap="round"/>
              </svg>
              Cible
            </div>
            <div className="text-xs font-semibold leading-[1.5] text-gray-700">
              {data.target_users || "—"}
            </div>
          </div>
          <div className="rounded-xl border border-[#FAC775] bg-[#FAEEDA] p-3">
            <div className="mb-1.5 flex items-center gap-1 text-[9px] font-bold uppercase tracking-[0.08em] text-[#854F0B]">
              <svg width="10" height="10" viewBox="0 0 10 10" fill="none">
                <rect x="1" y="3" width="8" height="6" rx="1" stroke="#854F0B" strokeWidth="1.2"/>
                <path d="M3.5 3V2a1.5 1.5 0 013 0v1" stroke="#854F0B" strokeWidth="1.2" strokeLinecap="round"/>
              </svg>
              Secteur
            </div>
            <div className="text-xs font-bold text-gray-700">
              {data.sector || "—"}
            </div>
          </div>
        </div>

        {hasBudget && (
          <div className="rounded-xl border border-[#bbf7d0] bg-[#f0fdf4] px-[14px] py-3">
            <div className="mb-1.5 text-[9px] font-bold uppercase tracking-[0.08em] text-[#15803d]">
              Budget de départ
            </div>
            <div className="flex flex-wrap items-center gap-2 text-xs text-gray-700">
              <span>
                Min: <strong>{data.budget_min ?? "—"}</strong>
              </span>
              <span>
                Max: <strong>{data.budget_max ?? "—"}</strong>
              </span>
              <span>
                Devise: <strong>{data.budget_currency || "—"}</strong>
              </span>
            </div>
          </div>
        )}

        {/* Zone géographique */}
        {hasCountry && (
          <div className="flex items-center gap-3 rounded-xl border border-[#bfdbfe] bg-[#eff6ff] px-4 py-3">
            <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full border border-[#93c5fd] bg-white text-lg shadow-[0_1px_4px_rgba(59,130,246,0.15)]">
              🌍
            </div>
            <div className="min-w-0 flex-1">
              <div className="mb-0.5 text-[9px] font-bold uppercase tracking-[0.08em] text-[#1d4ed8]">
                Zone géographique
              </div>
              <div className="flex items-center gap-2">
                <span className="text-sm font-bold text-[#1e3a8a]">
                  {data.country}
                </span>
                {data.country_code && (
                  <span className="rounded-md border border-[#93c5fd] bg-white px-1.5 py-0.5 font-[var(--font-mono)] text-[10px] font-bold text-[#2563eb]">
                    {data.country_code}
                  </span>
                )}
              </div>
            </div>
          </div>
        )}

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
