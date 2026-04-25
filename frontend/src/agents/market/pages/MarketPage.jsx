import { useEffect, useRef, useState } from "react";
import { useLocation } from "react-router-dom";
import {
  FiBarChart2, FiUsers, FiMessageSquare, FiTrendingUp,
  FiCompass, FiSearch, FiDatabase,
} from "react-icons/fi";
import { useMarketAgent } from "../hooks/useMarketAgent";
import { CLARITY_SCORE_MIN_PIPELINE } from "@/agents/clarifier/constants";
import { AGENTS } from "@/agents";
import { TabBar } from "@/shared/ui/TabBar";
import { SectionIntro } from "@/shared/ui/SectionIntro";
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
import PipelineLaunchModal from "../components/PipelineLaunchModal";

const MARKET_TABS = [
  { id: "apercu",       label: "Aperçu" },
  { id: "competiteurs", label: "TOP compétiteurs" },
  { id: "voc",          label: "VOC" },
  { id: "tendances",    label: "Tendances" },
  { id: "strategie",    label: "Stratégie" },
  { id: "mots-cles",    label: "Mots-clés" },
  { id: "raw",          label: "Données brutes" },
];

const TAB_INTROS = {
  apercu:       { icon: FiBarChart2,    title: "Aperçu du marché",        description: "Taille, revenus, CAGR et taux d'adoption — données clés du marché cible." },
  competiteurs: { icon: FiUsers,        title: "TOP Compétiteurs",         description: "Analyse des acteurs en présence : forces, faiblesses, positionnement." },
  voc:          { icon: FiMessageSquare,title: "Voice of Customer (VOC)",  description: "Pain points, frustrations et fonctionnalités souhaitées par les utilisateurs." },
  tendances:    { icon: FiTrendingUp,   title: "Tendances & Risques",      description: "Évolutions marché, technologiques, réglementaires et risques identifiés." },
  strategie:    { icon: FiCompass,      title: "Stratégie — SWOT & PESTEL",description: "Analyse stratégique complète : forces, faiblesses, opportunités, menaces." },
  "mots-cles":  { icon: FiSearch,       title: "Mots-clés",                description: "Mots-clés primaires, marché, VOC, compétiteurs et tendances." },
  raw:          { icon: FiDatabase,     title: "Données brutes",           description: "Réponse JSON complète de l'agent d'analyse de marché." },
};

const marketAgent = AGENTS.find((a) => a.id === "market");

