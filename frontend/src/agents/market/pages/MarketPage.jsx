import { useEffect, useRef } from "react";
import { useLocation, useNavigate, useOutletContext } from "react-router-dom";
import { useMarketAgent } from "../hooks/useMarketAgent";
import { MARKET_TABS } from "../constants";
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
    <div className="rounded-xl border border-slate-200 bg-white p-6 text-center text-sm text-slate-600 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-300">
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

  const activeIndex = MARKET_TABS.findIndex((tab) => tab.id === activeTab);
  const currentIndex = activeIndex >= 0 ? activeIndex : 0;
  const hasPrev = currentIndex > 0;
  const hasNext = currentIndex < MARKET_TABS.length - 1;
  const prevTab = hasPrev ? MARKET_TABS[currentIndex - 1] : null;
  const nextTab = hasNext ? MARKET_TABS[currentIndex + 1] : null;

  return (
    <div className="flex flex-1 flex-col gap-3 overflow-y-auto p-4">
      <MarketHeader
        meta={report?.meta}
        idea={idea}
        onRelaunch={handleRelaunchMarketOnly}
        isLoading={isLoading}
      />
      <MarketXaiBlock steps={xaiSteps} isLoading={isLoading} error={error} />

      <div className="rounded-xl border border-slate-200 bg-white p-3 dark:border-slate-700 dark:bg-slate-900">
        <MarketTabs activeTab={activeTab} onChange={setActiveTab} />
        <div className="mt-3">{hasData ? renderActiveTab() : <EmptyState />}</div>
        {hasData ? (
          <div className="mt-4 border-t border-slate-200 pt-3 dark:border-slate-700">
            <div className="flex items-center justify-between gap-3">
              <button
                type="button"
                disabled={!hasPrev}
                onClick={() => hasPrev && setActiveTab(prevTab.id)}
                className="rounded-md border border-slate-300 bg-white px-3 py-1.5 text-sm font-medium text-slate-700 disabled:cursor-not-allowed disabled:opacity-50 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-200"
              >
                Précédent
              </button>

              <div className="flex items-center gap-2">
                {MARKET_TABS.map((tab) => {
                  const isActive = tab.id === activeTab;
                  return (
                    <button
                      key={tab.id}
                      type="button"
                      aria-label={tab.label}
                      onClick={() => setActiveTab(tab.id)}
                      className={`h-2.5 w-2.5 rounded-full border ${
                        isActive
                          ? "border-blue-600 bg-blue-600 dark:border-blue-400 dark:bg-blue-400"
                          : "border-slate-400 bg-transparent dark:border-slate-500"
                      }`}
                    />
                  );
                })}
              </div>

              <button
                type="button"
                disabled={!hasNext}
                onClick={() => hasNext && setActiveTab(nextTab.id)}
                className="rounded-md border border-slate-300 bg-white px-3 py-1.5 text-sm font-medium text-slate-700 disabled:cursor-not-allowed disabled:opacity-50 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-200"
              >
                Suivant
              </button>
            </div>
          </div>
        ) : null}
      </div>
    </div>
  );
}

