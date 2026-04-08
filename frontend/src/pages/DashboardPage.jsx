import { useState, useEffect, useMemo } from "react";
import { useNavigate } from "react-router-dom";
import { Navbar } from "@/components/layout/Navbar";
import { apiGetIdeas, apiDeleteIdea, getErrorMessage } from "@/services/ideaApi";
import { toast } from "react-toastify";
import { useAuth } from "@/shared/hooks/useAuth";

/* ─────────────────────────────────────────────────────────────────────────────
   Constants
───────────────────────────────────────────────────────────────────────────── */
const IDEAS_PER_PAGE = 6;

/* ─────────────────────────────────────────────────────────────────────────────
   Sector color map — Tailwind classes only, no hex
   avatarFrom/avatarTo → used as inline gradient (CSS vars not available in JIT)
   bg/text            → Tailwind utility classes
───────────────────────────────────────────────────────────────────────────── */
const SECTOR_STYLES = {
  tech:       { bg: "bg-blue-50",         text: "text-blue-700",        avatarFrom: "#E6F1FB", avatarTo: "#B5D4F4" },
  education:  { bg: "bg-brand-light",     text: "text-brand-darker",    avatarFrom: "#EEEDFE", avatarTo: "#CECBF6" },
  ecommerce:  { bg: "bg-success-light",   text: "text-success",         avatarFrom: "#E1F5EE", avatarTo: "#9FE1CB" },
  sante:      { bg: "bg-pink-50",         text: "text-pink-700",        avatarFrom: "#FBEAF0", avatarTo: "#F4C0D1" },
  finance:    { bg: "bg-pink-50",         text: "text-pink-700",        avatarFrom: "#FBEAF0", avatarTo: "#F4C0D1" },
  default:    { bg: "bg-brand-light",     text: "text-brand-darker",    avatarFrom: "#EEEDFE", avatarTo: "#CECBF6" },
};

function getSectorStyle(sector) {
  return SECTOR_STYLES[sector?.toLowerCase()] ?? SECTOR_STYLES.default;
}

/* ─────────────────────────────────────────────────────────────────────────────
   Status helpers (logic unchanged)
───────────────────────────────────────────────────────────────────────────── */
const STATUS_PROGRESS_MAP = {
  clarifier_done: 17,
  market_done:    33,
  brand_done:     50,
  content_done:   67,
  website_done:   83,
  done:           100,
};

function getClarifierPct(idea) {
  const steps = idea?.pipeline_progress?.clarifier_steps;
  if (!Array.isArray(steps) || steps.length === 0) return 0;
  return Math.min(Math.round((steps.length / 7) * 17), 17);
}

function getProgress(idea) {
  if (idea?.status === "pending" || idea?.status === "in_progress")
    return getClarifierPct(idea);
  return STATUS_PROGRESS_MAP[idea?.status] ?? 0;
}

// Returns Tailwind text-color class + label string
function getStatusMeta(idea) {
  const pct = getProgress(idea);
  const map = {
    pending:        { cls: "text-ink-subtle",  label: `En attente · ${pct}%` },
    in_progress:    { cls: "text-brand",       label: `Clarifier en cours · ${pct}%` },
    clarifier_done: { cls: "text-brand",       label: `Clarifier ✓ · ${pct}%` },
    done:           { cls: "text-success",     label: `Pipeline complet ✓ · ${pct}%` },
  };
  return map[idea?.status] ?? { cls: "text-ink-subtle", label: `En attente · ${pct}%` };
}

function getInitials(idea) {
  return (idea.name || idea.description || "?").trim().slice(0, 2).toUpperCase();
}

function getDisplayName(idea) {
  if (idea.name?.trim()) return idea.name;
  const desc = idea.description || "";
  return desc.length > 48 ? `${desc.slice(0, 48)}…` : desc || "Idée sans nom";
}

/* ─────────────────────────────────────────────────────────────────────────────
   Sub-components
───────────────────────────────────────────────────────────────────────────── */

