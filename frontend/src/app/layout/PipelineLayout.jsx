import { useCallback, useEffect, useState } from "react";
import { useNavigate, useParams, Outlet, useLocation } from "react-router-dom";
import { useAuth } from "@/shared/hooks/useAuth";

const AGENTS = [
  {
    id: "clarifier",
    label: "Idea Clarifier",
    short: "IC",
    color: "#7F77DD",
    gradient: "linear-gradient(135deg,#7F77DD,#534AB7)",
    doneBg: "#f0fdf4",
    doneBorder: "#9FE1CB",
    doneColor: "#085041",
  },
  {
    id: "enhancer",
    label: "Idea Enhancer",
    short: "IE",
    color: "#1D9E75",
    gradient: "linear-gradient(135deg,#1D9E75,#085041)",
    doneBg: "#f0fdf4",
    doneBorder: "#9FE1CB",
    doneColor: "#085041",
  },
  {
    id: "market",
    label: "Market Analysis",
    short: "MA",
    color: "#378ADD",
    gradient: "linear-gradient(135deg,#378ADD,#185FA5)",
    doneBg: "#EBF5FF",
    doneBorder: "#B5D4F4",
    doneColor: "#0C447C",
  },
  {
    id: "brand",
    label: "Brand Identity",
    short: "BI",
    color: "#D4537E",
    gradient: "linear-gradient(135deg,#D4537E,#72243E)",
    doneBg: "#FBEAF0",
    doneBorder: "#F4C0D1",
    doneColor: "#72243E",
  },
  {
    id: "content",
    label: "Content Creator",
    short: "CC",
    color: "#D85A30",
    gradient: "linear-gradient(135deg,#D85A30,#712B13)",
    doneBg: "#FAECE7",
    doneBorder: "#F5C4B3",
    doneColor: "#712B13",
  },
  {
    id: "website",
    label: "Website Builder",
    short: "WB",
    color: "#185FA5",
    gradient: "linear-gradient(135deg,#185FA5,#042C53)",
    doneBg: "#EBF5FF",
    doneBorder: "#B5D4F4",
    doneColor: "#0C447C",
  },
  {
    id: "optimizer",
    label: "Optimizer",
    short: "OP",
    color: "#854F0B",
    gradient: "linear-gradient(135deg,#854F0B,#412402)",
    doneBg: "#FAEEDA",
    doneBorder: "#FAC775",
    doneColor: "#633806",
  },
];

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
    idea?.clarity_status === "clarified" && (idea?.clarity_score ?? 0) >= 80;

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
    sidebar: {
      width: sidebarOpen ? 224 : 0,
      minWidth: sidebarOpen ? 224 : 0,
      overflow: "hidden",
      background: "white",
      borderRight: "0.5px solid #f0eeff",
      display: "flex",
      flexDirection: "column",
      transition: "width 0.25s ease, min-width 0.25s ease",
      boxShadow: sidebarOpen ? "2px 0 16px rgba(124,58,237,0.06)" : "none",
      flexShrink: 0,
    },
    sidebarHeader: {
      padding: "14px 14px 10px",
      borderBottom: "0.5px solid #f0eeff",
      minWidth: 224,
    },
    agentList: {
      flex: 1,
      overflowY: "auto",
      padding: 8,
      display: "flex",
      flexDirection: "column",
      gap: 3,
      minWidth: 224,
    },
    pipelineBtn: {
      padding: "12px",
      borderTop: "0.5px solid #f0eeff",
      minWidth: 224,
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
      <div style={S.topbar}>
        {/* Logo */}
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: 7,
            marginRight: 4,
            flexShrink: 0,
          }}
        >
          <div style={S.logo}>
            <svg width="13" height="13" viewBox="0 0 14 14" fill="none">
              <path
                d="M7 1.5l1.2 3 3 .4-2.2 2.1.5 3L7 8.5l-2.5 1.5.5-3L2.8 5l3-.4L7 1.5z"
                stroke="white"
                strokeWidth="1.1"
                strokeLinejoin="round"
              />
            </svg>
          </div>
          <span
            style={{
              fontSize: 14,
              fontWeight: 800,
              color: "#1a1040",
            }}
          >
            BrandAI
          </span>
        </div>

        {/* Breadcrumb */}
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: 6,
            fontSize: 12,
            color: "#9ca3af",
            flex: 1,
            overflow: "hidden",
          }}
        >
          <span
            onClick={() => navigate("/dashboard")}
            style={{
              color: "#7F77DD",
              fontWeight: 600,
              cursor: "pointer",
              flexShrink: 0,
            }}
          >
            Mes idées
          </span>
          <svg
            width="12"
            height="12"
            viewBox="0 0 12 12"
            fill="none"
            style={{ flexShrink: 0 }}
          >
            <path
              d="M4 2l4 4-4 4"
              stroke="#AFA9EC"
              strokeWidth="1.2"
              strokeLinecap="round"
            />
          </svg>
          <span
            style={{
              overflow: "hidden",
              textOverflow: "ellipsis",
              whiteSpace: "nowrap",
              color: "#6b7280",
              fontWeight: 500,
            }}
          >
            {ideaTitle}...
          </span>
          <svg
            width="12"
            height="12"
            viewBox="0 0 12 12"
            fill="none"
            style={{ flexShrink: 0 }}
          >
            <path
              d="M4 2l4 4-4 4"
              stroke="#AFA9EC"
              strokeWidth="1.2"
              strokeLinecap="round"
            />
          </svg>
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: 5,
              flexShrink: 0,
            }}
          >
            <div
              style={{
                width: 18,
                height: 18,
                borderRadius: "50%",
                background: activeAgent.gradient,
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                fontSize: 7,
                fontWeight: 700,
                color: "white",
              }}
            >
              {activeAgent.short}
            </div>
            <span
              style={{
                color: "#3C3489",
                fontWeight: 700,
                fontSize: 12,
              }}
            >
              {activeAgent.label}
            </span>
          </div>
        </div>

        {/* Progress pill */}
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: 8,
            background: "#f0eeff",
            borderRadius: 99,
            padding: "5px 12px",
            flexShrink: 0,
          }}
        >
          <div
            style={{
              width: 50,
              height: 4,
              borderRadius: 99,
              background: "white",
              overflow: "hidden",
            }}
          >
            <div
              style={{
                height: "100%",
                width: progressPct + "%",
                background: "linear-gradient(90deg,#7F77DD,#534AB7)",
                borderRadius: 99,
                transition: "width 0.5s ease",
              }}
            />
          </div>
          <span
            style={{
              fontSize: 10,
              fontWeight: 700,
              color: "#534AB7",
            }}
          >
            {activeIndex + 1}/7
          </span>
        </div>

        {/* Hamburger */}
        <button
          onClick={() => setSidebarOpen((v) => !v)}
          style={{
            width: 34,
            height: 34,
            borderRadius: 8,
            background: sidebarOpen ? "#f0eeff" : "white",
            border: "0.5px solid #e8e4ff",
            cursor: "pointer",
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            justifyContent: "center",
            gap: 4,
            flexShrink: 0,
            transition: "all 0.2s",
          }}
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
            <div
              style={{
                display: "flex",
                flexDirection: "column",
                gap: 4,
                alignItems: "center",
              }}
            >
              <div
                style={{
                  width: 14,
                  height: 1.5,
                  background: "#7F77DD",
                  borderRadius: 99,
                }}
              />
              <div
                style={{
                  width: 14,
                  height: 1.5,
                  background: "#7F77DD",
                  borderRadius: 99,
                }}
              />
              <div
                style={{
                  width: 10,
                  height: 1.5,
                  background: "#7F77DD",
                  borderRadius: 99,
                }}
              />
            </div>
          )}
        </button>

        {/* Avatar */}
        <div
          style={{
            width: 32,
            height: 32,
            borderRadius: "50%",
            background: "linear-gradient(135deg,#7F77DD,#534AB7)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            fontSize: 10,
            fontWeight: 700,
            color: "white",
            flexShrink: 0,
            boxShadow: "0 2px 6px rgba(124,58,237,0.25)",
            cursor: "pointer",
          }}
        >
          {userInitials}
        </div>
      </div>

      {/* BODY */}
      <div style={S.body}>
        {/* SIDEBAR */}
        <div style={S.sidebar}>
          <div style={S.sidebarHeader}>
            <button
              onClick={() => navigate("/dashboard")}
              style={{
                display: "flex",
                alignItems: "center",
                gap: 5,
                background: "none",
                border: "none",
                cursor: "pointer",
                color: "#9ca3af",
                fontSize: 12,
                padding: 0,
                marginBottom: 12,
                fontWeight: 500,
                fontFamily: "var(--font-sans)",
                whiteSpace: "nowrap",
              }}
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

            <div
              style={{
                fontSize: 13,
                fontWeight: 700,
                color: "#1a1040",
                marginBottom: 2,
                overflow: "hidden",
                textOverflow: "ellipsis",
                whiteSpace: "nowrap",
              }}
            >
              {ideaTitle}...
            </div>
            <div
              style={{
                fontSize: 11,
                color: "#9ca3af",
                marginBottom: 10,
              }}
            >
              Étape {activeIndex + 1} · {activeAgent.label}
            </div>

            <div
              style={{
                height: 5,
                borderRadius: 99,
                background: "#f0eeff",
                overflow: "hidden",
              }}
            >
              <div
                style={{
                  height: "100%",
                  width: progressPct + "%",
                  background: "linear-gradient(90deg,#7F77DD,#534AB7)",
                  borderRadius: 99,
                  transition: "width 0.5s ease",
                }}
              />
            </div>
          </div>

          {/* Agents */}
          <div style={S.agentList}>
            {AGENTS.map((agent) => {
              const status = getStatus(agent.id);
              const isActive = agent.id === activeAgent.id;
              const isDone = status === "done";
              const isPending = status === "pending";

              return (
                <div
                  key={agent.id}
                  onClick={() => navigate("/ideas/" + id + "/" + agent.id)}
                  style={{
                    display: "flex",
                    alignItems: "center",
                    gap: 10,
                    padding: "9px 10px",
                    borderRadius: 10,
                    cursor: "pointer",
                    background: isDone
                      ? agent.doneBg
                      : isActive
                        ? "linear-gradient(135deg,#f0eeff,#fafafe)"
                        : "transparent",
                    border: isDone
                      ? "0.5px solid " + agent.doneBorder
                      : isActive
                        ? "0.5px solid #AFA9EC"
                        : "0.5px solid transparent",
                    opacity: isPending ? 0.45 : 1,
                    transition: "all 0.15s",
                  }}
                >
                  <div
                    style={{
                      width: 28,
                      height: 28,
                      borderRadius: "50%",
                      background: isDone
                        ? "#1D9E75"
                        : isActive
                          ? agent.gradient
                          : "#f5f5f5",
                      border: isPending ? "0.5px solid #e5e7eb" : "none",
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "center",
                      flexShrink: 0,
                      boxShadow: isActive
                        ? "0 2px 8px " + agent.color + "44"
                        : "none",
                      transition: "all 0.15s",
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
                        style={{
                          fontSize: 9,
                          fontWeight: 700,
                          color: isActive ? "white" : "#9ca3af",
                        }}
                      >
                        {agent.short}
                      </span>
                    )}
                  </div>

                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div
                      style={{
                        fontSize: 11,
                        fontWeight: isDone || isActive ? 700 : 500,
                        color: isDone
                          ? agent.doneColor
                          : isActive
                            ? "#3C3489"
                            : "#6b7280",
                        overflow: "hidden",
                        textOverflow: "ellipsis",
                        whiteSpace: "nowrap",
                      }}
                    >
                      {agent.label}
                    </div>
                    <div
                      style={{
                        fontSize: 9,
                        color: isDone
                          ? "#1D9E75"
                          : isActive
                            ? "#7F77DD"
                            : "#9ca3af",
                        marginTop: 2,
                        display: "flex",
                        alignItems: "center",
                        gap: 3,
                      }}
                    >
                      {isActive && (
                        <span
                          style={{
                            animation: "pulse 1.2s infinite",
                            display: "inline-block",
                          }}
                        >
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
          <div style={S.pipelineBtn}>
            <button
              onClick={() => {
                if (pipelineEnabled) {
                  navigate(`/ideas/${id}/enhancer`);
                }
              }}
              disabled={!pipelineEnabled}
              style={{
                width: "100%",
                padding: "10px",
                background: pipelineEnabled
                  ? "linear-gradient(135deg,#7F77DD,#534AB7)"
                  : "#f3f0ff",
                color: pipelineEnabled ? "white" : "#AFA9EC",
                border: pipelineEnabled ? "none" : "0.5px solid #e8e4ff",
                borderRadius: 99,
                fontSize: 12,
                fontWeight: 700,
                cursor: pipelineEnabled ? "pointer" : "not-allowed",
                boxShadow: pipelineEnabled
                  ? "0 2px 10px rgba(124,58,237,0.25)"
                  : "none",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                gap: 6,
                transition: "all 0.2s",
                whiteSpace: "nowrap",
                opacity: pipelineEnabled ? 1 : 0.6,
              }}
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
            <div
              style={{
                fontSize: 10,
                color: "#AFA9EC",
                textAlign: "center",
                marginTop: 6,
              }}
            >
              {idea?.clarity_status === "refused"
                ? "Idée refusée — non conforme"
                : idea?.clarity_status === "clarified" &&
                    (idea?.clarity_score ?? 0) < 80
                  ? `Score insuffisant (${idea.clarity_score}/100 < 80)`
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
