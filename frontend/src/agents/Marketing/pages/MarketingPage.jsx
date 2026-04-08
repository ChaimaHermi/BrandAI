import { useEffect, useState } from "react";
import {
  FiTarget, FiUsers, FiRadio, FiDollarSign, FiFlag, FiCalendar,
} from "react-icons/fi";
import { usePipeline } from "@/context/PipelineContext";
import { useMarketingAgent } from "../hooks/useMarketingAgent";
import { EmptyState } from "@/shared/ui/EmptyState";
import { ErrorBanner } from "@/shared/ui/ErrorBanner";
import { Loader } from "@/shared/ui/Loader";
import { SectionIntro } from "@/shared/ui/SectionIntro";
import { MarketingHeader, SECTION_TABS } from "../components/MarketingHeader";
import { PositioningSection } from "../components/sections/PositioningSection";
import { TargetsSection }     from "../components/sections/TargetsSection";
import { ChannelsSection }    from "../components/sections/ChannelsSection";
import { PricingSection }     from "../components/sections/PricingSection";
import { GtmSection }         from "../components/sections/GtmSection";
import { ActionSection }      from "../components/sections/ActionSection";

const SECTION_MAP = {
  positioning: PositioningSection,
  targets:     TargetsSection,
  channels:    ChannelsSection,
  pricing:     PricingSection,
  gtm:         GtmSection,
  action:      ActionSection,
};

const SECTION_INTROS = {
  positioning: { icon: FiTarget,    title: "Positionnement",        description: "Segment cible, différenciation, proposition de valeur et message principal." },
  targets:     { icon: FiUsers,     title: "Cibles",                description: "Persona principal, focus segment et personas secondaires." },
  channels:    { icon: FiRadio,     title: "Canaux de distribution", description: "Canaux prioritaires, secondaires, justification et ton éditorial." },
  pricing:     { icon: FiDollarSign,title: "Stratégie Pricing",      description: "Modèle tarifaire, logique de pricing et hypothèses clés." },
  gtm:         { icon: FiFlag,      title: "Go-to-Market",           description: "Premiers utilisateurs, stratégie de lancement, partenariats et tactiques de croissance." },
  action:      { icon: FiCalendar,  title: "Plan d'action",          description: "Actions court terme, moyen terme et long terme pour le lancement." },
};

export default function MarketingPage() {
  const { idea, token } = usePipeline();
  const { plan, hasData, isLoading, error, loadLatest } = useMarketingAgent({ idea, token });
  const [activeSection, setActiveSection] = useState("positioning");

  useEffect(() => {
    if (!idea?.id || !token) return;
    loadLatest().catch(() => {});
  }, [idea?.id, token, loadLatest]);

  const activeIndex = SECTION_TABS.findIndex((s) => s.id === activeSection);

  function prevSection() {
    if (activeIndex > 0) setActiveSection(SECTION_TABS[activeIndex - 1].id);
  }
  function nextSection() {
    if (activeIndex < SECTION_TABS.length - 1) setActiveSection(SECTION_TABS[activeIndex + 1].id);
  }

  const ActiveSection = SECTION_MAP[activeSection] ?? null;
  const intro         = SECTION_INTROS[activeSection];

  return (
    <div className="app-content-scroll flex flex-1 flex-col gap-3">
      <MarketingHeader
        idea={idea}
        plan={plan}
        activeTab={activeSection}
        onTabChange={setActiveSection}
      />

      {isLoading && !hasData && (
        <div className="flex items-center gap-3 rounded-2xl border border-brand-border bg-white px-5 py-4 shadow-card">
          <Loader className="h-5 w-5" />
          <span className="text-sm text-brand-dark">Chargement du plan marketing…</span>
        </div>
      )}

      {error && <ErrorBanner message={error} variant={hasData ? "warning" : "error"} />}

      {!isLoading && !hasData && !error && (
        <EmptyState
          title="Aucun plan marketing disponible"
          description="Lancez le pipeline depuis le clarifier pour générer l'analyse de marché et le plan marketing."
        />
      )}

      {hasData && (
        <div className="flex flex-col gap-3">
          {/* Section intro card */}
          {intro && (
            <SectionIntro
              icon={intro.icon}
              title={intro.title}
              description={intro.description}
            />
          )}

          {ActiveSection && <ActiveSection plan={plan} />}
        </div>
      )}

      {/* Section navigation */}
      {hasData && (
        <div className="flex items-center justify-between rounded-2xl border border-brand-border bg-white px-5 py-3 shadow-card">
          <button
            type="button"
            disabled={activeIndex === 0}
            onClick={prevSection}
            className="rounded-full border border-brand-border bg-white px-4 py-1.5 text-xs font-semibold text-ink-muted transition-all disabled:opacity-40 hover:border-brand-muted hover:text-brand-dark"
          >
            ← Précédent
          </button>
          <span className="text-xs text-ink-subtle">
            {activeIndex + 1} / {SECTION_TABS.length}
          </span>
          <button
            type="button"
            disabled={activeIndex === SECTION_TABS.length - 1}
            onClick={nextSection}
            className="rounded-full border border-brand-border bg-white px-4 py-1.5 text-xs font-semibold text-ink-muted transition-all disabled:opacity-40 hover:border-brand-muted hover:text-brand-dark"
          >
            Suivant →
          </button>
        </div>
      )}
    </div>
  );
}