/** Stat card — top 3 counters */
function StatCard({ label, value, icon, accent = "brand" }) {
  const accents = {
    brand:   { card: "border-brand-border",  label: "text-ink-subtle",  value: "text-ink",         icon: "bg-brand-light"   },
    active:  { card: "border-brand-muted",   label: "text-brand",       value: "text-brand-darker", icon: "bg-brand-100"     },
    success: { card: "border-success-border",label: "text-success",     value: "text-success-dark", icon: "bg-success-light" },
  };
  const a = accents[accent];

  return (
    <div className={`rounded-xl border ${a.card} bg-white px-5 py-4 shadow-card`}>
      <div className="mb-3 flex items-center justify-between">
        <span className={`text-2xs font-bold uppercase tracking-widest ${a.label}`}>{label}</span>
        <div className={`flex h-8 w-8 items-center justify-center rounded-lg ${a.icon}`}>
          {icon}
        </div>
      </div>
      <p className={`text-4xl font-extrabold ${a.value}`}>{value}</p>
    </div>
  );
}

/** Skeleton row while loading */
function SkeletonRow() {
  return (
    <div className="flex items-center gap-3 rounded-xl border border-brand-border bg-white px-5 py-4 shadow-card">
      <div className="h-10 w-10 shrink-0 animate-pulse rounded-xl bg-brand-light" />
      <div className="flex-1 space-y-2">
        <div className="h-3 w-3/5 animate-pulse rounded-full bg-brand-light" />
        <div className="h-2.5 w-2/5 animate-pulse rounded-full bg-gray-100" />
      </div>
      <div className="h-7 w-20 animate-pulse rounded-full bg-brand-light" />
    </div>
  );
}

/** Empty state */
function EmptyIdeas({ onNew }) {
  return (
    <div className="flex flex-col items-center justify-center rounded-2xl border border-brand-border bg-white px-6 py-16 text-center shadow-card">
      <div className="mx-auto mb-5 flex h-16 w-16 items-center justify-center rounded-2xl bg-brand-light shadow-card">
        <svg width="28" height="28" viewBox="0 0 24 24" fill="none">
          <path
            d="M12 3l2 5.5 5.5.8-4 3.9.9 5.5L12 16l-4.4 2.7.9-5.5-4-3.9 5.5-.8L12 3z"
            stroke="#7C3AED"
            strokeWidth="1.5"
            strokeLinejoin="round"
          />
        </svg>
      </div>
      <h3 className="mb-1.5 text-lg font-extrabold text-ink">Aucune idée pour l&apos;instant</h3>
      <p className="mb-6 max-w-xs text-sm text-ink-muted">
        Créez votre première idée et laissez l&apos;IA la transformer en marque complète.
      </p>
      <button
        type="button"
        onClick={onNew}
        className="inline-flex items-center gap-2 rounded-full bg-gradient-to-br from-brand to-brand-dark px-6 py-2.5 text-sm font-bold text-white shadow-btn transition-all hover:shadow-btn-hover hover:-translate-y-px"
      >
        Créer ma première idée →
      </button>
    </div>
  );
}

