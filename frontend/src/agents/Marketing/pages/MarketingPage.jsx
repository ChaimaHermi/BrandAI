import { useEffect, useMemo, useState } from "react";
import { useOutletContext } from "react-router-dom";
import { useMarketingAgent } from "../hooks/useMarketingAgent";

const SECTION_TABS = [
  { id: "positioning", label: "Positionnement" },
  { id: "targets", label: "Cibles" },
  { id: "channels", label: "Canaux" },
  { id: "pricing", label: "Pricing" },
  { id: "gtm", label: "Go-to-Market" },
  { id: "action", label: "Plan d'action" },
];

function Card({ children, className = "" }) {
  return <div className={`rounded-xl border border-slate-200 bg-white p-5 ${className}`}>{children}</div>;
}

function EmptyState() {
  return (
    <Card>
      <p className="text-sm text-slate-600">
        Aucun plan marketing disponible. Lance le pipeline après l&apos;analyse de marché.
      </p>
    </Card>
  );
}

function SafeList({ items }) {
  if (!Array.isArray(items) || items.length === 0) {
    return <p className="text-sm text-slate-500">-</p>;
  }
  return (
    <ul className="space-y-1">
      {items.map((item, idx) => (
        <li key={`${item}-${idx}`} className="text-sm text-slate-700">
          • {item}
        </li>
      ))}
    </ul>
  );
}