export default function MarketPage() {
  const { idea, token } = usePipeline();
  const location = useLocation();
  const lastAutoStartKeyRef = useRef("");
  const { report, rawReport, xaiSteps, isLoading, error, loadLatest, startMarketAnalysis } =
    useMarketAgent({ idea, token });
  const [activeTab, setActiveTab] = useState("apercu");
  const [showModal, setShowModal] = useState(false);
  const [modalDone, setModalDone] = useState(false);
  const wasLoadingRef = useRef(false);

  useEffect(() => {
    if (!idea?.id || !token) return;

    const state = location.state;
    if (state?.autoStartMarket) {
      const launchKey = `${location.key}:${state?.sourceIdeaId || idea.id}`;
      if (lastAutoStartKeyRef.current === launchKey) return;
      lastAutoStartKeyRef.current = launchKey;
      setShowModal(true);
      setModalDone(false);
      wasLoadingRef.current = false;
      startMarketAnalysis({ mode: "pipeline", clarifiedIdea: state.clarifiedIdea });
    } else {
      loadLatest().catch(() => {});
    }

    return () => {
      // Reset dedup guard on cleanup so a Strict Mode remount (dev) can retry
      // if the stream was aborted during the simulated unmount.
      lastAutoStartKeyRef.current = "";
    };
  }, [idea?.id, token, location.key, location.state, startMarketAnalysis, loadLatest]);

  /* ── Track loading → done to drive modal state ─────────────────────────── */
  useEffect(() => {
    if (isLoading) {
      wasLoadingRef.current = true;
    } else if (wasLoadingRef.current) {
      wasLoadingRef.current = false;
      setModalDone(true);
      // Auto-close after 1.5 s when no error
      if (!error) {
        const t = setTimeout(() => setShowModal(false), 1500);
        return () => clearTimeout(t);
      }
    }
  }, [isLoading, error]);

  const normalizedReport = report?.raw ?? rawReport ?? {};
  const clarifiedIdea = normalizedReport?.clarified_idea ?? {
    short_pitch:          idea?.clarity_short_pitch ?? "",
    problem:              idea?.clarity_problem ?? "",
    sector:               idea?.clarity_sector ?? "",
    country:              idea?.clarity_country ?? "",
    country_code:         idea?.clarity_country_code ?? "",
    target_users:         idea?.clarity_target_users ?? "",
    solution_description: idea?.clarity_solution ?? "",
  };

  const competitorsCount =
    normalizedReport?.competitor?.top_competitors?.length ??
    normalizedReport?.competitor?.competitors?.length ??
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
      onClick={() => canRelaunch && startMarketAnalysis({ mode: "pipeline" })}
      disabled={!canRelaunch}
      className={`rounded-full px-4 py-1.5 text-xs font-bold transition-all ${
        canRelaunch
          ? "bg-gradient-to-br from-brand to-brand-dark text-white shadow-btn hover:shadow-btn-hover hover:-translate-y-px"
          : "cursor-not-allowed bg-brand-light text-brand-muted"
      }`}
    >
      {isLoading ? "En cours…" : "Relancer"}
    </button>
  );

  function renderTabContent() {
    const intro = TAB_INTROS[activeTab];
    const introNode = intro ? (
      <SectionIntro icon={intro.icon} title={intro.title} description={intro.description} />
    ) : null;

    if (activeTab === "raw")          return <>{introNode}<MarketRawDataViewer data={normalizedReport} /></>;
    if (activeTab === "apercu")       return <>{introNode}<MarketApercu market={normalizedReport?.market} /></>;
    if (activeTab === "competiteurs") return (
      <>
        {introNode}
        <MarketCompetitors
          competitors={
            normalizedReport?.competitor?.top_competitors ??
            normalizedReport?.competitor?.competitors ??
            []
          }
        />
      </>
    );
    if (activeTab === "voc")       return <>{introNode}<MarketVOC voc={normalizedReport?.voc} /></>;
    if (activeTab === "tendances") return <>{introNode}<MarketTrendsRisks trends={normalizedReport?.trends} /></>;
    if (activeTab === "strategie") return (
      <>
        {introNode}
        <MarketStrategy strategy={report?.strategy} />
      </>
    );
    if (activeTab === "mots-cles") return <>{introNode}<MarketKeywords keywords={normalizedReport?.keywords} /></>;
    const label = MARKET_TABS.find((t) => t.id === activeTab)?.label ?? "Section";
    return <MarketTabEmpty label={label} />;
  }

  return (
    <>
      <PipelineLaunchModal
        isOpen={showModal}
        isDone={modalDone}
        xaiSteps={xaiSteps}
        error={error}
        onClose={() => setShowModal(false)}
      />

    <div className="app-content-scroll flex flex-1 flex-col gap-3">
      <AgentPageHeader
        agent={marketAgent}
        subtitle="Analyse de marché · Étape 2 sur 6"
        action={relaunchAction}
      />

      <MarketDashboardHeader
        clarified_idea={clarifiedIdea}
        idea_id={normalizedReport?.idea_id ?? rawReport?.idea_id ?? idea?.id}
        competitorsCount={competitorsCount}
      />

      {isLoading && (
        <div className="flex items-center gap-3 rounded-2xl border border-brand-border bg-white px-5 py-4 shadow-card">
          <Loader className="h-5 w-5" />
          <span className="text-sm text-brand-dark">Pipeline en cours…</span>
        </div>
      )}

      {error && <ErrorBanner message={error} />}

      {!isLoading && normalizedReport && (
        <>
          <TabBar tabs={MARKET_TABS} activeId={activeTab} onChange={setActiveTab} />
          <div className="flex flex-col gap-3">
            {renderTabContent()}
          </div>
        </>
      )}
    </div>
    </>
  );
}
