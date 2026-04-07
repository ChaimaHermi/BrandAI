import { useEffect, useState } from "react";
import { useOutletContext } from "react-router-dom";
import { useMarketAgent } from "../hooks/useMarketAgent";
import { CLARITY_SCORE_MIN_PIPELINE } from "@/agents/clarifier/constants";
import MarketDashboardHeader from "../components/MarketDashboardHeader";
import MarketDashboardTabs from "../components/MarketDashboardTabs";
import MarketTabEmpty from "../components/MarketTabEmpty";
import MarketRawDataViewer from "../components/MarketRawDataViewer";
import MarketApercu from "../components/MarketApercu";
import MarketCompetitors from "../components/MarketCompetitors";
import MarketVOC from "../components/MarketVOC";
import MarketTrendsRisks from "../components/MarketTrendsRisks";
import MarketStrategy from "../components/MarketStrategy";
import MarketKeywords from "../components/MarketKeywords";

const marketTabs = [
  { id: "raw", label: "Raw JSON" },
  { id: "apercu", label: "Aperçu" },
  { id: "competiteurs", label: "Compétiteurs" },
  { id: "voc", label: "VOC" },
  { id: "tendances", label: "Tendances" },
  { id: "strategie", label: "Stratégie" },
  { id: "mots-cles", label: "Mots-clés" },
];

export default function MarketAnalysisDashboard() {
  const { idea, token } = useOutletContext();
  const { rawReport, isLoading, error, loadLatest, startMarketAnalysis } =
    useMarketAgent({ idea, token });
  const [activeTab, setActiveTab] = useState("raw");

  useEffect(() => {
    if (!idea?.id || !token) return;
    loadLatest().catch(() => {});
  }, [idea?.id, token, loadLatest]);

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

  const activeLabel =
    marketTabs.find((tab) => tab.id === activeTab)?.label ?? "Section";

  const canRelaunchPipeline =
    !!idea?.id &&
    !!token &&
    idea?.clarity_status === "clarified" &&
    (idea?.clarity_score ?? 0) >= CLARITY_SCORE_MIN_PIPELINE &&
    !isLoading;

  const handleRelaunchPipeline = () => {
    if (!canRelaunchPipeline) return;
    startMarketAnalysis({ mode: "pipeline" });
  };

  return (
    <div className="app-content-scroll flex flex-1 flex-col gap-3">
      <div className="flex items-center justify-end">
        <button
          type="button"
          onClick={handleRelaunchPipeline}
          disabled={!canRelaunchPipeline}
          className={
            canRelaunchPipeline
              ? "rounded-xl bg-violet-600 px-4 py-2 text-sm font-semibold text-white hover:bg-violet-700"
              : "cursor-not-allowed rounded-xl bg-gray-200 px-4 py-2 text-sm font-semibold text-gray-500"
          }
        >
          {isLoading ? "Pipeline en cours..." : "Relancer pipeline"}
        </button>
      </div>

      <MarketDashboardHeader
        clarified_idea={clarifiedIdea}
        idea_id={rawReport?.idea_id ?? idea?.id}
        competitorsCount={competitorsCount}
      />

      <MarketDashboardTabs activeTab={activeTab} onTabChange={setActiveTab} />

      {isLoading ? (
        <div className="rounded-xl border border-violet-200 bg-white p-4 text-sm text-violet-600">
          Chargement des données marché...
        </div>
      ) : error ? (
        <div className="rounded-xl border border-red-200 bg-white p-4 text-sm text-red-600">
          {error}
        </div>
      ) : activeTab === "raw" ? (
        <MarketRawDataViewer data={rawReport} />
      ) : activeTab === "apercu" ? (
        <MarketApercu market={rawReport?.market} />
      ) : activeTab === "competiteurs" ? (
        <MarketCompetitors
          competitors={
            rawReport?.competitor?.top_competitors ??
            rawReport?.competitor?.competitors ??
            []
          }
        />
      ) : activeTab === "voc" ? (
        <MarketVOC voc={rawReport?.voc} />
      ) : activeTab === "tendances" ? (
        <MarketTrendsRisks trends={rawReport?.trends} />
      ) : activeTab === "strategie" ? (
        <MarketStrategy strategy={rawReport?.strategy} />
      ) : activeTab === "mots-cles" ? (
        <MarketKeywords keywords={rawReport?.keywords} />
      ) : (
        <MarketTabEmpty label={activeLabel} />
      )}
    </div>
  );
}
