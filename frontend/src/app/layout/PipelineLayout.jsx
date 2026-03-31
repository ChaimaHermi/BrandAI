import { useCallback, useEffect, useState } from "react";
import { useNavigate, useParams, Outlet, useLocation } from "react-router-dom";
import { useAuth } from "@/shared/hooks/useAuth";
import { AGENTS } from "@/agents";
import { CLARITY_SCORE_MIN_PIPELINE } from "@/agents/clarifier/constants";

export default function PipelineLayout() {
  const { id } = useParams();
  const navigate = useNavigate();
  const location = useLocation();
  const { token, user } = useAuth();

  const [idea, setIdea] = useState(null);
  const [sidebarOpen, setSidebarOpen] = useState(true);

  const activeAgent =
    AGENTS.find((a) => location.pathname.includes("/" + a.id)) || AGENTS[0];

  const activeIndex = AGENTS.findIndex((a) => a.id === activeAgent.id);

  const progressPct = Math.round(((activeIndex + 1) / AGENTS.length) * 100);

  const getStatus = (agentId) => {
    const idx = AGENTS.findIndex((a) => a.id === agentId);
    if (idx < activeIndex) return "done";
    if (idx === activeIndex) return "active";
    return "pending";
  };

  const refetchIdea = useCallback(() => {
    if (!id || !token) return;
    fetch(import.meta.env.VITE_API_URL + "/ideas/" + id, {
      headers: { Authorization: "Bearer " + token },
    })
      .then((r) => (r.ok ? r.json() : null))
      .then((data) => {
        if (data) setIdea(data);
      })
      .catch(console.error);
  }, [id, token]);

  useEffect(() => {
    refetchIdea();
  }, [refetchIdea, location.pathname]);

  // Calculer si pipeline est disponible
  const pipelineEnabled =
    idea?.clarity_status === "clarified" &&
    (idea?.clarity_score ?? 0) >= CLARITY_SCORE_MIN_PIPELINE;

  const userInitials = (user?.name || user?.email || "U")
    .slice(0, 2)
    .toUpperCase();

  const ideaTitle = (idea?.description || "Votre projet").slice(0, 26);

  const S = {
    page: {
      display: "flex",
      flexDirection: "column",
      minHeight: "100vh",
      overflowY: "auto",
      fontFamily: "var(--font-sans)",
      background: "linear-gradient(135deg,#f8f7ff 0%,#f0eeff 40%,#faf5ff 100%)",
    },
    topbar: {
      height: 52,
      background: "white",
      borderBottom: "0.5px solid #e8e4ff",
      display: "flex",
      alignItems: "center",
      padding: "0 20px",
      gap: 12,
      flexShrink: 0,
      boxShadow: "0 1px 8px rgba(124,58,237,0.06)",
    },
    logo: {
      width: 28,
      height: 28,
      background: "linear-gradient(135deg,#7F77DD,#534AB7)",
      borderRadius: 8,
      display: "flex",
      alignItems: "center",
      justifyContent: "center",
      boxShadow: "0 2px 8px rgba(124,58,237,0.3)",
    },
    body: {
      flex: 1,
      display: "flex",
    },
    content: {
      flex: 1,
      display: "flex",
      flexDirection: "column",
      minWidth: 0,
      minHeight: 0,
    },
  };

  return (
    <div style={S.page}>
      {/* TOP BAR */}
      <div className="flex h-[52px] shrink-0 items-center gap-3 border-b border-[#e8e4ff] bg-white px-5 shadow-[0_1px_8px_rgba(124,58,237,0.06)]">
        {/* Logo */}
        <div className="mr-1 flex shrink-0 items-center gap-[7px]">
          <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-gradient-to-br from-[#7F77DD] to-[#534AB7] shadow-[0_2px_8px_rgba(124,58,237,0.3)]">
            <svg width="13" height="13" viewBox="0 0 14 14" fill="none">
              <path
                d="M7 1.5l1.2 3 3 .4-2.2 2.1.5 3L7 8.5l-2.5 1.5.5-3L2.8 5l3-.4L7 1.5z"
                stroke="white"
                strokeWidth="1.1"
                strokeLinejoin="round"
              />
            </svg>
          </div>
          <span className="text-sm font-extrabold text-[#1a1040]">
            BrandAI
          </span>
        </div>

        {/* Breadcrumb */}
        <div className="flex flex-1 items-center gap-1.5 overflow-hidden text-xs text-gray-400">
          <span
            onClick={() => navigate("/dashboard")}
            className="shrink-0 cursor-pointer font-semibold text-[#7F77DD]"
          >
            Mes idées
          </span>
          <svg
            width="12"
            height="12"
            viewBox="0 0 12 12"
            fill="none"
            className="shrink-0"
          >
            <path
              d="M4 2l4 4-4 4"
              stroke="#AFA9EC"
              strokeWidth="1.2"
              strokeLinecap="round"
            />
          </svg>
          <span className="overflow-hidden text-ellipsis whitespace-nowrap font-medium text-gray-500">
            {ideaTitle}...
          </span>
          <svg
            width="12"
            height="12"
            viewBox="0 0 12 12"
            fill="none"
            className="shrink-0"
          >
            <path
              d="M4 2l4 4-4 4"
              stroke="#AFA9EC"
              strokeWidth="1.2"
              strokeLinecap="round"
            />
          </svg>
          <div className="flex shrink-0 items-center gap-[5px]">
            <div
              className="flex h-[18px] w-[18px] items-center justify-center rounded-full text-[7px] font-bold text-white"
              style={{ background: activeAgent.gradient }}
            >
              {activeAgent.short}
            </div>
            <span className="text-xs font-bold text-[#3C3489]">
              {activeAgent.label}
            </span>
          </div>
        </div>

        {/* Progress pill */}
        <div className="flex shrink-0 items-center gap-2 rounded-full bg-[#f0eeff] px-3 py-[5px]">
          <div className="h-1 w-[50px] overflow-hidden rounded-full bg-white">
            <div
              style={{
                height: "100%",
                width: progressPct + "%",
                transition: "width 0.5s ease",
              }}
              className="rounded-full bg-gradient-to-r from-[#7F77DD] to-[#534AB7]"
            />
          </div>
          <span className="text-[10px] font-bold text-[#534AB7]">
            {activeIndex + 1}/{AGENTS.length}
          </span>
        </div>

        {/* Hamburger */}
        <button
          onClick={() => setSidebarOpen((v) => !v)}
          className={`flex h-[34px] w-[34px] shrink-0 cursor-pointer flex-col items-center justify-center gap-1 rounded-lg border border-[#e8e4ff] transition-all ${sidebarOpen ? "bg-[#f0eeff]" : "bg-white"}`}
        >
          {sidebarOpen ? (
            <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
              <path
                d="M3 3l8 8M11 3l-8 8"
                stroke="#7F77DD"
                strokeWidth="1.5"
                strokeLinecap="round"
              />
            </svg>
          ) : (
            <div className="flex flex-col items-center gap-1">
              <div className="h-[1.5px] w-[14px] rounded-full bg-[#7F77DD]" />
              <div className="h-[1.5px] w-[14px] rounded-full bg-[#7F77DD]" />
              <div className="h-[1.5px] w-[10px] rounded-full bg-[#7F77DD]" />
            </div>
          )}
        </button>

        {/* Avatar */}
        <div className="flex h-8 w-8 shrink-0 cursor-pointer items-center justify-center rounded-full bg-gradient-to-br from-[#7F77DD] to-[#534AB7] text-[10px] font-bold text-white shadow-[0_2px_6px_rgba(124,58,237,0.25)]">
          {userInitials}
        </div>
      </div>

      {/* BODY */}
      <div style={S.body}>
        {/* SIDEBAR */}
        <div
          className={`flex shrink-0 flex-col overflow-hidden border-r border-[#f0eeff] bg-white transition-[width,min-width] duration-200 ease-in-out ${sidebarOpen ? "w-56 min-w-56 shadow-[2px_0_16px_rgba(124,58,237,0.06)]" : "w-0 min-w-0 shadow-none"}`}
        >
          <div className="min-w-56 border-b border-[#f0eeff] px-[14px] pb-[10px] pt-[14px]">
            <button
              onClick={() => navigate("/dashboard")}
              className="mb-3 flex cursor-pointer items-center gap-[5px] whitespace-nowrap border-0 bg-transparent p-0 font-[var(--font-sans)] text-xs font-medium text-gray-400"
            >
              <svg width="13" height="13" viewBox="0 0 14 14" fill="none">
                <path
                  d="M9 2L4 7l5 5"
                  stroke="#9ca3af"
                  strokeWidth="1.4"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />
              </svg>
              Retour
            </button>

            <div className="mb-0.5 overflow-hidden text-ellipsis whitespace-nowrap text-[13px] font-bold text-[#1a1040]">
              {ideaTitle}...
            </div>
            <div className="mb-[10px] text-[11px] text-gray-400">
              Étape {activeIndex + 1} · {activeAgent.label}
            </div>

            <div className="h-[5px] overflow-hidden rounded-full bg-[#f0eeff]">
              <div
                style={{
                  height: "100%",
                  width: progressPct + "%",
                  transition: "width 0.5s ease",
                }}
                className="rounded-full bg-gradient-to-r from-[#7F77DD] to-[#534AB7]"
              />
            </div>
          </div>

          {/* Agents */}
          <div className="flex min-w-56 flex-1 flex-col gap-[3px] overflow-y-auto p-2">
            {AGENTS.map((agent) => {
              const status = getStatus(agent.id);
              const isActive = agent.id === activeAgent.id;
              const isDone = status === "done";
              const isPending = status === "pending";

              return (
                <div
                  key={agent.id}
                  onClick={() => navigate("/ideas/" + id + "/" + agent.id)}
                  className={`flex cursor-pointer items-center gap-[10px] rounded-[10px] px-[10px] py-[9px] transition-all duration-150 ${
                    isDone
                      ? "border"
                      : isActive
                        ? "border border-[#AFA9EC] bg-gradient-to-br from-[#f0eeff] to-[#fafafe]"
                        : "border border-transparent bg-transparent"
                  } ${isPending ? "opacity-45" : "opacity-100"}`}
                  style={isDone ? { background: agent.doneBg, borderColor: agent.doneBorder } : undefined}
                >
                  <div
                    className={`flex h-7 w-7 shrink-0 items-center justify-center rounded-full transition-all duration-150 ${isPending ? "border border-[#e5e7eb]" : "border-0"} ${isDone ? "bg-[#1D9E75]" : isActive ? "" : "bg-[#f5f5f5]"}`}
                    style={{
                      background: isDone ? "#1D9E75" : isActive ? agent.gradient : "#f5f5f5",
                      boxShadow: isActive ? `0 2px 8px ${agent.color}44` : "none",
                    }}
                  >
                    {isDone ? (
                      <svg
                        width="11"
                        height="11"
                        viewBox="0 0 12 12"
                        fill="none"
                      >
                        <path
                          d="M1.5 6l3 3 6-6"
                          stroke="white"
                          strokeWidth="1.6"
                          strokeLinecap="round"
                          strokeLinejoin="round"
                        />
                      </svg>
                    ) : (
                      <span
                        className={`text-[9px] font-bold ${isActive ? "text-white" : "text-gray-400"}`}
                      >
                        {agent.short}
                      </span>
                    )}
                  </div>

                  <div className="min-w-0 flex-1">
                    <div
                      className={`overflow-hidden text-ellipsis whitespace-nowrap text-[11px] ${isDone || isActive ? "font-bold" : "font-medium"} ${isActive ? "text-[#3C3489]" : "text-gray-500"}`}
                      style={isDone ? { color: agent.doneColor } : undefined}
                    >
                      {agent.label}
                    </div>
                    <div className={`mt-0.5 flex items-center gap-[3px] text-[9px] ${isDone ? "text-[#1D9E75]" : isActive ? "text-[#7F77DD]" : "text-gray-400"}`}>
                      {isActive && (
                        <span className="inline-block animate-[pulse_1.2s_infinite]">
                          ●
                        </span>
                      )}
                      {isDone
                        ? "Terminé ✓"
                        : isActive
                          ? "En cours"
                          : "En attente"}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>

          {/* Pipeline button */}
          <div className="min-w-56 border-t border-[#f0eeff] p-3">
            <button
              onClick={() => {
                if (pipelineEnabled) {
                  navigate(`/ideas/${id}/market`, {
                    state: {
                      autoStartMarket: true,
                      clarifiedIdea: {
                        short_pitch: idea?.clarity_short_pitch || idea?.name || "",
                        solution_description: idea?.clarity_solution || idea?.description || "",
                        target_users: idea?.clarity_target_users || idea?.target_audience || "",
                        problem: idea?.clarity_problem || idea?.description || "",
                        sector: idea?.clarity_sector || idea?.sector || "",
                        country_code: idea?.clarity_country_code || "TN",
                        language: idea?.clarity_language || "fr",
                      },
                    },
                  });
                }
              }}
              disabled={!pipelineEnabled}
              className={`flex w-full items-center justify-center gap-1.5 whitespace-nowrap rounded-full px-[10px] py-2.5 text-xs font-bold transition-all duration-200 ${pipelineEnabled ? "cursor-pointer bg-gradient-to-br from-[#7F77DD] to-[#534AB7] text-white shadow-[0_2px_10px_rgba(124,58,237,0.25)] opacity-100" : "cursor-not-allowed border border-[#e8e4ff] bg-[#f3f0ff] text-[#AFA9EC] opacity-60"}`}
            >
              {pipelineEnabled ? (
                <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
                  <path
                    d="M2 6h8M7 3l3 3-3 3"
                    stroke="white"
                    strokeWidth="1.5"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  />
                </svg>
              ) : (
                <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
                  <rect
                    x="2"
                    y="5"
                    width="8"
                    height="6"
                    rx="1"
                    stroke="#AFA9EC"
                    strokeWidth="1.2"
                  />
                  <path
                    d="M4 5V3.5a2 2 0 014 0V5"
                    stroke="#AFA9EC"
                    strokeWidth="1.2"
                    strokeLinecap="round"
                  />
                </svg>
              )}
              {pipelineEnabled ? "Lancer le pipeline" : "Pipeline verrouillé"}
            </button>
            <div className="mt-1.5 text-center text-[10px] text-[#AFA9EC]">
              {idea?.clarity_status === "refused"
                ? "Idée refusée — non conforme"
                : idea?.clarity_status === "clarified" &&
                    (idea?.clarity_score ?? 0) < CLARITY_SCORE_MIN_PIPELINE
                  ? `Score insuffisant (${idea.clarity_score}/100 < ${CLARITY_SCORE_MIN_PIPELINE})`
                  : idea?.clarity_status === "questions"
                    ? "Répondez aux questions d'abord"
                    : "Disponible après clarification"}
            </div>
          </div>
        </div>

        {/* CONTENU */}
        <div style={S.content}>
          <Outlet context={{ idea, setIdea, token, refetchIdea }} />
        </div>
      </div>
    </div>
  );
}
