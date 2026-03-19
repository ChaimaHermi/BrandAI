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
        <div className="mb-5 flex items-start justify-between">
          <div>
            <h1 className="mb-1 text-[24px] font-extrabold text-[#1a1040]">
              Mes idées
            </h1>
            <p className="m-0 text-[13px] text-gray-400">
              Gérez et suivez vos projets IA
            </p>
          </div>
          <button
            type="button"
            onClick={() => navigate("/ideas/new")}
            className="flex cursor-pointer items-center gap-1.5 rounded-full border-0 bg-gradient-to-br from-[#7F77DD] to-[#534AB7] px-5 py-[10px] text-[13px] font-bold text-white shadow-[0_2px_10px_rgba(124,58,237,0.25)] transition-all hover:-translate-y-[1px] hover:shadow-[0_4px_16px_rgba(124,58,237,0.35)]"
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
        <div className="mb-5 grid grid-cols-3 gap-[10px]">
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
                className="rounded-[14px] bg-white px-[18px] py-4 shadow-[0_2px_8px_rgba(124,58,237,0.05)]"
                style={{ border: `0.5px solid ${border}` }}
              >
                <div className="mb-2 flex items-center justify-between">
                  <span className="text-[11px] font-semibold uppercase tracking-[0.07em]" style={{ color: labelColor }}>
                    {label}
                  </span>
                  <div className="flex h-7 w-7 items-center justify-center rounded-lg" style={{ background: iconBg }}>
                    {icon}
                  </div>
                </div>
                <div className="text-[28px] font-extrabold" style={{ color: valueColor }}>
                  {value}
                </div>
              </div>
            ),
          )}
        </div>

        {/* Erreur */}
        {error && (
          <div className="mb-4 rounded-xl border border-[#fecaca] bg-[#fef2f2] px-[14px] py-[10px] text-[13px] text-[#b91c1c]">
            {error}
          </div>
        )}

        {/* Filtres + Search */}
        <div className="mb-[14px] flex items-center gap-[10px]">
          <div className="relative flex-1">
            <svg
              width="14"
              height="14"
              viewBox="0 0 14 14"
              fill="none"
              className="absolute left-3 top-1/2 -translate-y-1/2"
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
              className="box-border w-full rounded-full border-[1.5px] border-[#e8e4ff] bg-white py-[9px] pl-9 pr-[14px] text-[13px] text-[#1a1040] outline-none transition-colors focus:border-[#7F77DD]"
            />
          </div>

          <select
            value={statusFilter}
            onChange={(e) => {
              setStatusFilter(e.target.value);
              setCurrentPage(1);
            }}
            className="cursor-pointer rounded-full border-[1.5px] border-[#e8e4ff] bg-white px-[14px] py-[9px] font-[var(--font-sans)] text-xs text-gray-500 outline-none"
          >
            <option value="">Tous les statuts</option>
            <option value="pending">En attente</option>
            <option value="in_progress">En cours</option>
            <option value="done">Terminé</option>
          </select>
        </div>

        {/* Liste d'idées */}
        {loading ? (
          <div className="mb-5 flex flex-col gap-2">
            {[1, 2, 3].map((i) => (
              <div key={i} className="flex items-center gap-3 rounded-[14px] border border-[#e8e4ff] bg-white px-4 py-[14px] shadow-[0_2px_8px_rgba(124,58,237,0.04)]">
                <div className="h-10 w-10 shrink-0 rounded-[10px] bg-[#f0eeff]" />
                <div className="flex-1">
                  <div className="mb-2 h-[13px] w-3/5 rounded bg-[#f0eeff]" />
                  <div className="h-[10px] w-[30%] rounded bg-[#f8f7ff]" />
                </div>
              </div>
            ))}
          </div>
        ) : ideas.length === 0 ? (
          <div className="mb-5 rounded-2xl border border-[#e8e4ff] bg-white px-6 py-12 text-center shadow-[0_2px_8px_rgba(124,58,237,0.04)]">
            <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-full bg-[#f0eeff]">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
                <path
                  d="M12 3l2 5.5 5.5.8-4 3.9.9 5.5L12 16l-4.4 2.7.9-5.5-4-3.9 5.5-.8L12 3z"
                  stroke="#7F77DD"
                  strokeWidth="1.5"
                  strokeLinejoin="round"
                />
              </svg>
            </div>
            <div className="mb-2 text-[15px] font-bold text-[#1a1040]">
              Aucune idée pour l&apos;instant
            </div>
            <div className="mb-5 text-[13px] text-gray-400">
              Créez votre première idée et laissez l&apos;IA la transformer en
              marque complète.
            </div>
            <button
              type="button"
              onClick={() => navigate("/ideas/new")}
              className="cursor-pointer rounded-full border-0 bg-gradient-to-br from-[#7F77DD] to-[#534AB7] px-6 py-[10px] text-[13px] font-bold text-white shadow-[0_2px_10px_rgba(124,58,237,0.25)]"
            >
              Créer ma première idée →
            </button>
          </div>
        ) : (
          <div className="mb-5 flex flex-col gap-2">
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
                  style={{ animationDelay: `${index * 0.05}s` }}
                  onClick={() => navigate(`/ideas/${idea.id}`)}
                >
                  <div
                    className="flex h-10 w-10 shrink-0 items-center justify-center rounded-[10px] text-xs font-extrabold"
                    style={{ background: avatarBg, color }}
                  >
                    {getInitials(idea)}
                  </div>

                  <div className="min-w-0 flex-1">
                    <div className="mb-[3px] overflow-hidden text-ellipsis whitespace-nowrap text-[13px] font-bold text-[#1a1040]">
                      {getDisplayName(idea)}
                    </div>
                    <div className="flex items-center gap-1.5">
                      {idea.sector && (
                        <span className="rounded-full px-2 py-0.5 text-[10px] font-semibold" style={{ background: bg, color }}>
                          {idea.sector}
                        </span>
                      )}
                      <span className="text-[11px] text-gray-400">
                        {new Date(idea.created_at).toLocaleDateString("fr-FR", {
                          day: "numeric",
                          month: "long",
                          year: "numeric",
                        })}
                      </span>
                    </div>
                  </div>

                  <div className="flex shrink-0 items-center gap-[10px]">
                    <div className="text-right">
                      <div className="mb-1 text-[10px] font-semibold" style={{ color: statusColor }}>
                        {statusLabel}
                      </div>
                      <div className="h-1 w-[72px] overflow-hidden rounded-full" style={{ background: bg }}>
                        <div
                          style={{
                            height: "100%",
                            width: `${progress}%`,
                            background:
                              progress === 100
                                ? "linear-gradient(90deg,#1D9E75,#085041)"
                                : "linear-gradient(90deg,#7F77DD,#534AB7)",
                            transition: "width 0.5s ease",
                          }}
                          className="rounded-full"
                        />
                      </div>
                    </div>

                    <button
                      type="button"
                      onClick={(e) => {
                        e.stopPropagation();
                        navigate(`/ideas/${idea.id}`);
                      }}
                      className={`whitespace-nowrap rounded-full px-[14px] py-1.5 text-[11px] font-bold ${
                        idea.status === "done"
                          ? "border border-[#9FE1CB] bg-white text-[#1D9E75] shadow-none"
                          : "bg-gradient-to-br from-[#7F77DD] to-[#534AB7] text-white shadow-[0_2px_6px_rgba(124,58,237,0.25)]"
                      }`}
                    >
                      {idea.status === "done" ? "Voir →" : "Affiner →"}
                    </button>

                    <button
                      type="button"
                      onClick={(e) => {
                        e.stopPropagation();
                        handleDeleteIdea(idea.id);
                      }}
                      className="flex h-7 w-7 shrink-0 cursor-pointer items-center justify-center rounded-full border border-[#fecaca] bg-white transition-all duration-150 hover:bg-[#fff5f5]"
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
          <div className="mt-4 flex items-center justify-between">
            <span className="text-xs text-gray-400">
              {filteredIdeas.length === 0
                ? "Aucun résultat"
                : `${(currentPage - 1) * IDEAS_PER_PAGE + 1}–${Math.min(
                    currentPage * IDEAS_PER_PAGE,
                    filteredIdeas.length,
                  )} sur ${filteredIdeas.length} idées`}
            </span>

            <div className="flex items-center gap-1">
              <button
                type="button"
                onClick={() => handlePageChange(currentPage - 1)}
                disabled={currentPage === 1}
                className="flex h-8 w-8 cursor-pointer items-center justify-center rounded-full border border-[#e8e4ff] bg-white transition-all duration-150 disabled:cursor-not-allowed disabled:opacity-40"
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
                    className={`flex h-8 w-8 cursor-pointer items-center justify-center rounded-full border border-[#e8e4ff] transition-all duration-150 ${
                      page === currentPage
                        ? "bg-gradient-to-br from-[#7F77DD] to-[#534AB7] text-white shadow-[0_2px_8px_rgba(124,58,237,0.25)]"
                        : "bg-white text-xs text-gray-500"
                    }`}
                  >
                    {page}
                  </button>
                );
              })}

              {totalPages > 5 && currentPage < totalPages - 2 && (
                <span className="px-1 text-xs text-gray-400">
                  ...
                </span>
              )}

              {totalPages > 5 && currentPage < totalPages - 2 && (
                <button
                  type="button"
                  onClick={() => handlePageChange(totalPages)}
                  className="flex h-8 w-8 cursor-pointer items-center justify-center rounded-full border border-[#e8e4ff] bg-white text-xs text-gray-500 transition-all duration-150"
                >
                  {totalPages}
                </button>
              )}

              <button
                type="button"
                onClick={() => handlePageChange(currentPage + 1)}
                disabled={currentPage === totalPages}
                className="flex h-8 w-8 cursor-pointer items-center justify-center rounded-full border border-[#e8e4ff] bg-white transition-all duration-150 disabled:cursor-not-allowed disabled:opacity-40"
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

