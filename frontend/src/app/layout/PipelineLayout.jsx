import { useEffect, useState } from "react";
import { useNavigate, useParams, Outlet, useLocation } from "react-router-dom";
import { useAuth } from "@/shared/hooks/useAuth";

const AGENTS = [
  {
    id: "clarifier",
    label: "Idea Clarifier",
    short: "IC",
    color: "#7F77DD",
    gradient: "linear-gradient(135deg,#7F77DD,#534AB7)",
  },
  {
    id: "enhancer",
    label: "Idea Enhancer",
    short: "IE",
    color: "#1D9E75",
    gradient: "linear-gradient(135deg,#1D9E75,#085041)",
  },
  {
    id: "market",
    label: "Market Analysis",
    short: "MA",
    color: "#378ADD",
    gradient: "linear-gradient(135deg,#378ADD,#185FA5)",
  },
  {
    id: "brand",
    label: "Brand Identity",
    short: "BI",
    color: "#D4537E",
    gradient: "linear-gradient(135deg,#D4537E,#72243E)",
  },
  {
    id: "content",
    label: "Content Creator",
    short: "CC",
    color: "#D85A30",
    gradient: "linear-gradient(135deg,#D85A30,#712B13)",
  },
  {
    id: "website",
    label: "Website Builder",
    short: "WB",
    color: "#185FA5",
    gradient: "linear-gradient(135deg,#185FA5,#042C53)",
  },
  {
    id: "optimizer",
    label: "Optimizer",
    short: "OP",
    color: "#854F0B",
    gradient: "linear-gradient(135deg,#854F0B,#412402)",
  },
];