/** Single idea row */
function IdeaRow({ idea, onNavigate, onDelete }) {
  const { bg, text, avatarFrom, avatarTo } = getSectorStyle(idea.sector);
  const { cls: statusCls, label: statusLabel } = getStatusMeta(idea);
  const progress  = getProgress(idea);
  const isDone    = idea.status === "done";

  return (
    <div
      className="idea-card"
      onClick={() => onNavigate(`/ideas/${idea.id}`)}
    >
      {/* Avatar */}
      <div
        className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl text-xs font-extrabold"
        style={{ background: `linear-gradient(135deg, ${avatarFrom}, ${avatarTo})` }}
      >
        <span className={text}>{getInitials(idea)}</span>
      </div>

      {/* Info */}
      <div className="min-w-0 flex-1">
        <p className="mb-1 truncate text-base font-bold text-ink">
          {getDisplayName(idea)}
        </p>
        <div className="flex items-center gap-2">
          {idea.sector && (
            <span className={`rounded-full px-2 py-0.5 text-2xs font-semibold ${bg} ${text}`}>
              {idea.sector}
            </span>
          )}
          <span className="text-xs text-ink-subtle">
            {new Date(idea.created_at).toLocaleDateString("fr-FR", {
              day: "numeric", month: "long", year: "numeric",
            })}
          </span>
        </div>
      </div>

      {/* Progress + actions */}
      <div className="flex shrink-0 items-center gap-3">
        {/* Progress */}
        <div className="hidden sm:block text-right">
          <p className={`mb-1.5 text-2xs font-semibold ${statusCls}`}>{statusLabel}</p>
          <div className="h-1.5 w-20 overflow-hidden rounded-full bg-gray-100">
            <div
              className={`h-full rounded-full transition-all duration-500 ${
                isDone
                  ? "bg-gradient-to-r from-success to-success-dark"
                  : "bg-gradient-to-r from-brand to-brand-dark"
              }`}
              style={{ width: `${progress}%` }}
            />
          </div>
        </div>

        {/* Open button */}
        <button
          type="button"
          onClick={(e) => { e.stopPropagation(); onNavigate(`/ideas/${idea.id}`); }}
          className={`whitespace-nowrap rounded-full px-4 py-1.5 text-xs font-bold transition-all ${
            isDone
              ? "border border-success-border bg-white text-success hover:bg-success-light"
              : "bg-gradient-to-br from-brand to-brand-dark text-white shadow-pill hover:shadow-btn"
          }`}
        >
          {isDone ? "Voir →" : "Affiner →"}
        </button>

        {/* Delete button */}
        <button
          type="button"
          onClick={(e) => { e.stopPropagation(); onDelete(idea.id); }}
          className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full border border-red-200 bg-white text-red-400 transition-all hover:bg-red-50 hover:text-red-600"
          aria-label="Supprimer"
        >
          <svg width="11" height="11" viewBox="0 0 12 12" fill="none">
            <path
              d="M2 3h8M5 3V2h2v1M4 3v6h4V3"
              stroke="currentColor"
              strokeWidth="1.3"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          </svg>
        </button>
      </div>
    </div>
  );
}

/** Pagination controls */
function Pagination({ currentPage, totalPages, onChange }) {
  const pageNumbers = useMemo(() => {
    const range = [];
    if (totalPages <= 5) {
      for (let i = 1; i <= totalPages; i++) range.push(i);
    } else if (currentPage <= 3) {
      range.push(1, 2, 3, 4, 5);
    } else if (currentPage >= totalPages - 2) {
      for (let i = totalPages - 4; i <= totalPages; i++) range.push(i);
    } else {
      for (let i = currentPage - 2; i <= currentPage + 2; i++) range.push(i);
    }
    return range;
  }, [currentPage, totalPages]);

  const navBtn = "flex h-8 w-8 items-center justify-center rounded-full border border-brand-border bg-white text-ink-muted transition-all hover:border-brand-muted hover:text-brand disabled:cursor-not-allowed disabled:opacity-40";

  return (
    <div className="flex items-center gap-1">
      <button type="button" onClick={() => onChange(currentPage - 1)} disabled={currentPage === 1} className={navBtn}>
        <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
          <path d="M7 2L3 6l4 4" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" />
        </svg>
      </button>

      {pageNumbers.map((p) => (
        <button
          key={p}
          type="button"
          onClick={() => onChange(p)}
          className={`flex h-8 w-8 items-center justify-center rounded-full border text-xs font-semibold transition-all ${
            p === currentPage
              ? "border-brand bg-gradient-to-br from-brand to-brand-dark text-white shadow-btn"
              : "border-brand-border bg-white text-ink-muted hover:border-brand-muted hover:text-brand"
          }`}
        >
          {p}
        </button>
      ))}

      <button type="button" onClick={() => onChange(currentPage + 1)} disabled={currentPage === totalPages} className={navBtn}>
        <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
          <path d="M5 2l4 4-4 4" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" />
        </svg>
      </button>
    </div>
  );
}

