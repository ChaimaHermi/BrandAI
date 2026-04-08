import { useEffect, useRef, useState } from "react";
import { useLocation } from "react-router-dom";
import { useMarketAgent } from "../hooks/useMarketAgent";
import { CLARITY_SCORE_MIN_PIPELINE } from "@/agents/clarifier/constants";
import { AGENTS } from "@/agents";
import { TabBar } from "@/shared/ui/TabBar";
import { ErrorBanner } from "@/shared/ui/ErrorBanner";
import { Loader } from "@/shared/ui/Loader";
import { AgentPageHeader } from "@/agents/shared/components/AgentPageHeader";
import { usePipeline } from "@/context/PipelineContext";
import MarketDashboardHeader from "../components/MarketDashboardHeader";
import MarketRawDataViewer from "../components/MarketRawDataViewer";
import MarketApercu from "../components/MarketApercu";
import MarketCompetitors from "../components/MarketCompetitors";
import MarketVOC from "../components/MarketVOC";
import MarketTrendsRisks from "../components/MarketTrendsRisks";
import MarketStrategy from "../components/MarketStrategy";
import MarketKeywords from "../components/MarketKeywords";
import MarketTabEmpty from "../components/MarketTabEmpty";

// "Aperçu" is the default — raw data is last and accessible but not prominent.
const MARKET_TABS = [
  { id: "apercu", label: "Aperçu" },
  { id: "competiteurs", label: "TOP compétiteurs" },
  { id: "voc", label: "VOC" },
  { id: "tendances", label: "Tendances" },
  { id: "strategie", label: "Stratégie" },
  { id: "mots-cles", label: "Mots-clés" },
  { id: "raw", label: "Données brutes" },
];

const marketAgent = AGENTS.find((a) => a.id === "market");

