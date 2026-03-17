import React, { useState, useEffect, useMemo } from "react";
import { Link, useNavigate } from "react-router-dom";
import {
  HiOutlineClipboardDocumentList,
  HiOutlineArrowPath,
  HiOutlineCheckCircle,
  HiOutlinePlus,
} from "react-icons/hi2";
import { Navbar } from "@/components/layout/Navbar";
import { Card } from "@/shared/ui/Card";
import { Button } from "@/shared/ui/Button";
import {
  IdeasTable,
  IdeasTableSkeleton,
  IdeasFilters,
  Pagination,
} from "@/components/dashboard";
import {
  apiGetIdeas,
  apiDeleteIdea,
  getErrorMessage,
} from "@/services/ideaApi";
import { toast } from "react-toastify";
import { useAuth } from "@/shared/hooks/useAuth";

const IDEAS_PER_PAGE = 4;

export default function DashboardPage() {
  const { token } = useAuth();
  const [ideas, setIdeas] = useState([]);
  const [totalFromApi, setTotalFromApi] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [currentPage, setCurrentPage] = useState(1);
  const navigate = useNavigate();

  useEffect(() => {
    if (!token) return;
    let cancelled = false;
    (async () => {
      try {
        const data = await apiGetIdeas(token);
        if (!cancelled) {
          setIdeas(data.ideas || []);
          setTotalFromApi(data.total ?? (data.ideas || []).length);
          setError("");
        }
      } catch (err) {
        if (!cancelled) setError(getErrorMessage(err));
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => { cancelled = true; };
  }, [token]);

  const filteredIdeas = useMemo(() => {
    let list = [...ideas];
    const q = search.trim().toLowerCase();
    if (q) {
      list = list.filter(
        (i) =>
          (i.name || "").toLowerCase().includes(q) ||
          (i.sector || "").toLowerCase().includes(q),
      );
    }
    if (statusFilter) {
      list = list.filter((i) => i.status === statusFilter);
    }
    return list;
  }, [ideas, search, statusFilter]);

  const totalPages = Math.max(1, Math.ceil(filteredIdeas.length / IDEAS_PER_PAGE));
  const pageIdeas = useMemo(() => {
    const start = (currentPage - 1) * IDEAS_PER_PAGE;
    return filteredIdeas.slice(start, start + IDEAS_PER_PAGE);
  }, [filteredIdeas, currentPage]);

  useEffect(() => {
    if (currentPage > totalPages) setCurrentPage(1);
  }, [currentPage, totalPages]);

  const handleDeleteIdea = async (ideaId) => {
    if (!token) return;
    try {
      await apiDeleteIdea(ideaId, token);
      setIdeas((prev) => prev.filter((i) => i.id !== ideaId));
      setTotalFromApi((prev) => Math.max(0, prev - 1));
      toast.success("Idée supprimée avec succès.");
    } catch (err) {
      setError(getErrorMessage(err));
      toast.error("Impossible de supprimer l'idée. Réessayez.");
    }
  };

  const totalCount = totalFromApi || ideas.length;
  const runningCount = ideas.filter((i) => i.status === "running").length;
  const doneCount = ideas.filter((i) => i.status === "done").length;

  const getSectorStyle = (sector) => {
    const map = {
      tech: {
        bg: "#E6F1FB",
        color: "#185FA5",
        avatarBg: "linear-gradient(135deg,#E6F1FB,#B5D4F4)",
      },
      education: {
        bg: "#f0eeff",
        color: "#534AB7",
        avatarBg: "linear-gradient(135deg,#EEEDFE,#CECBF6)",
      },
      ecommerce: {
        bg: "#E1F5EE",
        color: "#0F6E56",
        avatarBg: "linear-gradient(135deg,#E1F5EE,#9FE1CB)",
      },
      sante: {
        bg: "#FBEAF0",
        color: "#993556",
        avatarBg: "linear-gradient(135deg,#FBEAF0,#F4C0D1)",
      },
      finance: {
        bg: "#FBEAF0",
        color: "#993556",
        avatarBg: "linear-gradient(135deg,#FBEAF0,#F4C0D1)",
      },
    };
    const key = sector?.toLowerCase();
    return (
      map[key] || {
        bg: "#f0eeff",
        color: "#534AB7",
        avatarBg: "linear-gradient(135deg,#EEEDFE,#CECBF6)",
      }
    );
  };

  const getInitials = (idea) => {
    const text = idea.name || idea.description || "?";
    return text.trim().slice(0, 2).toUpperCase();
  };

  const getDisplayName = (idea) => {
    if (idea.name && idea.name.trim() !== "") return idea.name;
    const desc = idea.description || "";
    return desc.length > 45 ? `${desc.slice(0, 45)}...` : desc || "Idée sans nom";
  };

  const clamp = (n, min, max) => Math.max(min, Math.min(max, n));

  // Pour le moment, on calcule la progression "clarifier" en % depuis
  // `idea.pipeline_progress.clarifier_steps` (même si l'idée est encore "pending").
  const getClarifierProgressFromSteps = (idea) => {
    const steps = idea?.pipeline_progress?.clarifier_steps;
    if (!Array.isArray(steps) || steps.length <= 0) return 0;

    // UI actuelle: "1/7" => 14%. On ramène donc 7 steps => 14%.
    const clarifierTotalSteps = 7;
    const clarifierMaxPct = 14;

    const pct = Math.round((steps.length / clarifierTotalSteps) * clarifierMaxPct);
    return clamp(pct, 0, clarifierMaxPct);
  };

  const getProgress = (idea) => {
    const statusMap = {
      clarifier_done: 14,
      enhancer_done: 28,
      market_done: 42,
      brand_done: 57,
      content_done: 71,
      website_done: 85,
      done: 100,
    };

    // Si l’idée est encore en cours de clarification,
    // on affiche le % depuis le pipeline sauvegardé.
    if (idea?.status === "pending" || idea?.status === "in_progress") {
      const clarifierPct = getClarifierProgressFromSteps(idea);
      return clarifierPct;
    }

    return statusMap[idea?.status] || 0;
  };

  const getStatusLabel = (idea) => {
    const progress = getProgress(idea);
    const map = {
      pending: {
        label: `En attente · ${progress}%`,
        color: "#9ca3af",
      },
      in_progress: {
        label: `Clarifier en cours · ${progress}%`,
        color: "#7F77DD",
      },
      clarifier_done: {
        label: `Clarifier ✓ · ${progress}%`,
        color: "#7F77DD",
      },
      enhancer_done: {
        label: `Enhancer ✓ · ${progress}%`,
        color: "#1D9E75",
      },
      done: {
        label: `Pipeline complet ✓ · ${progress}%`,
        color: "#1D9E75",
      },
    };
    return map[idea?.status] || { label: `En attente · ${progress}%`, color: "#9ca3af" };
  };

  const handlePageChange = (page) => {
    if (page < 1 || page > totalPages) return;
    setCurrentPage(page);
  };

  const total = totalFromApi || ideas.length;

  return (
    <>
      <Navbar variant="app" />
      <div
        className="pt-20 px-6"
        style={{
          background:
            "linear-gradient(135deg,#f8f7ff 0%,#f0eeff 30%,#faf5ff 100%)",
          minHeight: "100vh",
          fontFamily: "var(--font-sans)",
        }}
      >
        <div className="max-w-7xl mx-auto w-full">
        {/* Header */}
        <div
          style={{
            display: "flex",
            alignItems: "flex-start",
            justifyContent: "space-between",
            marginBottom: 20,
          }}
        >
          <div>
            <h1
              style={{
                fontSize: 24,
                fontWeight: 800,
                color: "#1a1040",
                margin: "0 0 4px",
              }}
            >
              Mes idées
            </h1>
            <p
              style={{
                fontSize: 13,
                color: "#9ca3af",
                margin: 0,
              }}
            >
              Gérez et suivez vos projets IA
            </p>
          </div>
          <button
            type="button"
            onClick={() => navigate("/ideas/new")}
            style={{
              padding: "10px 20px",
              background: "linear-gradient(135deg,#7F77DD,#534AB7)",
              color: "white",
              border: "none",
              borderRadius: 99,
              fontSize: 13,
              fontWeight: 700,
              cursor: "pointer",
              boxShadow: "0 2px 10px rgba(124,58,237,0.25)",
              display: "flex",
              alignItems: "center",
              gap: 6,
              transition: "all 0.2s",
            }}
            onMouseOver={(e) => {
              e.currentTarget.style.boxShadow =
                "0 4px 16px rgba(124,58,237,0.35)";
              e.currentTarget.style.transform = "translateY(-1px)";
            }}
            onMouseOut={(e) => {
              e.currentTarget.style.boxShadow =
                "0 2px 10px rgba(124,58,237,0.25)";
              e.currentTarget.style.transform = "translateY(0)";
            }}
          >
            <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
              <path
                d="M7 2v10M2 7h10"
                stroke="white"
                strokeWidth="1.8"
                strokeLinecap="round"
              />
            </svg>
            Nouvelle idée
          </button>
        </div>

        {/* Stats */}
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(3,1fr)",
            gap: 10,
            marginBottom: 20,
          }}
        >
          {[
            {
              label: "Total idées",
              value: totalCount,
              border: "#e8e4ff",
              labelColor: "#9ca3af",
              valueColor: "#1a1040",
              iconBg: "#f0eeff",
              icon: (
                <svg width="13" height="13" viewBox="0 0 14 14" fill="none">
                  <path
                    d="M7 1.5l1.2 3 3 .4-2.2 2.1.5 3L7 8.5l-2.5 1.5.5-3L2.8 5l3-.4L7 1.5z"
                    stroke="#7F77DD"
                    strokeWidth="1.1"
                    strokeLinejoin="round"
                  />
                </svg>
              ),
            },
            {
              label: "En cours",
              value: runningCount,
              border: "#AFA9EC",
              labelColor: "#7F77DD",
              valueColor: "#3C3489",
              iconBg: "#EEEDFE",
              icon: (
                <svg width="13" height="13" viewBox="0 0 14 14" fill="none">
                  <circle
                    cx="7"
                    cy="7"
                    r="5"
                    stroke="#7F77DD"
                    strokeWidth="1.3"
                  />
                  <path
                    d="M7 4.5v3M7 9v.3"
                    stroke="#7F77DD"
                    strokeWidth="1.3"
                    strokeLinecap="round"
                  />
                </svg>
              ),
            },
            {
              label: "Terminées",
              value: doneCount,
              border: "#9FE1CB",
              labelColor: "#1D9E75",
              valueColor: "#085041",
              iconBg: "#E1F5EE",
              icon: (
                <svg width="13" height="13" viewBox="0 0 14 14" fill="none">
                  <path
                    d="M2 7l3 3 7-6"
                    stroke="#1D9E75"
                    strokeWidth="1.5"
                    strokeLinecap="round"
                  />
                </svg>
              ),
            },
          ].map(
            ({
              label,
              value,
              border,
              labelColor,
              valueColor,
              iconBg,
              icon,
            }) => (
              <div
                key={label}
                style={{
                  background: "white",
                  border: `0.5px solid ${border}`,
                  borderRadius: 14,
                  padding: "16px 18px",
                  boxShadow: "0 2px 8px rgba(124,58,237,0.05)",
                }}
              >
                <div
                  style={{
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "space-between",
                    marginBottom: 8,
                  }}
                >
                  <span
                    style={{
                      fontSize: 11,
                      fontWeight: 600,
                      color: labelColor,
                      textTransform: "uppercase",
                      letterSpacing: "0.07em",
                    }}
                  >
                    {label}
                  </span>
                  <div
                    style={{
                      width: 28,
                      height: 28,
                      borderRadius: 8,
                      background: iconBg,
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "center",
                    }}
                  >
                    {icon}
                  </div>
                </div>
                <div
                  style={{
                    fontSize: 28,
                    fontWeight: 800,
                    color: valueColor,
                  }}
                >
                  {value}
                </div>
              </div>
            ),
          )}
        </div>

        {/* Erreur */}
        {error && (
          <div
            style={{
              marginBottom: 16,
              borderRadius: 12,
              border: "0.5px solid #fecaca",
              background: "#fef2f2",
              padding: "10px 14px",
              fontSize: 13,
              color: "#b91c1c",
            }}
          >
            {error}
          </div>
        )}

        {/* Filtres + Search */}
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: 10,
            marginBottom: 14,
          }}
        >
          <div style={{ flex: 1, position: "relative" }}>
            <svg
              width="14"
              height="14"
              viewBox="0 0 14 14"
              fill="none"
              style={{
                position: "absolute",
                left: 12,
                top: "50%",
                transform: "translateY(-50%)",
              }}
            >
              <circle
                cx="6"
                cy="6"
                r="4"
                stroke="#AFA9EC"
                strokeWidth="1.3"
              />
              <path
                d="M9.5 9.5l2.5 2.5"
                stroke="#AFA9EC"
                strokeWidth="1.3"
                strokeLinecap="round"
              />
            </svg>
            <input
              type="text"
              value={search}
              onChange={(e) => {
                setSearch(e.target.value);
                setCurrentPage(1);
              }}
              placeholder="Rechercher par nom ou secteur..."
              style={{
                width: "100%",
                padding: "9px 14px 9px 36px",
                border: "1.5px solid #e8e4ff",
                borderRadius: 99,
                fontSize: 13,
                background: "white",
                color: "#1a1040",
                outline: "none",
                boxSizing: "border-box",
                transition: "border-color 0.2s",
              }}
              onFocus={(e) => {
                e.target.style.borderColor = "#7F77DD";
              }}
              onBlur={(e) => {
                e.target.style.borderColor = "#e8e4ff";
              }}
            />
          </div>

          <select
            value={statusFilter}
            onChange={(e) => {
              setStatusFilter(e.target.value);
              setCurrentPage(1);
            }}
            style={{
              padding: "9px 14px",
              border: "1.5px solid #e8e4ff",
              borderRadius: 99,
              fontSize: 12,
              background: "white",
              color: "#6b7280",
              outline: "none",
              cursor: "pointer",
              fontFamily: "var(--font-sans)",
            }}
          >
            <option value="">Tous les statuts</option>
            <option value="pending">En attente</option>
            <option value="in_progress">En cours</option>
            <option value="done">Terminé</option>
          </select>
        </div>

        {/* Liste d'idées */}
        {loading ? (
          <div
            style={{
              display: "flex",
              flexDirection: "column",
              gap: 8,
              marginBottom: 20,
            }}
          >
            {[1, 2, 3].map((i) => (
              <div
                key={i}
                style={{
                  background: "white",
                  border: "0.5px solid #e8e4ff",
                  borderRadius: 14,
                  padding: "14px 16px",
                  display: "flex",
                  alignItems: "center",
                  gap: 12,
                  boxShadow: "0 2px 8px rgba(124,58,237,0.04)",
                }}
              >
                <div
                  style={{
                    width: 40,
                    height: 40,
                    borderRadius: 10,
                    background: "#f0eeff",
                    flexShrink: 0,
                  }}
                />
                <div style={{ flex: 1 }}>
                  <div
                    style={{
                      height: 13,
                      width: "60%",
                      background: "#f0eeff",
                      borderRadius: 4,
                      marginBottom: 8,
                    }}
                  />
                  <div
                    style={{
                      height: 10,
                      width: "30%",
                      background: "#f8f7ff",
                      borderRadius: 4,
                    }}
                  />
                </div>
              </div>
            ))}
          </div>
        ) : ideas.length === 0 ? (
          <div
            style={{
              background: "white",
              border: "0.5px solid #e8e4ff",
              borderRadius: 16,
              padding: "48px 24px",
              textAlign: "center",
              boxShadow: "0 2px 8px rgba(124,58,237,0.04)",
              marginBottom: 20,
            }}
          >
            <div
              style={{
                width: 56,
                height: 56,
                borderRadius: "50%",
                background: "#f0eeff",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                margin: "0 auto 16px",
              }}
            >
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
                <path
                  d="M12 3l2 5.5 5.5.8-4 3.9.9 5.5L12 16l-4.4 2.7.9-5.5-4-3.9 5.5-.8L12 3z"
                  stroke="#7F77DD"
                  strokeWidth="1.5"
                  strokeLinejoin="round"
                />
              </svg>
            </div>
            <div
              style={{
                fontSize: 15,
                fontWeight: 700,
                color: "#1a1040",
                marginBottom: 8,
              }}
            >
              Aucune idée pour l&apos;instant
            </div>
            <div
              style={{
                fontSize: 13,
                color: "#9ca3af",
                marginBottom: 20,
              }}
            >
              Créez votre première idée et laissez l&apos;IA la transformer en
              marque complète.
            </div>
            <button
              type="button"
              onClick={() => navigate("/ideas/new")}
              style={{
                padding: "10px 24px",
                background: "linear-gradient(135deg,#7F77DD,#534AB7)",
                color: "white",
                border: "none",
                borderRadius: 99,
                fontSize: 13,
                fontWeight: 700,
                cursor: "pointer",
                boxShadow: "0 2px 10px rgba(124,58,237,0.25)",
              }}
            >
              Créer ma première idée →
            </button>
          </div>
        ) : (
          <div
            style={{
              display: "flex",
              flexDirection: "column",
              gap: 8,
              marginBottom: 20,
            }}
          >
            {pageIdeas.map((idea, index) => {
              const { bg, color, avatarBg } = getSectorStyle(idea.sector);
              const {
                label: statusLabel,
                color: statusColor,
              } = getStatusLabel(idea);
              const progress = getProgress(idea);

              return (
                <div
                  key={idea.id}
                  className="idea-card"
                  style={{
                    animationDelay: `${index * 0.05}s`,
                  }}
                  onClick={() => navigate(`/ideas/${idea.id}`)}
                >
                  <div
                    style={{
                      width: 40,
                      height: 40,
                      borderRadius: 10,
                      background: avatarBg,
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "center",
                      fontSize: 12,
                      fontWeight: 800,
                      color,
                      flexShrink: 0,
                    }}
                  >
                    {getInitials(idea)}
                  </div>

                  <div
                    style={{
                      flex: 1,
                      minWidth: 0,
                    }}
                  >
                    <div
                      style={{
                        fontSize: 13,
                        fontWeight: 700,
                        color: "#1a1040",
                        marginBottom: 3,
                        overflow: "hidden",
                        textOverflow: "ellipsis",
                        whiteSpace: "nowrap",
                      }}
                    >
                      {getDisplayName(idea)}
                    </div>
                    <div
                      style={{
                        display: "flex",
                        gap: 6,
                        alignItems: "center",
                      }}
                    >
                      {idea.sector && (
                        <span
                          style={{
                            fontSize: 10,
                            padding: "2px 8px",
                            borderRadius: 99,
                            background: bg,
                            color,
                            fontWeight: 600,
                          }}
                        >
                          {idea.sector}
                        </span>
                      )}
                      <span
                        style={{
                          fontSize: 11,
                          color: "#9ca3af",
                        }}
                      >
                        {new Date(idea.created_at).toLocaleDateString("fr-FR", {
                          day: "numeric",
                          month: "long",
                          year: "numeric",
                        })}
                      </span>
                    </div>
                  </div>

                  <div
                    style={{
                      display: "flex",
                      alignItems: "center",
                      gap: 10,
                      flexShrink: 0,
                    }}
                  >
                    <div style={{ textAlign: "right" }}>
                      <div
                        style={{
                          fontSize: 10,
                          fontWeight: 600,
                          color: statusColor,
                          marginBottom: 4,
                        }}
                      >
                        {statusLabel}
                      </div>
                      <div
                        style={{
                          width: 72,
                          height: 4,
                          borderRadius: 99,
                          background: bg,
                          overflow: "hidden",
                        }}
                      >
                        <div
                          style={{
                            height: "100%",
                            width: `${progress}%`,
                            background:
                              progress === 100
                                ? "linear-gradient(90deg,#1D9E75,#085041)"
                                : "linear-gradient(90deg,#7F77DD,#534AB7)",
                            borderRadius: 99,
                            transition: "width 0.5s ease",
                          }}
                        />
                      </div>
                    </div>

                    <button
                      type="button"
                      onClick={(e) => {
                        e.stopPropagation();
                        navigate(`/ideas/${idea.id}`);
                      }}
                      style={{
                        padding: "6px 14px",
                        background:
                          idea.status === "done"
                            ? "white"
                            : "linear-gradient(135deg,#7F77DD,#534AB7)",
                        color: idea.status === "done" ? "#1D9E75" : "white",
                        border:
                          idea.status === "done"
                            ? "0.5px solid #9FE1CB"
                            : "none",
                        borderRadius: 99,
                        fontSize: 11,
                        fontWeight: 700,
                        cursor: "pointer",
                        boxShadow:
                          idea.status === "done"
                            ? "none"
                            : "0 2px 6px rgba(124,58,237,0.25)",
                        whiteSpace: "nowrap",
                      }}
                    >
                      {idea.status === "done" ? "Voir →" : "Affiner →"}
                    </button>

                    <button
                      type="button"
                      onClick={(e) => {
                        e.stopPropagation();
                        handleDeleteIdea(idea.id);
                      }}
                      style={{
                        width: 28,
                        height: 28,
                        borderRadius: "50%",
                        background: "white",
                        border: "0.5px solid #fecaca",
                        cursor: "pointer",
                        display: "flex",
                        alignItems: "center",
                        justifyContent: "center",
                        flexShrink: 0,
                        transition: "all 0.15s",
                      }}
                      onMouseOver={(e) => {
                        e.currentTarget.style.background = "#fff5f5";
                      }}
                      onMouseOut={(e) => {
                        e.currentTarget.style.background = "white";
                      }}
                    >
                      <svg
                        width="11"
                        height="11"
                        viewBox="0 0 12 12"
                        fill="none"
                      >
                        <path
                          d="M2 3h8M5 3V2h2v1M4 3v6h4V3"
                          stroke="#e11d48"
                          strokeWidth="1.2"
                          strokeLinecap="round"
                          strokeLinejoin="round"
                        />
                      </svg>
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        )}

        {/* Pagination avec style précédent */}
        {totalPages > 1 && (
          <div
            style={{
              display: "flex",
              alignItems: "center",
              justifyContent: "space-between",
              marginTop: 16,
            }}
          >
            <span
              style={{
                fontSize: 12,
                color: "#9ca3af",
              }}
            >
              {filteredIdeas.length === 0
                ? "Aucun résultat"
                : `${(currentPage - 1) * IDEAS_PER_PAGE + 1}–${Math.min(
                    currentPage * IDEAS_PER_PAGE,
                    filteredIdeas.length,
                  )} sur ${filteredIdeas.length} idées`}
            </span>

            <div
              style={{
                display: "flex",
                alignItems: "center",
                gap: 4,
              }}
            >
              <button
                type="button"
                onClick={() => handlePageChange(currentPage - 1)}
                disabled={currentPage === 1}
                style={{
                  width: 32,
                  height: 32,
                  borderRadius: 99,
                  background: "white",
                  border: "0.5px solid #e8e4ff",
                  cursor: currentPage === 1 ? "not-allowed" : "pointer",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  opacity: currentPage === 1 ? 0.4 : 1,
                  transition: "all 0.15s",
                }}
              >
                <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
                  <path
                    d="M7 2L3 6l4 4"
                    stroke="#6b7280"
                    strokeWidth="1.3"
                    strokeLinecap="round"
                  />
                </svg>
              </button>

              {Array.from({ length: Math.min(totalPages, 5) }, (_, i) => {
                let page;
                if (totalPages <= 5) {
                  page = i + 1;
                } else if (currentPage <= 3) {
                  page = i + 1;
                } else if (currentPage >= totalPages - 2) {
                  page = totalPages - 4 + i;
                } else {
                  page = currentPage - 2 + i;
                }
                return (
                  <button
                    key={page}
                    type="button"
                    onClick={() => handlePageChange(page)}
                    style={{
                      width: 32,
                      height: 32,
                      borderRadius: 99,
                      background:
                        page === currentPage
                          ? "linear-gradient(135deg,#7F77DD,#534AB7)"
                          : "white",
                      border: "0.5px solid #e8e4ff",
                      color: page === currentPage ? "white" : "#6b7280",
                      fontSize: 12,
                      fontWeight: page === currentPage ? 700 : 400,
                      cursor: "pointer",
                      boxShadow:
                        page === currentPage
                          ? "0 2px 8px rgba(124,58,237,0.25)"
                          : "none",
                      transition: "all 0.15s",
                    }}
                  >
                    {page}
                  </button>
                );
              })}

              {totalPages > 5 && currentPage < totalPages - 2 && (
                <span
                  style={{
                    fontSize: 12,
                    color: "#9ca3af",
                    padding: "0 4px",
                  }}
                >
                  ...
                </span>
              )}

              {totalPages > 5 && currentPage < totalPages - 2 && (
                <button
                  type="button"
                  onClick={() => handlePageChange(totalPages)}
                  style={{
                    width: 32,
                    height: 32,
                    borderRadius: 99,
                    background: "white",
                    border: "0.5px solid #e8e4ff",
                    color: "#6b7280",
                    fontSize: 12,
                    cursor: "pointer",
                    transition: "all 0.15s",
                  }}
                >
                  {totalPages}
                </button>
              )}

              <button
                type="button"
                onClick={() => handlePageChange(currentPage + 1)}
                disabled={currentPage === totalPages}
                style={{
                  width: 32,
                  height: 32,
                  borderRadius: 99,
                  background: "white",
                  border: "0.5px solid #e8e4ff",
                  cursor:
                    currentPage === totalPages ? "not-allowed" : "pointer",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  opacity: currentPage === totalPages ? 0.4 : 1,
                  transition: "all 0.15s",
                }}
              >
                <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
                  <path
                    d="M5 2l4 4-4 4"
                    stroke="#6b7280"
                    strokeWidth="1.3"
                    strokeLinecap="round"
                  />
                </svg>
              </button>
            </div>
          </div>
        )}
      </div>
      </div>
    </>
  );
}

