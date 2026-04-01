import { useEffect, useMemo, useState } from "react";
import { useOutletContext } from "react-router-dom";
import { useMarketingAgent } from "../hooks/useMarketingAgent";

const SECTION_TABS = [
  { id: "positioning", label: "Positionnement", accent: "#378ADD" },
  { id: "targets", label: "Cibles", accent: "#7C5CFA" },
  { id: "channels", label: "Canaux", accent: "#0F9D9D" },
  { id: "pricing", label: "Pricing", accent: "#16A34A" },
  { id: "gtm", label: "Go-to-Market", accent: "#F59E0B" },
  { id: "action", label: "Plan d'action", accent: "#2563EB" },
];

const SECTION_ACCENTS = {
  positioning: "#378ADD",
  targets: "#7C5CFA",
  channels: "#0F9D9D",
  pricing: "#16A34A",
  gtm: "#F59E0B",
  action: "#2563EB",
};

function PremiumCard({ children, className = "" }) {
  return (
    <div
      className={`rounded-[12px] border-[0.5px] border-slate-200 bg-white p-6 transition-all dark:border-slate-700 dark:bg-slate-900 ${className}`}
      style={{ boxShadow: "0 1px 3px rgba(0,0,0,0.06)" }}
    >
      {children}
    </div>
  );
}

function Tag({ children, className = "" }) {
  return (
    <span className={`inline-flex items-center rounded-full px-2.5 py-1 text-[11px] font-medium ${className}`}>
      {children}
    </span>
  );
}

function SectionHeader({ id, title }) {
  const accent = SECTION_ACCENTS[id] || "#378ADD";
  return (
    <div className="mb-2 flex items-center gap-2">
      <span className="h-2.5 w-2.5 rounded-full" style={{ backgroundColor: accent }} />
      <p className="text-[12px] font-medium uppercase tracking-[0.08em]" style={{ color: accent }}>
        {title}
      </p>
      <div className="h-px flex-1 bg-slate-200 dark:bg-slate-700" />
    </div>
  );
}

function EmptyState() {
  return (
    <PremiumCard>
      <p className="text-[13px] font-normal leading-[1.6] text-slate-600 dark:text-slate-300">
        Aucun plan marketing disponible. Lance le pipeline après l'analyse de marché.
      </p>
    </PremiumCard>
  );
}

function HighlightValueText({ text }) {
  const source = String(text || "-");
  const keyword = "vérifiées, sécurisées et alignées";
  const idx = source.toLowerCase().indexOf(keyword.toLowerCase());

  if (idx < 0) return <>{source}</>;

  const before = source.slice(0, idx);
  const match = source.slice(idx, idx + keyword.length);
  const after = source.slice(idx + keyword.length);

  return (
    <>
      {before}
      <span className="font-medium text-[#378ADD]">{match}</span>
      {after}
    </>
  );
}

function IconBox({ color = "#378ADD", children }) {
  return (
    <div className="flex h-9 w-9 items-center justify-center rounded-[8px]" style={{ backgroundColor: `${color}1A` }}>
      {children}
    </div>
  );
}