export default function MarketPage() {
  const { idea, token } = usePipeline();
  const location = useLocation();
  const lastAutoStartKeyRef = useRef("");
  const { rawReport, isLoading, error, loadLatest, startMarketAnalysis } =
    useMarketAgent({ idea, token });
  const [activeTab, setActiveTab] = useState("apercu");

  // Auto-start pipeline when navigated from sidebar "Lancer le pipeline" button.
  useEffect(() => {
    if (!idea?.id || !token) return;

    const state = location.state;
    // #region agent log
    fetch("http://127.0.0.1:7388/ingest/0467a1a6-9592-4997-af51-266c4e6ab3de", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-Debug-Session-Id": "2401d3",
      },
      body: JSON.stringify({
        sessionId: "2401d3",
        runId: "pre-fix",
        hypothesisId: "H2",
        location: "MarketPage.jsx:47",
        message: "MarketPage effect",
        data: {
          ideaId: idea.id,
          autoStart: !!state?.autoStartMarket,
          locationKey: location.key,
        },
        timestamp: Date.now(),
      }),
    }).catch(() => {});
    // #endregion
    if (state?.autoStartMarket) {
      // Ensure each navigation intent can trigger a new launch once.
      const launchKey = `${location.key}:${state?.sourceIdeaId || idea.id}`;
      if (lastAutoStartKeyRef.current === launchKey) return;
      lastAutoStartKeyRef.current = launchKey;
      // #region agent log
      fetch(
        "http://127.0.0.1:7388/ingest/0467a1a6-9592-4997-af51-266c4e6ab3de",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "X-Debug-Session-Id": "2401d3",
          },
          body: JSON.stringify({
            sessionId: "2401d3",
            runId: "pre-fix",
            hypothesisId: "H2",
            location: "MarketPage.jsx:54",
            message: "Auto start pipeline call",
            data: { ideaId: idea.id, launchKey },
            timestamp: Date.now(),
          }),
        },
      ).catch(() => {});
      // #endregion
      startMarketAnalysis({
        mode: "pipeline",
        clarifiedIdea: state.clarifiedIdea,
      });
    } else {
      loadLatest().catch(() => {});
    }
  }, [
    idea?.id,
    token,
    location.key,
    location.state,
    startMarketAnalysis,
    loadLatest,
  ]);

  const clarifiedIdea = rawReport?.clarified_idea ?? {
    short_pitch: idea?.clarity_short_pitch ?? "",
    problem: idea?.clarity_problem ?? "",
    sector: idea?.clarity_sector ?? "",
    country: idea?.clarity_country ?? "",
    country_code: idea?.clarity_country_code ?? "",
    target_users: idea?.clarity_target_users ?? "",
    solution_description: idea?.clarity_solution ?? "",
  };

  const competitorsCount =
    rawReport?.competitor?.top_competitors?.length ??
    rawReport?.competitor?.competitors?.length ??
    0;

  const canRelaunch =
    !!idea?.id &&
    !!token &&
    idea?.clarity_status === "clarified" &&
    (idea?.clarity_score ?? 0) >= CLARITY_SCORE_MIN_PIPELINE &&
    !isLoading;

  const relaunchAction = (
    <button
      type="button"
      onClick={() => {
        // #region agent log
        fetch(
          "http://127.0.0.1:7388/ingest/0467a1a6-9592-4997-af51-266c4e6ab3de",
          {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
              "X-Debug-Session-Id": "2401d3",
            },
            body: JSON.stringify({
              sessionId: "2401d3",
              runId: "pre-fix",
              hypothesisId: "H2",
              location: "MarketPage.jsx:98",
              message: "Relaunch clicked",
              data: { ideaId: idea?.id || null, canRelaunch, isLoading },
              timestamp: Date.now(),
            }),
          },
        ).catch(() => {});
        // #endregion
        canRelaunch && startMarketAnalysis({ mode: "pipeline" });
      }}
      disabled={!canRelaunch}
      className={`rounded-full px-4 py-1.5 text-[11px] font-bold transition-all ${
        canRelaunch
          ? "bg-gradient-to-br from-[#7F77DD] to-[#534AB7] text-white shadow-[0_2px_8px_rgba(124,58,237,0.25)]"
          : "cursor-not-allowed bg-[#f0eeff] text-[#AFA9EC]"
      }`}
    >
      {isLoading ? "En cours…" : "Relancer"}
    </button>
  );

  function renderTabContent() {
    if (activeTab === "raw") return <MarketRawDataViewer data={rawReport} />;
    if (activeTab === "apercu")
      return <MarketApercu market={rawReport?.market} />;
    if (activeTab === "competiteurs")
      return (
        <MarketCompetitors
          competitors={
            rawReport?.competitor?.top_competitors ??
            rawReport?.competitor?.competitors ??
            []
          }
        />
      );
    if (activeTab === "voc") return <MarketVOC voc={rawReport?.voc} />;
    if (activeTab === "tendances")
      return <MarketTrendsRisks trends={rawReport?.trends} />;
    if (activeTab === "strategie")
      return <MarketStrategy strategy={rawReport?.strategy} />;
    if (activeTab === "mots-cles")
      return <MarketKeywords keywords={rawReport?.keywords} />;
    const label =
      MARKET_TABS.find((t) => t.id === activeTab)?.label ?? "Section";
    return <MarketTabEmpty label={label} />;
  }

  return (
    <div className="app-content-scroll flex flex-1 flex-col gap-3">
      <AgentPageHeader
        agent={marketAgent}
        subtitle="Analyse de marché · Étape 2 sur 6"
        action={relaunchAction}
      />

      {/* Project summary card */}
      <MarketDashboardHeader
        clarified_idea={clarifiedIdea}
        idea_id={rawReport?.idea_id ?? idea?.id}
        competitorsCount={competitorsCount}
      />

      {/* Loading */}
      {isLoading && (
        <div className="flex items-center gap-3 rounded-[14px] border border-[#e8e4ff] bg-white px-5 py-4">
          <Loader className="h-5 w-5" />
          <span className="text-[13px] text-[#534AB7]">Pipeline en cours…</span>
        </div>
      )}

      {/* Error */}
      {error && <ErrorBanner message={error} />}

      {/* Tabs — shown when data exists */}
      {!isLoading && rawReport && (
        <>
          <TabBar
            tabs={MARKET_TABS}
            activeId={activeTab}
            onChange={setActiveTab}
          />
          {renderTabContent()}
        </>
      )}
    </div>
  );
}
