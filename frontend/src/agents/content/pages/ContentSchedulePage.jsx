import { useCallback, useEffect, useMemo, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import {
  FiCalendar, FiChevronLeft, FiChevronRight,
  FiClock, FiFilter, FiInfo, FiLayers, FiPlus,
} from "react-icons/fi";
import { FaFacebookF, FaInstagram, FaLinkedinIn } from "react-icons/fa";
import { AGENTS } from "@/agents";
import { AgentPageHeader } from "@/agents/shared/components/AgentPageHeader";
import { ErrorBanner } from "@/shared/ui/ErrorBanner";
import { usePipeline } from "@/context/PipelineContext";
import { apiListScheduledPublications } from "@/services/scheduledPublicationsApi";
import CalendarPostDetailModal from "../components/CalendarPostDetailModal";
import ContentCreationModal from "../components/ContentCreationModal";
import GeneratedContentsHistoryModal from "../components/GeneratedContentsHistoryModal";
import WeeklyPlanModal from "../components/WeeklyPlanModal";
import { Button } from "@/shared/ui/Button";

const contentAgent = AGENTS.find((a) => a.id === "content");
const WEEK_DAYS = ["Lun", "Mar", "Mer", "Jeu", "Ven", "Sam", "Dim"];

const PLATFORMS = {
  facebook: {
    key: "facebook",
    label: "Facebook",
    Icon: FaFacebookF,
    color: "#1877F2",
    lightBg: "bg-[#1877F2]/10",
    lightText: "text-[#1877F2]",
    border: "border-[#1877F2]/30",
  },
  instagram: {
    key: "instagram",
    label: "Instagram",
    Icon: FaInstagram,
    color: "#E1306C",
    lightBg: "bg-[#E1306C]/10",
    lightText: "text-[#E1306C]",
    border: "border-[#E1306C]/30",
  },
  linkedin: {
    key: "linkedin",
    label: "LinkedIn",
    Icon: FaLinkedinIn,
    color: "#0A66C2",
    lightBg: "bg-[#0A66C2]/10",
    lightText: "text-[#0A66C2]",
    border: "border-[#0A66C2]/30",
  },
};

function isoDate(date) {
  const y = date.getFullYear();
  const m = String(date.getMonth() + 1).padStart(2, "0");
  const d = String(date.getDate()).padStart(2, "0");
  return `${y}-${m}-${d}`;
}

function buildMonthGrid(monthDate) {
  const year = monthDate.getFullYear();
  const month = monthDate.getMonth();
  const firstDay = new Date(year, month, 1);
  const startOffset = (firstDay.getDay() + 6) % 7;
  const startDate = new Date(year, month, 1 - startOffset);
  return Array.from({ length: 42 }).map((_, i) => {
    const d = new Date(startDate);
    d.setDate(startDate.getDate() + i);
    return { date: d, key: isoDate(d), inCurrentMonth: d.getMonth() === month };
  });
}

function formatDayLabel(dateStr) {
  return new Date(`${dateStr}T12:00:00`).toLocaleDateString("fr-FR", {
    weekday: "long",
    day: "numeric",
    month: "long",
  });
}

function mapApiRowToPost(row) {
  const d = new Date(row.scheduled_at);
  const cap = row.caption_snapshot || "";
  const shortTitle = row.title?.trim() || (cap.length > 72 ? `${cap.slice(0, 72)}…` : cap);
  return {
    id: `sp-${row.id}`,
    scheduleId: row.id,
    date: isoDate(d),
    platform: row.platform,
    title: shortTitle,
    time: d.toLocaleTimeString("fr-FR", { hour: "2-digit", minute: "2-digit" }),
    status: row.status,
    sortKey: d.getTime(),
  };
}

function statusLabel(st) {
  if (st === "scheduled") return "Planifié";
  if (st === "cancelled") return "Annulé";
  if (st === "published") return "Publié";
  if (st === "failed") return "Échec";
  if (st === "publishing") return "Envoi…";
  return st;
}

function statusClass(st) {
  if (st === "scheduled") return "bg-success/10 text-success";
  if (st === "published") return "bg-brand-light text-brand-dark";
  if (st === "cancelled") return "bg-ink-muted/10 text-ink-muted";
  if (st === "failed") return "bg-red-50 text-red-600";
  return "bg-amber-50 text-amber-600";
}

function LeftPanel({ selectedDay, eventsByDay, activeFilters, onToggleFilter, allPosts, onPostClick }) {
  const dayPosts = selectedDay ? (eventsByDay[selectedDay] || []) : [];
  const todayKey = isoDate(new Date());
  const allUpcoming = allPosts
    .filter((p) => p.status === "scheduled" && p.date >= todayKey)
    .sort((a, b) => a.sortKey - b.sortKey)
    .slice(0, 12);

  const listItems = selectedDay ? dayPosts : allUpcoming;

  return (
    <aside className="w-56 shrink-0 space-y-3">
      <div className="rounded-2xl border border-brand-border bg-white p-3 shadow-sm">
        <div className="mb-2 flex items-center gap-1.5 text-2xs font-bold uppercase tracking-wider text-ink-muted">
          <FiFilter className="h-3 w-3" />
          Plateformes
        </div>
        <div className="flex flex-col gap-1.5">
          {Object.values(PLATFORMS).map((p) => {
            const active = activeFilters.includes(p.key);
            const count = allPosts.filter(
              (post) => post.platform === p.key && post.status === "scheduled",
            ).length;
            return (
              <button
                key={p.key}
                type="button"
                onClick={() => onToggleFilter(p.key)}
                className={`flex items-center gap-2 rounded-xl border px-3 py-2 text-left transition-all ${
                  active ? `${p.lightBg} ${p.border}` : "border-transparent bg-brand-light/20"
                }`}
              >
                <span
                  className="flex h-6 w-6 shrink-0 items-center justify-center rounded-lg text-white shadow-sm"
                  style={{ background: active ? p.color : "#d1d5db" }}
                >
                  <p.Icon className="h-3 w-3" />
                </span>
                <span className={`text-xs font-semibold ${active ? p.lightText : "text-ink-muted"}`}>
                  {p.label}
                </span>
                {active && (
                  <span className="ml-auto text-[10px] font-bold" style={{ color: p.color }}>
                    {count}
                  </span>
                )}
              </button>
            );
          })}
        </div>
      </div>

      <div className="overflow-hidden rounded-2xl border border-brand-border bg-white shadow-sm">
        <div className="border-b border-brand-border px-3 py-2.5">
          {selectedDay ? (
            <p className="text-xs font-bold capitalize text-ink">
              {formatDayLabel(selectedDay)}
            </p>
          ) : (
            <div className="flex items-center gap-1.5">
              <FiCalendar className="h-3 w-3 text-brand" />
              <p className="text-xs font-bold text-ink">À venir</p>
            </div>
          )}
        </div>

        <div className="max-h-72 space-y-1.5 overflow-y-auto p-2 scrollbar-thin scrollbar-thumb-brand-border scrollbar-track-transparent">
          {listItems.length === 0 ? (
            <div className="flex flex-col items-center justify-center gap-1 py-6 text-center">
              <FiInfo className="h-5 w-5 text-ink-muted/40" />
              <p className="text-2xs text-ink-muted">
                {selectedDay ? "Aucun post planifié" : "Aucun post à venir"}
              </p>
            </div>
          ) : (
            listItems.map((post) => {
              const p = PLATFORMS[post.platform];
              if (!p) return null;
              return (
                <button
                  key={post.id}
                  type="button"
                  onClick={() => onPostClick?.(post.scheduleId)}
                  className={`w-full rounded-xl border p-2.5 text-left transition-colors hover:opacity-95 ${p.lightBg} ${p.border}`}
                >
                  <div className="mb-1 flex items-center gap-1.5">
                    <span
                      className="flex h-5 w-5 shrink-0 items-center justify-center rounded-lg text-white"
                      style={{ background: p.color }}
                    >
                      <p.Icon className="h-2.5 w-2.5" />
                    </span>
                    <span className={`text-[11px] font-bold ${p.lightText}`}>{p.label}</span>
                    {!selectedDay && (
                      <span className="ml-auto text-[10px] text-ink-muted">
                        {new Date(`${post.date}T12:00:00`).toLocaleDateString("fr-FR", {
                          day: "numeric",
                          month: "short",
                        })}
                      </span>
                    )}
                  </div>
                  <p className="text-xs font-semibold leading-snug text-ink">{post.title}</p>
                  <div className="mt-1 flex items-center gap-1">
                    <FiClock className="h-3 w-3 text-ink-muted" />
                    <span className="text-[10px] text-ink-muted">{post.time}</span>
                    <span
                      className={`ml-auto rounded-full px-1.5 py-0.5 text-[10px] font-semibold ${statusClass(post.status)}`}
                    >
                      {statusLabel(post.status)}
                    </span>
                  </div>
                </button>
              );
            })
          )}
        </div>
      </div>
    </aside>
  );
}

export default function ContentSchedulePage() {
  const location = useLocation();
  const navigate = useNavigate();
  const { idea, token } = usePipeline();
  const [monthCursor, setMonthCursor] = useState(() => new Date());
  const [selectedDay, setSelectedDay] = useState(null);
  const [activeFilters, setActiveFilters] = useState(["facebook", "instagram", "linkedin"]);
  const [allPosts, setAllPosts] = useState([]);
  const [loadError, setLoadError] = useState(null);
  const [loading, setLoading] = useState(false);
  const [detailScheduleId, setDetailScheduleId] = useState(null);
  const [creationModalOpen, setCreationModalOpen] = useState(false);
  const [historyOpen, setHistoryOpen] = useState(false);
  const [weeklyPlanOpen, setWeeklyPlanOpen] = useState(false);

  const todayKey = isoDate(new Date());

  const monthLabel = useMemo(
    () => monthCursor.toLocaleDateString("fr-FR", { month: "long", year: "numeric" }),
    [monthCursor],
  );

  const grid = useMemo(() => buildMonthGrid(monthCursor), [monthCursor]);

  const loadMonth = useCallback(async () => {
    if (!idea?.id || !token) {
      setAllPosts([]);
      return;
    }
    const y = monthCursor.getFullYear();
    const m = monthCursor.getMonth();
    // Important:
    // The calendar UI renders a 6x7 grid (42 cells), including spillover days
    // from previous/next months. We must fetch the full visible range,
    // otherwise posts (e.g. 1st of next month) won't appear in current view.
    const firstDay = new Date(y, m, 1);
    const startOffset = (firstDay.getDay() + 6) % 7; // Monday-based
    const from = new Date(y, m, 1 - startOffset, 0, 0, 0, 0);
    const to = new Date(from);
    to.setDate(from.getDate() + 41);
    to.setHours(23, 59, 59, 999);
    setLoading(true);
    setLoadError(null);
    try {
      const res = await apiListScheduledPublications(idea.id, token, {
        date_from: from.toISOString(),
        date_to: to.toISOString(),
      });
      const items = (res?.items || []).map(mapApiRowToPost);
      setAllPosts(items);
    } catch (e) {
      setLoadError(e?.message || "Impossible de charger le calendrier.");
      setAllPosts([]);
    } finally {
      setLoading(false);
    }
  }, [idea?.id, token, monthCursor]);

  useEffect(() => {
    loadMonth();
  }, [loadMonth]);

  useEffect(() => {
    if (location.state?.openGeneratedHistory) {
      setHistoryOpen(true);
      navigate(".", { replace: true, state: {} });
    }
  }, [location.state, navigate]);

  const eventsByDay = useMemo(
    () =>
      allPosts.reduce((acc, event) => {
        if (event.status !== "scheduled") return acc;
        if (!acc[event.date]) acc[event.date] = [];
        acc[event.date].push(event);
        return acc;
      }, {}),
    [allPosts],
  );

  const filteredEventsByDay = useMemo(
    () =>
      Object.fromEntries(
        Object.entries(eventsByDay).map(([day, posts]) => [
          day,
          posts.filter((p) => activeFilters.includes(p.platform)),
        ]),
      ),
    [eventsByDay, activeFilters],
  );

  function toggleFilter(key) {
    setActiveFilters((prev) =>
      prev.includes(key) ? (prev.length === 1 ? prev : prev.filter((k) => k !== key)) : [...prev, key],
    );
  }

  function handleDayClick(key) {
    setSelectedDay((prev) => (prev === key ? null : key));
  }

  function prevMonth() {
    setMonthCursor((p) => new Date(p.getFullYear(), p.getMonth() - 1, 1));
    setSelectedDay(null);
  }
  function nextMonth() {
    setMonthCursor((p) => new Date(p.getFullYear(), p.getMonth() + 1, 1));
    setSelectedDay(null);
  }
  function goToday() {
    setMonthCursor(new Date());
    setSelectedDay(todayKey);
  }

  return (
    <div className="app-content-scroll flex flex-1 flex-col gap-3">
      <AgentPageHeader
        agent={contentAgent}
        subtitle="Content Creator · Planification"
        action={
          idea?.id && token ? (
            <Button
              type="button"
              variant="secondary"
              size="md"
              className="shrink-0"
              onClick={() => setHistoryOpen(true)}
            >
              Historique des publications
            </Button>
          ) : null
        }
      />

      {!idea?.id && <ErrorBanner message="Chargez un projet pour voir le calendrier." />}
      {loadError && <ErrorBanner message={loadError} />}

      <div className="flex items-start gap-3">
        <LeftPanel
          selectedDay={selectedDay}
          eventsByDay={filteredEventsByDay}
          activeFilters={activeFilters}
          onToggleFilter={toggleFilter}
          allPosts={allPosts}
          onPostClick={(id) => setDetailScheduleId(id)}
        />

        <div className="flex min-w-0 flex-1 flex-col gap-3">
          <div className="flex items-center justify-between gap-2 rounded-2xl border border-brand-border bg-white px-4 py-3 shadow-sm">
            <div className="flex items-center gap-2">
              <button
                type="button"
                onClick={prevMonth}
                className="flex h-8 w-8 items-center justify-center rounded-xl border border-brand-border bg-white text-ink-muted transition-colors hover:bg-brand-light hover:text-brand-dark"
              >
                <FiChevronLeft className="h-4 w-4" />
              </button>
              <button
                type="button"
                onClick={nextMonth}
                className="flex h-8 w-8 items-center justify-center rounded-xl border border-brand-border bg-white text-ink-muted transition-colors hover:bg-brand-light hover:text-brand-dark"
              >
                <FiChevronRight className="h-4 w-4" />
              </button>
            </div>

            <p className="text-sm font-bold capitalize text-ink">
              {monthLabel}
              {loading ? (
                <span className="ml-2 text-2xs font-normal text-ink-muted">Chargement…</span>
              ) : null}
            </p>

            <div className="flex flex-wrap items-center justify-end gap-2">
              <button
                type="button"
                onClick={goToday}
                className="rounded-xl border border-brand-border bg-white px-3 py-1.5 text-xs font-semibold text-ink-muted transition-colors hover:bg-brand-light hover:text-brand-dark"
              >
                Aujourd'hui
              </button>
              <button
                type="button"
                onClick={() => setWeeklyPlanOpen(true)}
                className="inline-flex items-center gap-1.5 rounded-xl border border-brand-border bg-white px-3 py-1.5 text-xs font-semibold text-brand-dark transition-colors hover:bg-brand-light/60"
              >
                <FiLayers className="h-3.5 w-3.5 text-brand" />
                Plan des posts de la semaine
              </button>
              <button
                type="button"
                onClick={() => setCreationModalOpen(true)}
                className="inline-flex items-center gap-1.5 rounded-xl bg-brand px-3 py-1.5 text-xs font-semibold text-white transition-colors hover:bg-brand-dark"
              >
                <FiPlus className="h-3.5 w-3.5" />
                Nouveau post
              </button>
            </div>
          </div>

          <div className="overflow-hidden rounded-2xl border border-brand-border bg-white shadow-card">
            <div className="grid grid-cols-7 border-b border-brand-border">
              {WEEK_DAYS.map((d) => (
                <div
                  key={d}
                  className="border-r border-brand-border/50 px-2 py-2 text-center text-2xs font-bold uppercase tracking-wider text-ink-muted last:border-r-0"
                >
                  {d}
                </div>
              ))}
            </div>

            <div className="grid grid-cols-7" style={{ gridAutoRows: "88px" }}>
              {grid.map((cell) => {
                const events = filteredEventsByDay[cell.key] || [];
                const isToday = cell.key === todayKey;
                const isSelected = cell.key === selectedDay;
                const isOut = !cell.inCurrentMonth;

                return (
                  <div
                    key={cell.key}
                    role="button"
                    tabIndex={0}
                    onClick={() => handleDayClick(cell.key)}
                    onKeyDown={(e) => e.key === "Enter" && handleDayClick(cell.key)}
                    className={[
                      "cursor-pointer select-none border-b border-r border-brand-border/50 p-1.5 transition-colors last-in-row:border-r-0",
                      isOut ? "bg-brand-light/10" : "bg-white hover:bg-brand-light/20",
                      isSelected ? "ring-2 ring-inset ring-brand/60" : "",
                    ].join(" ")}
                  >
                    <div className="mb-1 flex items-center justify-between">
                      <span
                        className={[
                          "flex h-6 w-6 items-center justify-center rounded-full text-xs font-bold",
                          isToday ? "bg-brand text-white shadow-sm" : isOut ? "text-ink-subtle" : "text-ink",
                        ].join(" ")}
                      >
                        {cell.date.getDate()}
                      </span>
                      {events.length > 0 && (
                        <span className="text-[10px] font-semibold text-ink-muted">{events.length}</span>
                      )}
                    </div>

                    <div className="flex flex-col gap-0.5">
                      {events.slice(0, 2).map((ev) => {
                        const p = PLATFORMS[ev.platform];
                        return (
                          <div
                            key={ev.id}
                            role="button"
                            tabIndex={0}
                            onClick={(e) => {
                              e.stopPropagation();
                              setDetailScheduleId(ev.scheduleId);
                            }}
                            onKeyDown={(e) => {
                              if (e.key === "Enter") {
                                e.stopPropagation();
                                setDetailScheduleId(ev.scheduleId);
                              }
                            }}
                            className={`flex cursor-pointer items-center gap-1 rounded-lg px-1.5 py-0.5 ${p.lightBg} hover:ring-1 hover:ring-brand/30`}
                          >
                            <span
                              className="flex h-3.5 w-3.5 shrink-0 items-center justify-center rounded-full text-white"
                              style={{ background: p.color }}
                            >
                              <p.Icon className="h-1.5 w-1.5" />
                            </span>
                            <span className={`truncate text-[10px] font-semibold ${p.lightText}`}>
                              {ev.title}
                            </span>
                          </div>
                        );
                      })}
                      {events.length > 2 && (
                        <span className="px-1 text-[10px] font-semibold text-brand">
                          +{events.length - 2} de plus
                        </span>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          <div className="flex flex-wrap items-center gap-3 rounded-2xl border border-brand-border bg-white px-4 py-2.5 shadow-sm">
            {Object.values(PLATFORMS).map((p) => (
              <span key={p.key} className="flex items-center gap-1.5 text-xs text-ink-muted">
                <span
                  className="flex h-4 w-4 items-center justify-center rounded-full text-white"
                  style={{ background: p.color }}
                >
                  <p.Icon className="h-2 w-2" />
                </span>
                {p.label}
              </span>
            ))}
            <span className="ml-auto flex items-center gap-1.5 text-xs text-ink-muted">
              <span className="flex h-4 w-4 items-center justify-center rounded-full bg-brand text-[9px] font-bold text-white">
                {new Date().getDate()}
              </span>
              Aujourd'hui
            </span>
            <span className="flex items-center gap-1.5 text-xs text-ink-muted">
              <span className="inline-block h-3 w-3 rounded-full bg-white ring-2 ring-brand/50" />
              Sélectionné
            </span>
          </div>
        </div>
      </div>

      <CalendarPostDetailModal
        open={detailScheduleId != null}
        onClose={() => setDetailScheduleId(null)}
        ideaId={idea?.id}
        token={token}
        scheduleId={detailScheduleId}
        onUpdated={loadMonth}
      />

      <ContentCreationModal
        open={creationModalOpen}
        onClose={() => setCreationModalOpen(false)}
        onScheduleCreated={loadMonth}
      />

      <GeneratedContentsHistoryModal
        open={historyOpen}
        onClose={() => setHistoryOpen(false)}
        ideaId={idea?.id}
        token={token}
      />

      <WeeklyPlanModal
        open={weeklyPlanOpen}
        onClose={() => setWeeklyPlanOpen(false)}
        ideaId={idea?.id}
        token={token}
        onApproved={loadMonth}
      />
    </div>
  );
}
