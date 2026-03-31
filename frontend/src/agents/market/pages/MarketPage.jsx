import { useEffect, useRef } from "react";
import { useLocation, useOutletContext } from "react-router-dom";
import { useMarketAgent } from "../hooks/useMarketAgent";
import MarketHeader from "../components/MarketHeader";
import MarketTabs from "../components/MarketTabs";
import OverviewTab from "../components/OverviewTab";
import VocTab from "../components/VocTab";
import CompetitorsTab from "../components/CompetitorsTab";
import SwotTab from "../components/SwotTab";
import RisksRecoTab from "../components/RisksRecoTab";
import SourcesTab from "../components/SourcesTab";
import MarketXaiBlock from "../components/MarketXaiBlock";

function EmptyState() {
  return (
    <div className="rounded-xl border border-[#e8e4ff] bg-white p-6 text-center text-sm text-[#7a76a3]">
      Aucun rapport de marché disponible. Lance une analyse depuis Clarifier.
    </div>
  );
}

export default function MarketPage() {
  const { idea, token, refetchIdea } = useOutletContext();
  const location = useLocation();
  const autoStartedRef = useRef(false);

  const {
    activeTab,
    setActiveTab,
    report,
    hasData,
    xaiSteps,
    isLoading,
    error,
    loadLatest,
    startMarketAnalysis,
  } = useMarketAgent({ idea, token });

  useEffect(() => {
    if (!idea?.id || !token) return;
    loadLatest().catch(() => {});
  }, [idea?.id, token, loadLatest]);

  useEffect(() => {
    if (!idea?.id || !token) return;
    if (autoStartedRef.current) return;

    const state = location.state || {};
    if (state.autoStartMarket && state.clarifiedIdea) {
      autoStartedRef.current = true;
      startMarketAnalysis({
        clarifiedIdea: state.clarifiedIdea,
        onDone: () => refetchIdea?.(),
      });
    }
  }, [idea?.id, token, location.state, startMarketAnalysis, refetchIdea]);

  const renderActiveTab = () => {
    if (!report) return <EmptyState />;
    if (activeTab === "overview") return <OverviewTab report={report} />;
    if (activeTab === "voc") return <VocTab report={report} />;
    if (activeTab === "competitors") return <CompetitorsTab report={report} />;
    if (activeTab === "swot") return <SwotTab report={report} />;
    if (activeTab === "risks") return <RisksRecoTab report={report} />;
    if (activeTab === "sources") return <SourcesTab report={report} />;
    return <OverviewTab report={report} />;
  };

  return (
    <div className="flex flex-1 flex-col gap-3 overflow-y-auto p-4">
      <MarketHeader meta={report?.meta} overview={report?.overview} />
      <MarketXaiBlock steps={xaiSteps} isLoading={isLoading} error={error} />

      <div className="rounded-xl border border-[#e8e4ff] bg-[#f7f6ff] p-3">
        <MarketTabs activeTab={activeTab} onChange={setActiveTab} />
        <div className="mt-3">{hasData ? renderActiveTab() : <EmptyState />}</div>
      </div>
    </div>
  );
}

