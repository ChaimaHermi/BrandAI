import { useEffect, useMemo, useState } from "react";
import { useOutletContext } from "react-router-dom";
import { getLatestBrandIdentity } from "../api/brandIdentity.api";

function GeoLine({ idea }) {
  const country = idea?.clarity_country;
  const code = idea?.clarity_country_code;
  const lang = idea?.clarity_language;
  if (!country && !code && !lang) return null;
  return (
    <p className="text-[12px] text-[#6b7280]">
      Marché cible ·{" "}
      {[country, code ? `(${code})` : null, lang ? `· langue ${lang}` : null]
        .filter(Boolean)
        .join(" ")}
    </p>
  );
}

export default function BrandPage() {
  const { idea, token, refetchIdea } = useOutletContext();
  const [record, setRecord] = useState(null);
  const [loadError, setLoadError] = useState("");

  useEffect(() => {
    refetchIdea?.();
  }, [idea?.id, refetchIdea]);

  useEffect(() => {
    if (!idea?.id || !token) {
      setRecord(null);
      return;
    }
    let cancelled = false;
    setLoadError("");
    getLatestBrandIdentity(idea.id, token)
      .then((data) => {
        if (!cancelled) setRecord(data);
      })
      .catch((e) => {
        if (!cancelled) setLoadError(e?.message || "Chargement impossible");
      });
    return () => {
      cancelled = true;
    };
  }, [idea?.id, token]);

  const brand = useMemo(() => record?.result_json || null, [record]);

  const names = Array.isArray(brand?.name_options) ? brand.name_options : [];
  const status = brand?.branding_status;
  const errors = brand?.agent_errors || {};

  return (
    <div
      className="flex flex-col gap-4"
      style={{
        flex: 1,
        minHeight: 0,
        overflowY: "auto",
        padding: "16px 20px",
      }}
    >
      <div className="rounded-xl border border-[#e8e4ff] bg-white px-5 py-4 shadow-[0_2px_8px_rgba(124,58,237,0.06)]">
        <h1 className="text-[15px] font-extrabold text-[#1a1040]">
          Brand Identity
        </h1>
        <p className="mt-1 text-[12px] text-[#7a76a3]">
          Propositions persistées en base après le pipeline (table{" "}
          <code className="text-[11px]">brand_identity</code>).
        </p>
        <div className="mt-2">
          <GeoLine idea={idea} />
        </div>
        {record?.status && (
          <p className="mt-2 text-[11px] font-semibold uppercase tracking-wide text-[#534AB7]">
            Enregistrement · {record.status}
            {status ? ` · branding ${status}` : ""}
          </p>
        )}
        {loadError && (
          <p className="mt-2 text-[12px] text-red-600">{loadError}</p>
        )}
      </div>

      {Object.keys(errors).length > 0 && (
        <div className="rounded-xl border border-red-100 bg-red-50/80 px-4 py-3 text-[13px] text-red-800">
          <div className="font-bold">Erreurs agent</div>
          <ul className="mt-2 list-inside list-disc">
            {Object.entries(errors).map(([k, v]) => (
              <li key={k}>
                <span className="font-semibold">{k}</span>: {String(v)}
              </li>
            ))}
          </ul>
        </div>
      )}

      {names.length === 0 ? (
        <div className="rounded-xl border border-[#e8e4ff] bg-white p-6 text-center text-[13px] text-[#7a76a3]">
          Aucune identité en base pour cette idée. Lance « Lancer le pipeline »
          depuis le clarifier : marché → branding → le résultat est stocké via
          POST <code className="text-[11px]">/api/brand-identity/&lt;id&gt;</code>
          .
        </div>
      ) : (
        <div className="grid gap-3 sm:grid-cols-2">
          {names.map((opt, i) => (
            <div
              key={i}
              className="rounded-xl border border-[#e8e4ff] bg-white p-4 shadow-[0_1px_4px_rgba(124,58,237,0.05)]"
            >
              <div className="text-[16px] font-bold text-[#1a1040]">
                {opt?.name ?? "—"}
              </div>
              {opt?.availability != null && (
                <div className="mt-1 text-[11px] font-medium text-[#534AB7]">
                  Brandfetch · {String(opt.availability)}
                </div>
              )}
              {opt?.rationale && (
                <p className="mt-2 text-[12px] leading-relaxed text-[#4b5563]">
                  {opt.rationale}
                </p>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
