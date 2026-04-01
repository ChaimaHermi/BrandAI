import { useEffect, useRef } from "react";
import { useLocation, useNavigate, useOutletContext } from "react-router-dom";
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
    <div className="rounded-xl border border-[#e8e4ff] bg-white p-6 text-center text-[13px] font-normal leading-[1.6] text-[#7a76a3]">
      Aucun rapport de marché disponible. Lance une analyse depuis Clarifier.
    </div>
  );
}

export default function MarketPage() {
  const { idea, token, refetchIdea } = useOutletContext();
  const location = useLocation();
  const navigate = useNavigate();
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
    if (state.autoStartMarket && state.sourceIdeaId === idea.id) {
      autoStartedRef.current = true;
      startMarketAnalysis({
        clarifiedIdea: state.clarifiedIdea || undefined,
        onDone: () => refetchIdea?.(),
      });

      // Clear one-shot navigation state to avoid replay on future mounts.
      navigate(location.pathname, { replace: true, state: null });
      return;
    }

    // Safety: ignore stale navigation state coming from another idea.
    if (state.autoStartMarket && state.sourceIdeaId && state.sourceIdeaId !== idea.id) {
      navigate(location.pathname, { replace: true, state: null });
    }
  }, [idea?.id, token, location.state, startMarketAnalysis, refetchIdea, navigate, location.pathname]);

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

  const handleRelaunchMarketOnly = () => {
    startMarketAnalysis({
      mode: "market_only",
      onDone: () => refetchIdea?.(),
    });
  };

  return (
    <div className="app-content-scroll flex flex-1 flex-col gap-3">
      <MarketHeader
        meta={report?.meta}
        idea={idea}
        onRelaunch={handleRelaunchMarketOnly}
        isLoading={isLoading}
      />
      <MarketXaiBlock steps={xaiSteps} isLoading={isLoading} error={error} />

      <div className="rounded-xl border border-[#e8e4ff] bg-[#f7f6ff] p-3">
        <MarketTabs activeTab={activeTab} onChange={setActiveTab} />
        <div className="mt-3">{hasData ? renderActiveTab() : <EmptyState />}</div>
      </div>
    </div>
  );
}