export default function MarketingPage() {
  const { idea, token } = useOutletContext();
  const { plan, hasData, isLoading, error, loadLatest } = useMarketingAgent({ idea, token });
  const [activeSection, setActiveSection] = useState("positioning");

  useEffect(() => {
    if (!idea?.id || !token) return;
    loadLatest().catch(() => {});
  }, [idea?.id, token, loadLatest]);

  const activeIndex = useMemo(
    () => Math.max(0, SECTION_TABS.findIndex((s) => s.id === activeSection)),
    [activeSection],
  );

  if (isLoading && !hasData) {
    return (
      <div className="app-content-scroll flex flex-1 flex-col gap-4 bg-[#F8F9FC]">
        <Card>
          <p className="text-sm text-slate-600">Chargement du plan marketing...</p>
        </Card>
      </div>
    );
  }

  if (!hasData) {
    return (
      <div className="app-content-scroll flex flex-1 flex-col gap-4 bg-[#F8F9FC]">
        {error ? (
          <Card className="border-rose-200 bg-rose-50">
            <p className="text-sm text-rose-700">{error}</p>
          </Card>
        ) : null}
        <EmptyState />
      </div>
    );
  }

  return (
    <div className="app-content-scroll flex flex-1 flex-col gap-4 bg-[#F8F9FC]">
      {error ? (
        <Card className="border-amber-200 bg-amber-50">
          <p className="text-sm text-amber-700">{error}</p>
        </Card>
      ) : null}

      <Card>
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <p className="text-xs uppercase tracking-[0.08em] text-slate-400">
              Plan marketing · étape 3/7
            </p>
            <p className="text-base font-medium text-slate-900">{idea?.name || "Projet"}</p>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <span className="rounded-full bg-blue-50 px-2.5 py-1 text-xs text-blue-700">
              {idea?.clarity_sector || idea?.sector || "-"}
            </span>
            <span className="rounded-full bg-stone-100 px-2.5 py-1 text-xs text-stone-700">
              {idea?.clarity_country_code || "TN"}
            </span>
            <span className="rounded-full bg-amber-100 px-2.5 py-1 text-xs text-amber-700">
              Confiance {plan?.confidenceLevel || "-"}
            </span>
          </div>
        </div>

        <div className="mt-4 flex flex-wrap gap-2 border-t border-slate-200 pt-3">
          {SECTION_TABS.map((tab) => (
            <button
              key={tab.id}
              type="button"
              onClick={() => setActiveSection(tab.id)}
              className={`rounded-lg border px-4 py-2 text-sm ${
                activeSection === tab.id
                  ? "border-slate-400 bg-slate-200 text-slate-900"
                  : "border-slate-300 bg-slate-100 text-slate-700"
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>
      </Card>

      {activeSection === "positioning" ? (
        <div className="grid gap-3 md:grid-cols-2">
          <Card>
            <p className="mb-2 text-xs uppercase tracking-[0.08em] text-slate-400">Segment cible</p>
            <p className="text-sm text-slate-800">{plan?.positioning?.target_segment || "-"}</p>
          </Card>
          <Card>
            <p className="mb-2 text-xs uppercase tracking-[0.08em] text-slate-400">Différenciation</p>
            <p className="text-sm text-slate-800">{plan?.positioning?.differentiation || "-"}</p>
          </Card>
          <Card className="md:col-span-2">
            <p className="mb-2 text-xs uppercase tracking-[0.08em] text-slate-400">Proposition de valeur</p>
            <p className="text-sm text-slate-800">{plan?.positioning?.value_proposition || "-"}</p>
          </Card>
          <Card className="md:col-span-2">
            <p className="mb-2 text-xs uppercase tracking-[0.08em] text-slate-400">Message principal</p>
            <p className="text-sm text-slate-800">{plan?.messaging?.main_message || "-"}</p>
            <div className="mt-3 grid gap-2 md:grid-cols-2">
              <div className="rounded-lg bg-rose-50 p-3 text-sm text-rose-700">
                {plan?.messaging?.pain_point_focus || "-"}
              </div>
              <div className="rounded-lg bg-emerald-50 p-3 text-sm text-emerald-700">
                {plan?.messaging?.emotional_hook || "-"}
              </div>
            </div>
          </Card>
        </div>
      ) : null}

      {activeSection === "targets" ? (
        <div className="grid gap-3 md:grid-cols-2">
          <Card>
            <p className="mb-2 text-xs uppercase tracking-[0.08em] text-slate-400">Persona principal</p>
            <p className="text-sm text-slate-800">{plan?.targeting?.primary_persona || "-"}</p>
          </Card>
          <Card>
            <p className="mb-2 text-xs uppercase tracking-[0.08em] text-slate-400">Focus segment</p>
            <p className="text-sm text-slate-800">{plan?.targeting?.market_segment_focus || "-"}</p>
          </Card>
          <Card className="md:col-span-2">
            <p className="mb-2 text-xs uppercase tracking-[0.08em] text-slate-400">Personas secondaires</p>
            <SafeList items={plan?.targeting?.secondary_personas} />
          </Card>
        </div>
      ) : null}

      {activeSection === "channels" ? (
        <div className="grid gap-3 md:grid-cols-2">
          <Card>
            <p className="mb-2 text-xs uppercase tracking-[0.08em] text-slate-400">Canaux prioritaires</p>
            <SafeList items={plan?.channels?.primaryChannels} />
          </Card>
          <Card>
            <p className="mb-2 text-xs uppercase tracking-[0.08em] text-slate-400">Canaux secondaires</p>
            <SafeList items={plan?.channels?.secondaryChannels} />
          </Card>
          <Card>
            <p className="mb-2 text-xs uppercase tracking-[0.08em] text-slate-400">Justification</p>
            <p className="text-sm text-slate-800">{plan?.channels?.justification || "-"}</p>
          </Card>
          <Card>
            <p className="mb-2 text-xs uppercase tracking-[0.08em] text-slate-400">Ton</p>
            <p className="text-sm text-slate-800">{plan?.contentDirection?.tone || "-"}</p>
          </Card>
        </div>
      ) : null}

      {activeSection === "pricing" ? (
        <div className="grid gap-3 md:grid-cols-2">
          <Card>
            <p className="mb-2 text-xs uppercase tracking-[0.08em] text-slate-400">Modèle</p>
            <p className="text-sm text-slate-800">{plan?.pricingStrategy?.model || "-"}</p>
          </Card>
          <Card>
            <p className="mb-2 text-xs uppercase tracking-[0.08em] text-slate-400">Logique pricing</p>
            <p className="text-sm text-slate-800">{plan?.pricingStrategy?.pricing_logic || "-"}</p>
          </Card>
          <Card className="md:col-span-2">
            <p className="mb-2 text-xs uppercase tracking-[0.08em] text-slate-400">Justification</p>
            <p className="text-sm text-slate-800">{plan?.pricingStrategy?.justification || "-"}</p>
          </Card>
          <Card className="md:col-span-2">
            <p className="mb-2 text-xs uppercase tracking-[0.08em] text-slate-400">Hypothèses</p>
            <SafeList items={plan?.assumptions} />
          </Card>
        </div>
      ) : null}

      {activeSection === "gtm" ? (
        <div className="grid gap-3 md:grid-cols-2">
          <Card className="md:col-span-2">
            <p className="mb-2 text-xs uppercase tracking-[0.08em] text-slate-400">Premiers utilisateurs</p>
            <p className="text-sm text-slate-800">{plan?.goToMarket?.targetFirstUsers || "-"}</p>
          </Card>
          <Card className="md:col-span-2">
            <p className="mb-2 text-xs uppercase tracking-[0.08em] text-slate-400">Stratégie de lancement</p>
            <p className="text-sm text-slate-800">{plan?.goToMarket?.launchStrategy || "-"}</p>
          </Card>
          <Card>
            <p className="mb-2 text-xs uppercase tracking-[0.08em] text-slate-400">Partenariats</p>
            <SafeList items={plan?.goToMarket?.partnerships} />
          </Card>
          <Card>
            <p className="mb-2 text-xs uppercase tracking-[0.08em] text-slate-400">Tactiques de croissance</p>
            <SafeList items={plan?.goToMarket?.earlyGrowthTactics} />
          </Card>
        </div>
      ) : null}

      {activeSection === "action" ? (
        <div className="grid gap-3 lg:grid-cols-3">
          <Card>
            <p className="mb-2 text-xs uppercase tracking-[0.08em] text-slate-400">Court terme</p>
            <SafeList items={plan?.actionPlan?.shortTerm} />
          </Card>
          <Card>
            <p className="mb-2 text-xs uppercase tracking-[0.08em] text-slate-400">Moyen terme</p>
            <SafeList items={plan?.actionPlan?.midTerm} />
          </Card>
          <Card>
            <p className="mb-2 text-xs uppercase tracking-[0.08em] text-slate-400">Long terme</p>
            <SafeList items={plan?.actionPlan?.longTerm} />
          </Card>
        </div>
      ) : null}

      <Card>
        <div className="flex items-center justify-between">
          <button
            type="button"
            disabled={activeIndex === 0}
            onClick={() => setActiveSection(SECTION_TABS[Math.max(0, activeIndex - 1)].id)}
            className="rounded-lg border border-slate-300 bg-slate-100 px-4 py-2 text-sm text-slate-700 disabled:opacity-40"
          >
            ← Précédent
          </button>

          <div className="flex items-center gap-2">
            {SECTION_TABS.map((tab, idx) => (
              <button
                key={tab.id}
                type="button"
                onClick={() => setActiveSection(tab.id)}
                className={`h-7 w-9 rounded-full border ${
                  idx === activeIndex ? "border-slate-400 bg-slate-300" : "border-slate-300 bg-slate-100"
                }`}
                aria-label={tab.label}
              />
            ))}
          </div>

          <button
            type="button"
            disabled={activeIndex === SECTION_TABS.length - 1}
            onClick={() => setActiveSection(SECTION_TABS[Math.min(SECTION_TABS.length - 1, activeIndex + 1)].id)}
            className="rounded-lg border border-slate-300 bg-slate-100 px-4 py-2 text-sm text-slate-700 disabled:opacity-40"
          >
            Suivant →
          </button>
        </div>
      </Card>
    </div>
  );
}