/* ─────────────────────────────────────────────────────────────────────────────
   Main page
───────────────────────────────────────────────────────────────────────────── */
export default function DashboardPage() {
  const { token }       = useAuth();
  const navigate        = useNavigate();
  const [ideas,       setIdeas]       = useState([]);
  const [totalFromApi,setTotalFromApi]= useState(0);
  const [loading,     setLoading]     = useState(true);
  const [error,       setError]       = useState("");
  const [search,      setSearch]      = useState("");
  const [statusFilter,setStatusFilter]= useState("");
  const [currentPage, setCurrentPage] = useState(1);

  /* ── Fetch ─────────────────────────────────────────────────────────────── */
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

  /* ── Filtering + pagination ────────────────────────────────────────────── */
  const filteredIdeas = useMemo(() => {
    let list = [...ideas];
    const q  = search.trim().toLowerCase();
    if (q) list = list.filter((i) =>
      (i.name || "").toLowerCase().includes(q) ||
      (i.sector || "").toLowerCase().includes(q),
    );
    if (statusFilter) list = list.filter((i) => i.status === statusFilter);
    return list;
  }, [ideas, search, statusFilter]);

  const totalPages = Math.max(1, Math.ceil(filteredIdeas.length / IDEAS_PER_PAGE));
  const pageIdeas  = useMemo(() => {
    const start = (currentPage - 1) * IDEAS_PER_PAGE;
    return filteredIdeas.slice(start, start + IDEAS_PER_PAGE);
  }, [filteredIdeas, currentPage]);

  useEffect(() => {
    if (currentPage > totalPages) setCurrentPage(1);
  }, [currentPage, totalPages]);

  /* ── Actions ───────────────────────────────────────────────────────────── */
  const handleDelete = async (ideaId) => {
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

  const handlePageChange = (page) => {
    if (page < 1 || page > totalPages) return;
    setCurrentPage(page);
  };

  /* ── Counts ─────────────────────────────────────────────────────────────── */
  const totalCount   = totalFromApi || ideas.length;
  const runningCount = ideas.filter((i) => ["running", "in_progress"].includes(i.status)).length;
  const doneCount    = ideas.filter((i) => i.status === "done").length;

  /* ── Render ─────────────────────────────────────────────────────────────── */
  return (
    <>
      <Navbar variant="app" />

      <div className="min-h-screen bg-[image:var(--gradient-page)] pt-20">
        <div className="mx-auto w-full max-w-5xl px-6 py-8">

          {/* ── Page header ─────────────────────────────────────────────── */}
          <div className="mb-6 flex items-start justify-between">
            <div>
              <h1 className="mb-1 text-3xl font-extrabold text-ink">Mes idées</h1>
              <p className="text-sm text-ink-muted">Gérez et suivez vos projets IA</p>
            </div>
            <button
              type="button"
              onClick={() => navigate("/ideas/new")}
              className="inline-flex items-center gap-2 rounded-full bg-gradient-to-br from-brand to-brand-dark px-5 py-2.5 text-sm font-bold text-white shadow-btn transition-all hover:shadow-btn-hover hover:-translate-y-px"
            >
              <svg width="13" height="13" viewBox="0 0 14 14" fill="none">
                <path d="M7 2v10M2 7h10" stroke="white" strokeWidth="1.8" strokeLinecap="round" />
              </svg>
              Nouvelle idée
            </button>
          </div>

          {/* ── Stats ───────────────────────────────────────────────────── */}
          <div className="mb-6 grid grid-cols-3 gap-3">
            <StatCard
              label="Total idées"
              value={totalCount}
              accent="brand"
              icon={
                <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
                  <path d="M7 1.5l1.2 3 3 .4-2.2 2.1.5 3L7 8.5l-2.5 1.5.5-3L2.8 5l3-.4L7 1.5z" stroke="#7C3AED" strokeWidth="1.1" strokeLinejoin="round" />
                </svg>
              }
            />
            <StatCard
              label="En cours"
              value={runningCount}
              accent="active"
              icon={
                <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
                  <circle cx="7" cy="7" r="5" stroke="#7C3AED" strokeWidth="1.3" />
                  <path d="M7 4.5v3M7 9v.3" stroke="#7C3AED" strokeWidth="1.3" strokeLinecap="round" />
                </svg>
              }
            />
            <StatCard
              label="Terminées"
              value={doneCount}
              accent="success"
              icon={
                <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
                  <path d="M2 7l3 3 7-6" stroke="#1D9E75" strokeWidth="1.5" strokeLinecap="round" />
                </svg>
              }
            />
          </div>

          {/* ── Error ───────────────────────────────────────────────────── */}
          {error && (
            <div className="mb-4 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-600">
              {error}
            </div>
          )}

          {/* ── Search + filter ─────────────────────────────────────────── */}
          <div className="mb-4 flex items-center gap-3">
            {/* Search input */}
            <div className="relative flex-1">
              <svg width="14" height="14" viewBox="0 0 14 14" fill="none" className="absolute left-3.5 top-1/2 -translate-y-1/2 text-brand-muted">
                <circle cx="6" cy="6" r="4" stroke="currentColor" strokeWidth="1.3" />
                <path d="M9.5 9.5l2.5 2.5" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round" />
              </svg>
              <input
                type="text"
                value={search}
                onChange={(e) => { setSearch(e.target.value); setCurrentPage(1); }}
                placeholder="Rechercher par nom ou secteur…"
                className="w-full rounded-full border border-brand-border bg-white py-2.5 pl-10 pr-4 text-sm text-ink placeholder:text-ink-subtle focus:border-brand focus:outline-none focus:ring-2 focus:ring-brand/20 transition-all"
              />
            </div>

            {/* Status filter */}
            <select
              value={statusFilter}
              onChange={(e) => { setStatusFilter(e.target.value); setCurrentPage(1); }}
              className="cursor-pointer rounded-full border border-brand-border bg-white px-4 py-2.5 text-sm text-ink-muted focus:border-brand focus:outline-none focus:ring-2 focus:ring-brand/20 transition-all"
            >
              <option value="">Tous les statuts</option>
              <option value="pending">En attente</option>
              <option value="in_progress">En cours</option>
              <option value="done">Terminé</option>
            </select>
          </div>

          {/* ── Ideas list ──────────────────────────────────────────────── */}
          {loading ? (
            <div className="mb-5 flex flex-col gap-2">
              {[1, 2, 3, 4].map((i) => <SkeletonRow key={i} />)}
            </div>
          ) : ideas.length === 0 ? (
            <EmptyIdeas onNew={() => navigate("/ideas/new")} />
          ) : filteredIdeas.length === 0 ? (
            <div className="rounded-xl border border-brand-border bg-white px-6 py-10 text-center shadow-card">
              <p className="text-sm font-semibold text-ink">Aucun résultat pour &laquo;{search}&raquo;</p>
              <p className="mt-1 text-xs text-ink-muted">Essayez un autre mot-clé ou réinitialisez les filtres.</p>
              <button
                type="button"
                onClick={() => { setSearch(""); setStatusFilter(""); }}
                className="mt-4 rounded-full border border-brand-border bg-white px-4 py-2 text-xs font-semibold text-brand transition-all hover:bg-brand-light"
              >
                Réinitialiser les filtres
              </button>
            </div>
          ) : (
            <div className="mb-5 flex flex-col gap-2">
              {pageIdeas.map((idea) => (
                <IdeaRow
                  key={idea.id}
                  idea={idea}
                  onNavigate={navigate}
                  onDelete={handleDelete}
                />
              ))}
            </div>
          )}

          {/* ── Pagination ──────────────────────────────────────────────── */}
          {totalPages > 1 && (
            <div className="mt-5 flex items-center justify-between">
              <span className="text-xs text-ink-subtle">
                {filteredIdeas.length === 0
                  ? "Aucun résultat"
                  : `${(currentPage - 1) * IDEAS_PER_PAGE + 1}–${Math.min(
                      currentPage * IDEAS_PER_PAGE,
                      filteredIdeas.length,
                    )} sur ${filteredIdeas.length} idées`}
              </span>
              <Pagination
                currentPage={currentPage}
                totalPages={totalPages}
                onChange={handlePageChange}
              />
            </div>
          )}

        </div>
      </div>
    </>
  );
}