export default function PipelineLayout() {
  const { id } = useParams();
  const navigate = useNavigate();
  const location = useLocation();
  const { token } = useAuth();
  const [idea, setIdea] = useState(null);
  const [sidebarOpen, setSidebarOpen] = useState(true);

  const activeAgent =
    AGENTS.find((a) => location.pathname.includes(`/${a.id}`)) || AGENTS[0];

  const activeIndex = AGENTS.findIndex((a) => a.id === activeAgent.id);
  const progressPct = Math.round(((activeIndex + 1) / AGENTS.length) * 100);

  useEffect(() => {
    if (!id || !token) return;
    const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000/api";
    fetch(`${API_URL}/ideas/${id}`, {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then((r) => (r.ok ? r.json() : null))
      .then((data) => {
        if (data) setIdea(data);
      })
      .catch(() => {});
  }, [id, token]);

  const getStatus = (agentId) => {
    const idx = AGENTS.findIndex((a) => a.id === agentId);
    if (idx < activeIndex) return "done";
    if (idx === activeIndex) return "active";
    return "pending";
  };

  const ideaTitle =
    (idea?.description && idea.description.slice(0, 32)) || "Votre projet";

  return (
    <div
      style={{
        display: "flex",
        height: "100vh",
        background: "var(--page-bg, #f8f7ff)",
        fontFamily: "var(--font-sans)",
        overflow: "hidden",
      }}
    >
      {/* Sidebar */}
      <div
        style={{
          width: sidebarOpen ? 224 : 0,
          minWidth: sidebarOpen ? 224 : 0,
          overflow: "hidden",
          background: "#ffffff",
          borderRight: "0.5px solid #e8e4ff",
          display: "flex",
          flexDirection: "column",
          transition: "width 0.25s ease, min-width 0.25s ease",
          boxShadow: sidebarOpen
            ? "2px 0 16px rgba(124,58,237,0.06)"
            : "none",
        }}
      >
        <div
          style={{
            padding: "16px 14px 12px",
            borderBottom: "0.5px solid #f0eeff",
          }}
        >
          <button
            type="button"
            onClick={() => navigate("/dashboard")}
            style={{
              display: "flex",
              alignItems: "center",
              gap: 6,
              background: "none",
              border: "none",
              cursor: "pointer",
              color: "#9ca3af",
              fontSize: 12,
              padding: 0,
              marginBottom: 12,
            }}
          >
            <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
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
            Étape {activeIndex + 1} / {AGENTS.length}
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
                width: `${progressPct}%`,
                background: "linear-gradient(90deg,#7F77DD,#534AB7)",
                borderRadius: 99,
                transition: "width 0.5s ease",
              }}
            />
          </div>
        </div>

        <div
          style={{
            flex: 1,
            overflowY: "auto",
            padding: 8,
            display: "flex",
            flexDirection: "column",
            gap: 2,
          }}
        >
          {AGENTS.map((agent) => {
            const status = getStatus(agent.id);
            const isActive = agent.id === activeAgent.id;
            const isDone = status === "done";
            const isPending = status === "pending";

            return (
              <div
                key={agent.id}
                onClick={() => navigate(`/ideas/${id}/${agent.id}`)}
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: 10,
                  padding: "8px 10px",
                  borderRadius: 10,
                  cursor: "pointer",
                  background: isDone
                    ? "#f0fdf4"
                    : isActive
                    ? "linear-gradient(135deg,#f0eeff,#fafafe)"
                    : "transparent",
                  border: isActive
                    ? "0.5px solid #AFA9EC"
                    : isDone
                    ? "0.5px solid #9FE1CB"
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
                      ? `0 2px 8px ${agent.color}44`
                      : "none",
                  }}
                >
                  {isDone ? (
                    <svg width="11" height="11" viewBox="0 0 11 11" fill="none">
                      <path
                        d="M1.5 5.5l3 3 5-5"
                        stroke="white"
                        strokeWidth="1.5"
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
                      fontWeight: isActive ? 700 : 500,
                      color: isDone
                        ? "#085041"
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
                      marginTop: 1,
                      display: "flex",
                      alignItems: "center",
                      gap: 3,
                    }}
                  >
                    {isActive && (
                      <span style={{ animation: "pulse 1.2s infinite" }}>
                        ●
                      </span>
                    )}
                    {isDone ? "Terminé ✓" : isActive ? "En cours" : "En attente"}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Main */}
      <div
        style={{
          flex: 1,
          display: "flex",
          flexDirection: "column",
          overflow: "hidden",
          minWidth: 0,
        }}
      >
        <div
          style={{
            height: 52,
            background: "#ffffff",
            borderBottom: "0.5px solid #e8e4ff",
            display: "flex",
            alignItems: "center",
            padding: "0 16px",
            gap: 12,
            flexShrink: 0,
            boxShadow: "0 1px 8px rgba(124,58,237,0.05)",
          }}
        >
          <button
            type="button"
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
              <>
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
                    alignSelf: "flex-start",
                  }}
                />
              </>
            )}
          </button>

          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: 10,
              flex: 1,
            }}
          >
            <div
              style={{
                width: 32,
                height: 32,
                borderRadius: "50%",
                background: activeAgent.gradient,
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                boxShadow: `0 2px 8px ${activeAgent.color}44`,
              }}
            >
              <span
                style={{
                  fontSize: 9,
                  fontWeight: 700,
                  color: "white",
                }}
              >
                {activeAgent.short}
              </span>
            </div>
            <div>
              <div
                style={{
                  fontSize: 13,
                  fontWeight: 700,
                  color: "#1a1040",
                  lineHeight: 1.2,
                }}
              >
                {activeAgent.label}
              </div>
              <div
                style={{
                  fontSize: 10,
                  color: "#9ca3af",
                }}
              >
                Étape {activeIndex + 1} sur {AGENTS.length}
              </div>
            </div>
          </div>

          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: 8,
              background: "#f0eeff",
              borderRadius: 99,
              padding: "5px 12px",
            }}
          >
            <div
              style={{
                width: 48,
                height: 4,
                borderRadius: 99,
                background: "white",
                overflow: "hidden",
              }}
            >
              <div
                style={{
                  height: "100%",
                  width: `${progressPct}%`,
                  background: "linear-gradient(90deg,#7F77DD,#534AB7)",
                  borderRadius: 99,
                }}
              />
            </div>
            <span
              style={{
                fontSize: 10,
                fontWeight: 600,
                color: "#534AB7",
              }}
            >
              {progressPct}%
            </span>
          </div>
        </div>

        <div
          style={{
            flex: 1,
            overflowY: "auto",
            padding: "16px 20px",
            background: "#f8f7ff",
          }}
        >
          <Outlet context={{ idea, token }} />
        </div>
      </div>
    </div>
  );
}

