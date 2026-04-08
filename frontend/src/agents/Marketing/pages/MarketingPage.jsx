import { useEffect, useState } from "react";
import { usePipeline } from "@/context/PipelineContext";
import { useMarketingAgent } from "../hooks/useMarketingAgent";
import { EmptyState } from "@/shared/ui/EmptyState";
import { ErrorBanner } from "@/shared/ui/ErrorBanner";
import { Loader } from "@/shared/ui/Loader";
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

  return (
    <div className="app-content-scroll flex flex-1 flex-col gap-3">
      <MarketingHeader
        idea={idea}
        plan={plan}
        activeTab={activeSection}
        onTabChange={setActiveSection}
      />

      {isLoading && !hasData && (
        <div className="flex items-center gap-3 rounded-[14px] border border-[#e8e4ff] bg-white px-5 py-4">
          <Loader className="h-5 w-5" />
          <span className="text-[13px] text-[#534AB7]">Chargement du plan marketing…</span>
        </div>
      )}

      {error && <ErrorBanner message={error} variant={hasData ? "warning" : "error"} />}

      {!isLoading && !hasData && !error && (
        <EmptyState
          title="Aucun plan marketing disponible"
          description="Lancez le pipeline depuis le clarifier pour générer l'analyse de marché et le plan marketing."
        />
      )}

      {hasData && ActiveSection && (
        <ActiveSection plan={plan} />
      )}

      {hasData && (
        <div className="flex items-center justify-between rounded-[14px] border border-[#e8e4ff] bg-white px-5 py-3">
          <button
            type="button"
            disabled={activeIndex === 0}
            onClick={prevSection}
            className="rounded-full border border-[#e8e4ff] bg-white px-4 py-1.5 text-[12px] font-semibold text-gray-500 transition-all disabled:opacity-40 hover:border-[#AFA9EC] hover:text-[#534AB7]"
          >
            ← Précédent
          </button>
          <span className="text-[11px] text-gray-400">
            {activeIndex + 1} / {SECTION_TABS.length}
          </span>
          <button
            type="button"
            disabled={activeIndex === SECTION_TABS.length - 1}
            onClick={nextSection}
            className="rounded-full border border-[#e8e4ff] bg-white px-4 py-1.5 text-[12px] font-semibold text-gray-500 transition-all disabled:opacity-40 hover:border-[#AFA9EC] hover:text-[#534AB7]"
          >
            Suivant →
          </button>
        </div>
      )}
    </div>
  );
}