export default function MarketingPage() {
  const { idea, token } = useOutletContext();
  const { plan, hasData, isLoading, error, loadLatest } = useMarketingAgent({ idea, token });
  const [activeSection, setActiveSection] = useState("positioning");
  const activeIndex = useMemo(
    () => Math.max(0, SECTION_TABS.findIndex((s) => s.id === activeSection)),
    [activeSection],
  );

  const projectName = idea?.name || "Projet";
  const sector = idea?.clarity_sector || idea?.sector || "-";
  const countryCode = idea?.clarity_country_code || idea?.country_code || "TN";

  useEffect(() => {
    if (!idea?.id || !token) return;
    loadLatest().catch(() => {});
  }, [idea?.id, token, loadLatest]);

  if (isLoading && !hasData) {
    return (
      <div className="app-content-scroll flex flex-1 flex-col gap-4 bg-[#F8F9FC]">
        <PremiumCard>
          <p className="text-[13px] font-normal leading-[1.6] text-slate-600 dark:text-slate-300">Chargement du plan marketing...</p>
        </PremiumCard>
      </div>
    );
  }

  if (!hasData) {
    return (
      <div className="app-content-scroll flex flex-1 flex-col gap-4 bg-[#F8F9FC]">
        {error ? (
          <PremiumCard className="border-rose-200 bg-rose-50 dark:border-rose-900 dark:bg-rose-950/30">
            <p className="text-[13px] font-normal leading-[1.6] text-rose-700 dark:text-rose-300">{error}</p>
          </PremiumCard>
        ) : null}
        <EmptyState />
      </div>
    );
  }

  const primaryPersona = plan.targeting?.primary_persona || "-";
  const secondary = plan.targeting?.secondary_personas || [];
  const painPoints = plan.messaging?.pain_point_focus
    ? String(plan.messaging.pain_point_focus).split(/[;,]/).map((x) => x.trim()).filter(Boolean)
    : [];
  const motivations = plan.messaging?.emotional_hook
    ? String(plan.messaging.emotional_hook).split(/[;,]/).map((x) => x.trim()).filter(Boolean)
    : [];

  return (
    <div className="app-content-scroll flex flex-1 flex-col gap-4 bg-[#F8F9FC] dark:bg-slate-950">
      {error ? (
        <PremiumCard className="border-amber-200 bg-amber-50 dark:border-amber-900 dark:bg-amber-950/30">
          <p className="text-[13px] font-normal leading-[1.6] text-amber-700 dark:text-amber-300">{error}</p>
        </PremiumCard>
      ) : null}

      <PremiumCard>
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <p className="text-[11px] uppercase tracking-[0.08em] text-slate-400 dark:text-slate-500">
              Plan marketing · étape 3/7
            </p>
            <p className="text-[15px] font-medium text-slate-900 dark:text-slate-100">{projectName}</p>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <Tag className="bg-blue-50 text-[#2E6EA6] dark:bg-blue-900/40 dark:text-blue-200">{sector}</Tag>
            <Tag className="bg-stone-100 text-stone-600 dark:bg-stone-800 dark:text-stone-200">{countryCode}</Tag>
            <Tag className="bg-amber-100 text-amber-700 dark:bg-amber-900/60 dark:text-amber-200">
              Confiance {plan.confidenceLevel || "-"}
            </Tag>
          </div>
        </div>

        <div className="app-tabs-row mt-4 border-t border-slate-200 pt-3 dark:border-slate-700">
          {SECTION_TABS.map((tab) => {
            const active = tab.id === activeSection;
            return (
              <button
                key={tab.id}
                type="button"
                onClick={() => setActiveSection(tab.id)}
                className="min-w-max rounded-[10px] border px-5 py-2 text-[13px] font-medium transition"
                style={
                  active
                    ? {
                        borderColor: "#A9B6C5",
                        color: "#111827",
                        backgroundColor: "#EFF4FA",
                      }
                    : {
                        borderColor: "#A9B6C5",
                        color: "#111827",
                        backgroundColor: "#F5F6F8",
                      }
                }
              >
                {tab.label}
              </button>
            );
          })}
        </div>
      </PremiumCard>

      {activeSection === "positioning" ? (
        <div className="space-y-3">
          <SectionHeader id="positioning" title="Positionnement" />

          <PremiumCard className="border-blue-100 p-0" style={{ background: "#DCE8F6" }}>
            <div className="border-l-[3px] border-[#378ADD] pl-4">
              <p className="px-4 py-4 text-[15px] leading-relaxed text-[#003A75] dark:text-blue-100">
                <span className="mb-2 block text-[11px] font-medium uppercase tracking-[0.08em] text-[#225E97]">
                  Proposition de valeur
                </span>
                <HighlightValueText text={plan.positioning?.value_proposition || "-"} />
              </p>
            </div>
          </PremiumCard>

          <div className="app-grid-auto">
            <PremiumCard className="p-0" style={{ borderColor: "#D0D6DE" }}>
              <div className="flex items-center gap-2 rounded-t-[12px] bg-[#DCE8F6] px-4 py-3">
                <IconBox color="#378ADD">
                  <svg width="18" height="18" viewBox="0 0 20 20" fill="none">
                    <circle cx="10" cy="6" r="3" stroke="#378ADD" strokeWidth="1.4" />
                    <path d="M4 16c0-3 2.7-5 6-5s6 2 6 5" stroke="#378ADD" strokeWidth="1.4" strokeLinecap="round" />
                  </svg>
                </IconBox>
                <p className="text-[11px] font-medium uppercase tracking-[0.08em] text-[#0A4E8F]">Segment cible</p>
              </div>
              <div className="p-4 text-[13px] font-normal leading-[1.6] text-[#111827]">{plan.positioning?.target_segment || "-"}</div>
            </PremiumCard>

            <PremiumCard className="p-0" style={{ borderColor: "#D0D6DE" }}>
              <div className="flex items-center gap-2 rounded-t-[12px] bg-[#DCEFEA] px-4 py-3">
                <IconBox color="#13795B">
                  <svg width="18" height="18" viewBox="0 0 20 20" fill="none">
                    <path d="M10 2l2.4 4.9 5.4.8-3.9 3.8.9 5.3-4.8-2.5-4.8 2.5.9-5.3-3.9-3.8 5.4-.8L10 2z" stroke="#13795B" strokeWidth="1.2" fill="none" />
                  </svg>
                </IconBox>
                <p className="text-[11px] font-medium uppercase tracking-[0.08em] text-[#0D6A53]">Différenciateur clé</p>
              </div>
              <div className="p-4 text-[13px] font-normal leading-[1.6] text-[#111827]">{plan.positioning?.differentiation || "-"}</div>
            </PremiumCard>
          </div>

          <PremiumCard className="p-5" style={{ borderColor: "#D0D6DE" }}>
            <p className="mb-2 text-[11px] font-medium uppercase tracking-[0.08em] text-[#0A4E8F]">Message principal</p>
            <p className="border-l-[3px] border-[#378ADD] pl-4 text-[15px] font-medium leading-[1.6] text-[#111827]">
              "{plan.messaging?.main_message || "-"}"
            </p>
            <div className="mt-4 space-y-2">
              <div className="flex items-start gap-2 rounded-[8px] bg-[#F7E1E1] p-3">
                <Tag className="gap-1 bg-[#F2B8B8] text-[#7A1111]">pain point</Tag>
                <p className="text-[13px] font-normal leading-[1.6] text-[#7A1111]">{plan.messaging?.pain_point_focus || "-"}</p>
              </div>
              <div className="flex items-start gap-2 rounded-[8px] bg-[#DDEBCF] p-3">
                <Tag className="gap-1 bg-[#A8D07E] text-[#1F4D1F]">accroche</Tag>
                <p className="text-[13px] font-normal leading-[1.6] text-[#1F4D1F]">{plan.messaging?.emotional_hook || "-"}</p>
              </div>
            </div>
          </PremiumCard>
        </div>
      ) : null}

      {activeSection === "targets" ? (
        <div className="space-y-3">
          <SectionHeader id="targets" title="Cibles" />

          <PremiumCard className="border-[#D5D6E4] p-0">
            <div className="rounded-t-[12px] border-t-[3px] border-[#5B4FCB] px-4 py-3">
              <div className="rounded-[8px] bg-[#E5E6F8] px-4 py-3">
                <div className="flex items-start justify-between gap-3">
                  <div className="flex items-start gap-3">
                    <div className="flex h-[46px] w-[46px] items-center justify-center rounded-full bg-[#5B4FCB] text-[15px] font-medium text-white">
                      {primaryPersona.slice(0, 2).toUpperCase()}
                    </div>
                    <div>
                      <p className="text-[13px] font-medium leading-tight text-[#1F2E74]">{primaryPersona}</p>
                      <p className="text-[12px] font-normal text-[#2C3A96]">22-27 ans · usage intensif mobile · frustration face aux arnaques</p>
                    </div>
                  </div>
                  <Tag className="bg-[#7066D8] text-white">prioritaire</Tag>
                </div>
              </div>
            </div>

            <div className="px-5 pb-5">
              <div className="grid gap-4 md:grid-cols-2">
                <div>
                  <p className="mb-2 text-[11px] font-medium uppercase tracking-[0.08em] text-[#BB3B3B]">Pain points</p>
                  <div className="flex flex-wrap gap-1.5">
                    {(painPoints.length ? painPoints : ["Processus long", "Risque d'arnaques", "Offres non rémunérées"]).map((p, i) => (
                      <span
                        key={`${p}-${i}`}
                        className="rounded-[8px] border border-[#EEB2B2] bg-[#FBE9E9] px-2.5 py-1 text-[11px] font-medium text-[#992E2E]"
                      >
                        {p}
                      </span>
                    ))}
                  </div>
                </div>
                <div>
                  <p className="mb-2 text-[11px] font-medium uppercase tracking-[0.08em] text-[#4B7E1A]">Motivations</p>
                  <div className="flex flex-wrap gap-1.5">
                    {(motivations.length ? motivations : ["Expérience reconnue", "Employabilité int."]).map((m, i) => (
                      <span
                        key={`${m}-${i}`}
                        className="rounded-[8px] border border-[#B8D893] bg-[#EDF8E2] px-2.5 py-1 text-[11px] font-medium text-[#355E10]"
                      >
                        {m}
                      </span>
                    ))}
                  </div>
                </div>
              </div>

              <div className="mt-4 rounded-[8px] bg-[#ECEAE5] px-4 py-3 text-[15px] font-medium italic text-[#111827]">
                "{plan.targeting?.market_segment_focus || "Des stages vérifiés et rémunérés, trouvés en 5 minutes via notre IA de matching."}"
              </div>
            </div>
          </PremiumCard>

          <div className="grid gap-3 md:grid-cols-2">
            {secondary.slice(0, 2).map((persona, idx) => (
              <PremiumCard
                key={`${persona}-${idx}`}
                className="border-[#D5D6E4]"
                style={{ borderTop: `3px solid ${idx === 0 ? "#D38A1D" : "#18A06A"}` }}
              >
                <div className="flex items-start gap-3">
                  <div
                    className="flex h-10 w-10 items-center justify-center rounded-full text-[13px] font-medium"
                    style={{
                      backgroundColor: idx === 0 ? "#F3E8D8" : "#DDF2EA",
                      color: idx === 0 ? "#8A5B16" : "#116A49",
                    }}
                  >
                    {persona.slice(0, 2).toUpperCase()}
                  </div>
                  <div>
                    <p className="text-[13px] font-medium text-[#111827]">
                      {idx === 0 ? "Jeune professionnel" : "Entreprise tunisienne"}
                    </p>
                    <p className="text-[12px] font-normal text-[#374151]">
                      {idx === 0 ? "Reconversion via stage" : "PME, start-ups, grands groupes"}
                    </p>
                  </div>
                </div>
                <p className="mt-3 text-[15px] font-medium italic text-[#111827]">
                  "{idx === 0
                    ? "Revaloriser mes compétences avec un stage de reconversion validé."
                    : "Recruter rapidement des stagiaires qualifiés et vérifiés."}"
                </p>
              </PremiumCard>
            ))}
          </div>
        </div>
      ) : null}

      {activeSection === "channels" ? (
        <div className="space-y-3">
          <SectionHeader id="channels" title="Canaux" />

          <PremiumCard className="border-[#D5D6E4]">
            <p className="mb-4 text-[11px] font-medium uppercase tracking-[0.08em] text-[#046C70]">Canaux prioritaires</p>
            <div className="divide-y divide-slate-200 dark:divide-slate-700">
              {(plan.channels?.primaryChannels || []).map((channel, idx) => (
                <div key={`${channel}-${idx}`} className="flex items-start justify-between gap-3 py-3">
                  <div className="flex items-start gap-3">
                    <span className="mt-1 flex h-7 w-7 items-center justify-center rounded-full bg-[#CFEAE3] text-[11px] font-medium text-[#046C70]">
                      {idx + 1}
                    </span>
                    <div className="mt-1 flex h-8 w-8 items-center justify-center rounded-[8px] bg-[#CFEAE3] text-[#046C70]">
                      {idx === 0 ? (
                        <svg width="16" height="16" viewBox="0 0 20 20" fill="none">
                          <circle cx="10" cy="6" r="2.6" stroke="#046C70" strokeWidth="1.4" />
                          <path d="M4.7 15c0-2.6 2.3-4.4 5.3-4.4s5.3 1.8 5.3 4.4" stroke="#046C70" strokeWidth="1.4" strokeLinecap="round" />
                        </svg>
                      ) : idx === 1 ? (
                        <svg width="16" height="16" viewBox="0 0 20 20" fill="none">
                          <rect x="4" y="4" width="12" height="12" rx="3" stroke="#046C70" strokeWidth="1.4" />
                          <circle cx="10" cy="10" r="2.7" stroke="#046C70" strokeWidth="1.4" />
                        </svg>
                      ) : (
                        <svg width="16" height="16" viewBox="0 0 20 20" fill="none">
                          <circle cx="9" cy="9" r="5" stroke="#046C70" strokeWidth="1.4" />
                          <path d="M12.7 12.7L16 16" stroke="#046C70" strokeWidth="1.4" strokeLinecap="round" />
                        </svg>
                      )}
                    </div>
                    <div>
                      <p className="text-[13px] font-medium text-[#111827]">{channel}</p>
                      <p className="text-[12px] font-normal text-[#374151]">{plan.channels?.justification || "-"}</p>
                    </div>
                  </div>
                  <Tag className="bg-[#DDEBCF] text-[#355E10]">priorité {idx + 1}</Tag>
                </div>
              ))}
            </div>
          </PremiumCard>

          <div className="grid gap-3 md:grid-cols-2">
            <PremiumCard className="border-[#D5D6E4]">
              <p className="mb-3 text-[11px] font-medium uppercase tracking-[0.08em] text-[#046C70]">Canaux secondaires</p>
              <div className="flex flex-wrap gap-1.5">
                {(plan.channels?.secondaryChannels || []).map((channel, idx) => (
                  <span
                    key={`${channel}-${idx}`}
                    className="rounded-[8px] border border-[#CFCFCF] bg-[#ECEAE5] px-2.5 py-1 text-[11px] font-medium text-[#1F2937]"
                  >
                    {channel}
                  </span>
                ))}
              </div>
            </PremiumCard>

            <PremiumCard className="border-[#A8D4C8] bg-[#CFE3DE]">
              <p className="mb-3 text-[11px] font-medium uppercase tracking-[0.08em] text-[#046C70]">Ton de communication</p>
              <p className="text-[13px] font-normal leading-[1.6] text-[#003A44]">{plan.contentDirection?.tone || "-"}</p>
            </PremiumCard>
          </div>
        </div>
      ) : null}

      {activeSection === "pricing" ? (
        <div className="space-y-3">
          <SectionHeader id="pricing" title="Pricing" />

          <div className="grid gap-3 lg:grid-cols-2">
            <PremiumCard className="overflow-hidden border-[#2A68A8] p-0">
              <div className="bg-[#2868AA] px-5 py-4 text-white">
                <div className="flex items-start justify-between gap-2">
                  <p className="text-[11px] font-medium uppercase tracking-[0.08em]">B2C — Étudiant</p>
                  <Tag className="bg-[#0E4C8D] text-[#D6ECFF]">adoption max</Tag>
                </div>
                <p className="mt-2 text-[15px] font-medium leading-none">Gratuit</p>
                <p className="mt-2 text-[12px] font-normal text-[#9BC8F1]">Matching IA · alertes · offres vérifiées</p>
              </div>
              <div className="bg-[#154C86] px-5 py-3 text-white">
                <p className="text-[12px] font-normal text-[#A6D0FB]">Premium — abonnement mensuel</p>
                <div className="mt-2 flex flex-wrap gap-1.5">
                  <span className="rounded-[8px] border border-[#5FA2E7] bg-[#1E5F9F] px-2.5 py-1 text-[11px] font-medium text-[#A8D5FF]">Analytics</span>
                  <span className="rounded-[8px] border border-[#5FA2E7] bg-[#1E5F9F] px-2.5 py-1 text-[11px] font-medium text-[#A8D5FF]">Alertes prioritaires</span>
                  <span className="rounded-[8px] border border-[#5FA2E7] bg-[#1E5F9F] px-2.5 py-1 text-[11px] font-medium text-[#A8D5FF]">Coaching IA</span>
                </div>
              </div>
            </PremiumCard>

            <PremiumCard className="border-[#D5D6E4]">
              <div className="flex items-start justify-between gap-2">
                <p className="text-[11px] font-medium uppercase tracking-[0.08em] text-[#4B7E1A]">B2B — Entreprise</p>
                <Tag className="bg-[#DDEBCF] text-[#355E10]">revenus principaux</Tag>
              </div>
              <p className="mt-2 text-[13px] font-medium text-[#111827]">{plan.pricingStrategy?.model || "Abonnement / poste"}</p>
              <p className="mt-1 text-[12px] font-normal text-[#111827]">Publication + frais vérification optionnels</p>
              <div className="my-3 border-t border-slate-200 dark:border-slate-700" />
              <div className="flex flex-wrap gap-1.5">
                <span className="rounded-[8px] border border-[#CFCFCF] bg-[#ECEAE5] px-2.5 py-1 text-[11px] font-medium text-[#1F2937]">Publication offres vérifiées</span>
                <span className="rounded-[8px] border border-[#CFCFCF] bg-[#ECEAE5] px-2.5 py-1 text-[11px] font-medium text-[#1F2937]">Dashboard recruteur</span>
                <span className="rounded-[8px] border border-[#CFCFCF] bg-[#ECEAE5] px-2.5 py-1 text-[11px] font-medium text-[#1F2937]">Vivier candidats</span>
              </div>
            </PremiumCard>
          </div>

          <PremiumCard className="border-[#E0D2B5] bg-[#F3E8D5]">
            <p className="mb-2 text-[11px] font-medium uppercase tracking-[0.08em] text-[#8A5B16]">Hypothèses clés</p>
            <ul className="space-y-1.5">
              {(plan.assumptions || []).map((item, idx) => (
                <li key={`${item}-${idx}`} className="flex items-start gap-2 text-[13px] font-normal leading-[1.6] text-[#7A4A10]">
                  <span className="mt-1">·</span>
                  {item}
                </li>
              ))}
            </ul>
          </PremiumCard>
        </div>
      ) : null}

      {activeSection === "gtm" ? (
        <div className="space-y-3">
          <SectionHeader id="gtm" title="Go-to-Market" />

          <PremiumCard className="border-[#D5D6E4]">
            <p className="text-[11px] font-medium uppercase tracking-[0.08em] text-[#C24E1D]">Premiers utilisateurs ciblés</p>
            <p className="mt-2 text-[13px] font-normal leading-[1.6] text-[#111827]">{plan.goToMarket?.targetFirstUsers || "-"}</p>

            <div className="relative mt-4 pl-5">
              <div className="absolute left-[12px] top-[10px] h-[54px] w-[1px] bg-[#CFCFCF]" />
              <div className="space-y-3">
                <div className="flex items-start gap-3">
                  <span className="mt-[1px] flex h-7 w-7 items-center justify-center rounded-full bg-[#F2DADA] text-[13px] font-medium text-[#A64A4A]">
                    1
                  </span>
                  <div>
                    <p className="text-[13px] font-medium leading-[1.6] text-[#111827]">Beta fermée — 3 mois</p>
                    <p className="mt-0.5 text-[12px] font-normal text-[#111827]">{(plan.goToMarket?.launchStrategy || "").split("puis")[0] || "-"}</p>
                  </div>
                </div>

                <div className="flex items-start gap-3">
                  <span className="mt-[1px] flex h-7 w-7 items-center justify-center rounded-full bg-[#DDEBCF] text-[13px] font-medium text-[#355E10]">
                    2
                  </span>
                  <div>
                    <p className="text-[13px] font-medium leading-[1.6] text-[#111827]">Lancement national</p>
                    <p className="mt-0.5 text-[12px] font-normal text-[#111827]">
                      {(plan.goToMarket?.launchStrategy || "").split("puis")[1] || plan.goToMarket?.launchStrategy || "-"}
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </PremiumCard>

          <div className="grid gap-3 lg:grid-cols-2">
            <PremiumCard className="border-[#D5D6E4]">
              <p className="mb-2 text-[11px] font-medium uppercase tracking-[0.08em] text-[#C24E1D]">Partenariats clés</p>
              <div className="flex flex-wrap gap-1.5">
                {(plan.goToMarket?.partnerships || []).map((p, idx) => (
                  <span key={`${p}-${idx}`} className="rounded-[8px] border border-[#CFCFCF] bg-[#ECEAE5] px-2.5 py-1 text-[11px] font-medium text-[#1F2937]">
                    {p}
                  </span>
                ))}
              </div>
            </PremiumCard>

            <PremiumCard className="border-[#D5D6E4]">
              <p className="mb-2 text-[11px] font-medium uppercase tracking-[0.08em] text-[#C24E1D]">Tactiques de croissance</p>
              <ul className="space-y-1">
                {(plan.goToMarket?.earlyGrowthTactics || []).map((item, idx) => (
                  <li key={`${item}-${idx}`} className="flex items-start gap-2 text-[13px] font-normal leading-[1.6] text-[#111827]">
                    <span className="mt-[2px] text-[#D84C1B]">↗</span>
                    {item}
                  </li>
                ))}
              </ul>
            </PremiumCard>
          </div>
        </div>
      ) : null}

      {activeSection === "action" ? (
        <div className="space-y-3">
          <SectionHeader id="action" title="Plan d'action" />

          <div className="grid gap-3 lg:grid-cols-3">
            <PremiumCard className="p-0">
              <div className="rounded-t-[12px] bg-rose-600 px-4 py-3 text-[12px] font-medium uppercase tracking-[0.08em] text-white">Court terme 0-3 mois</div>
              <div className="space-y-2 p-4">
                {(plan.actionPlan?.shortTerm || []).map((step, idx) => (
                  <div key={`${step}-${idx}`} className="flex items-start gap-2">
                    <span className="flex h-7 w-7 items-center justify-center rounded-full bg-rose-100 text-[11px] font-medium text-rose-700 dark:bg-rose-900/60 dark:text-rose-300">
                      {idx + 1}
                    </span>
                    <p className="text-[13px] font-normal leading-[1.6] text-slate-700 dark:text-slate-300">{step}</p>
                  </div>
                ))}
              </div>
            </PremiumCard>

            <PremiumCard className="border-l-2 border-l-amber-300 p-0">
              <div className="rounded-t-[12px] bg-amber-500 px-4 py-3 text-[12px] font-medium uppercase tracking-[0.08em] text-white">Moyen terme 3-12 mois</div>
              <div className="space-y-2 p-4">
                {(plan.actionPlan?.midTerm || []).map((step, idx) => (
                  <div key={`${step}-${idx}`} className="flex items-start gap-2">
                    <span className="flex h-7 w-7 items-center justify-center rounded-full bg-amber-100 text-[11px] font-medium text-amber-700 dark:bg-amber-900/60 dark:text-amber-300">
                      {idx + 1}
                    </span>
                    <p className="text-[13px] font-normal leading-[1.6] text-slate-700 dark:text-slate-300">{step}</p>
                  </div>
                ))}
              </div>
            </PremiumCard>

            <PremiumCard className="border-l-2 border-l-blue-300 p-0">
              <div className="rounded-t-[12px] bg-blue-600 px-4 py-3 text-[12px] font-medium uppercase tracking-[0.08em] text-white">Long terme 12 mois+</div>
              <div className="space-y-2 p-4">
                {(plan.actionPlan?.longTerm || []).map((step, idx) => (
                  <div key={`${step}-${idx}`} className="flex items-start gap-2">
                    <span className="flex h-7 w-7 items-center justify-center rounded-full bg-blue-100 text-[11px] font-medium text-blue-700 dark:bg-blue-900/60 dark:text-blue-300">
                      {idx + 1}
                    </span>
                    <p className="text-[13px] font-normal leading-[1.6] text-slate-700 dark:text-slate-300">{step}</p>
                  </div>
                ))}
              </div>
            </PremiumCard>
          </div>
        </div>
      ) : null}

      <PremiumCard>
        <div className="flex items-center justify-between">
          <button
            type="button"
            disabled={activeIndex === 0}
            onClick={() => setActiveSection(SECTION_TABS[Math.max(0, activeIndex - 1)].id)}
            className="inline-flex items-center gap-1 rounded-[10px] border border-[#A9B6C5] bg-[#F5F6F8] px-4 py-2 text-[13px] font-medium text-[#111827] transition hover:bg-[#ECEFF3] disabled:opacity-40"
          >
            <span>←</span> Précédent
          </button>

          <div className="flex items-center gap-2">
            {SECTION_TABS.map((tab, idx) => (
              <button
                key={tab.id}
                type="button"
                onClick={() => setActiveSection(tab.id)}
                className="h-7 w-9 rounded-full border"
                style={{
                  borderColor: "#A9B6C5",
                  backgroundColor: idx === activeIndex ? "#DDE3EB" : "#F5F6F8",
                }}
                aria-label={tab.label}
              />
            ))}
          </div>

          <button
            type="button"
            disabled={activeIndex === SECTION_TABS.length - 1}
            onClick={() => setActiveSection(SECTION_TABS[Math.min(SECTION_TABS.length - 1, activeIndex + 1)].id)}
            className="inline-flex items-center gap-1 rounded-[10px] border border-[#A9B6C5] bg-[#F5F6F8] px-4 py-2 text-[13px] font-medium text-[#111827] transition hover:bg-[#ECEFF3] disabled:opacity-40"
          >
            Suivant <span>→</span>
          </button>
        </div>
      </PremiumCard>
    </div>
  );
}
