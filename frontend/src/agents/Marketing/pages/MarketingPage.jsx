import { useEffect, useState } from "react";
import {
  FiTarget, FiRadio, FiLayout, FiFlag,
} from "react-icons/fi";
import { usePipeline } from "@/context/PipelineContext";
import { useMarketingAgent } from "@/agents/Marketing/hooks/useMarketingAgent";
import { EmptyState } from "@/shared/ui/EmptyState";
import { ErrorBanner } from "@/shared/ui/ErrorBanner";
import { Loader } from "@/shared/ui/Loader";
import { SectionIntro } from "@/shared/ui/SectionIntro";
import { MarketingHeader, SECTION_TABS } from "@/agents/Marketing/components/MarketingHeader";
import { PositioningSection }     from "@/agents/Marketing/components/sections/PositioningSection";
import { ChannelsSection }         from "@/agents/Marketing/components/sections/ChannelsSection";
import { ContentStrategySection }  from "@/agents/Marketing/components/sections/ContentStrategySection";
import { GtmSection }              from "@/agents/Marketing/components/sections/GtmSection";
import { ActionSection }           from "@/agents/Marketing/components/sections/ActionSection";

function ChannelsContentSection({ plan }) {
  const channelCount = Array.isArray(plan?.channels?.primaryChannelsDetailed)
    ? plan.channels.primaryChannelsDetailed.length
    : 0;

  return (
    <div className="flex flex-col gap-5">
      <div className="rounded-2xl border border-brand-border bg-white p-4 shadow-card">
        <div className="mb-3 flex items-center justify-between">
          <p className="text-[11px] font-extrabold uppercase tracking-widest text-ink-muted">
            Canaux recommandés
          </p>
          <span className="rounded-full border border-brand-border bg-brand-light px-2.5 py-1 text-[10px] font-bold text-brand-dark">
            {channelCount} canal{channelCount > 1 ? "x" : ""}
          </span>
        </div>
        <ChannelsSection
          plan={plan}
          showBudget={false}
          showChannels={true}
          showChannelsTitle={false}
        />
      </div>
      <div className="rounded-2xl border border-brand-border bg-white p-4 shadow-card">
        <p className="mb-3 text-[11px] font-extrabold uppercase tracking-widest text-ink-muted">
          Stratégie de contenu
        </p>
        <ContentStrategySection plan={plan} />
      </div>
    </div>
  );
}

function GtmActionSection({ plan }) {
  return (
    <div className="flex flex-col gap-4">
      <div className="rounded-2xl border border-brand-border bg-white p-4 shadow-card">
        <p className="mb-3 text-[11px] font-extrabold uppercase tracking-widest text-ink-muted">
          Go-to-Market
        </p>
        <GtmSection plan={plan} />
      </div>
      <div className="rounded-2xl border border-brand-border bg-white p-4 shadow-card">
        <p className="mb-3 text-[11px] font-extrabold uppercase tracking-widest text-ink-muted">
          Plan d'action
        </p>
        <ActionSection plan={plan} />
      </div>
    </div>
  );
}

const SECTION_MAP = {
  positioning: PositioningSection,
  budget:      ({ plan }) => <ChannelsSection plan={plan} showBudget={true} showChannels={false} />,
  channels_content: ChannelsContentSection,
  gtm_action:  GtmActionSection,
};

const SECTION_INTROS = {
  positioning: {
    icon: FiTarget,
    title: "Positionnement & Cibles",
    description: "Segment cible, persona principal, focus marché, différenciation, proposition de valeur et message.",
  },
  budget: {
    icon: FiRadio,
    title: "Budget lancement",
    description: "Proposition de répartition du budget de lancement avec logique et justifications.",
  },
  channels_content: {
    icon: FiLayout,
    title: "Canaux & Stratégie de contenu",
    description: "Canaux recommandés et proposition de stratégie de contenu par plateforme.",
  },
  gtm_action: {
    icon: FiFlag,
    title: "Go-to-Market & Plan d'action",
    description: "Plan d'entrée dans le marché puis exécution opérationnelle court, moyen et long terme.",
  },
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
