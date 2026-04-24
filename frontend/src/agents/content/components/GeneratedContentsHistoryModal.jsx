import { useEffect, useMemo, useState } from "react";
import { FaInstagram, FaFacebookF, FaLinkedinIn } from "react-icons/fa";
import { FiClock, FiX, FiCheckCircle, FiAlertCircle, FiFileText, FiFilter } from "react-icons/fi";
import { apiListGeneratedContents } from "@/services/generatedContentApi";
import { Button } from "@/shared/ui/Button";
import { PLATFORMS, PLATFORM_LABELS } from "../constants";

/* ── Méta plateforme ─────────────────────────────────────────────────────── */
const PLATFORM_ICON = {
  instagram: FaInstagram,
  facebook:  FaFacebookF,
  linkedin:  FaLinkedinIn,
};

const PLATFORM_COLOR = {
  instagram: { bg: "bg-gradient-to-br from-[#833AB4] to-[#E1306C]", text: "text-white" },
  facebook:  { bg: "bg-[#1877F2]", text: "text-white" },
  linkedin:  { bg: "bg-[#0A66C2]", text: "text-white" },
};

/* ── Méta statut ─────────────────────────────────────────────────────────── */
const STATUS_META = {
  generated:     { label: "Non publié",  className: "bg-slate-100 text-slate-700",   dot: "bg-slate-400" },
  edited:        { label: "Modifié",     className: "bg-amber-50 text-amber-800",    dot: "bg-amber-500"  },
  published:     { label: "Publié",      className: "bg-emerald-50 text-emerald-800", dot: "bg-success"   },
  publish_failed:{ label: "Échec envoi", className: "bg-red-50 text-red-700",         dot: "bg-red-500"   },
};

/* ── Options filtre plateforme ───────────────────────────────────────────── */
const PLATFORM_OPTIONS = [
  { value: "", label: "Tout" },
  { value: PLATFORMS.instagram, label: "Instagram" },
  { value: PLATFORMS.facebook,  label: "Facebook"  },
  { value: PLATFORMS.linkedin,  label: "LinkedIn"  },
];

const PUBLICATION_OPTIONS = [
  { value: "all",         label: "Tous"       },
  { value: "published",   label: "Publiés"    },
  { value: "unpublished", label: "Brouillons" },
  { value: "failed",      label: "Échecs"     },
];

/* ── Helpers ─────────────────────────────────────────────────────────────── */
function formatDate(iso) {
  if (!iso) return "—";
  try {
    return new Date(iso).toLocaleString("fr-FR", {
      day: "numeric", month: "short", year: "numeric",
      hour: "2-digit", minute: "2-digit",
    });
  } catch { return "—"; }
}

function matchesPublicationFilter(row, f) {
  if (f === "all")         return true;
  if (f === "published")   return row.status === "published";
  if (f === "unpublished") return row.status === "generated" || row.status === "edited";
  if (f === "failed")      return row.status === "publish_failed";
  return true;
}

/* ── Filtre pill ─────────────────────────────────────────────────────────── */
function FilterPills({ options, value, onChange }) {
  return (
    <div className="flex flex-wrap gap-1.5">
      {options.map((o) => (
        <button
          key={o.value ?? "all"}
          type="button"
          onClick={() => onChange(o.value)}
          className={`rounded-full px-3 py-1 text-2xs font-semibold transition-all duration-150 ${
            value === o.value
              ? "bg-brand text-white shadow-sm"
              : "border border-brand-border bg-white text-ink-muted hover:border-brand-muted hover:text-brand-dark"
          }`}
        >
          {o.label}
        </button>
      ))}
    </div>
  );
}

/* ── Carte post ──────────────────────────────────────────────────────────── */
function PostCard({ row }) {
  const plat  = PLATFORM_LABELS[row.platform] || row.platform;
  const pc    = PLATFORM_COLOR[row.platform]  || { bg: "bg-brand-light", text: "text-brand-dark" };
  const PIcon = PLATFORM_ICON[row.platform]   || FiFileText;
  const st    = STATUS_META[row.status]        || STATUS_META.generated;

  const imgUrl  = row.image_url ? String(row.image_url).trim() : "";
  const hasImage = imgUrl && (imgUrl.startsWith("https://") || imgUrl.startsWith("http://"));

  return (
    <li className="overflow-hidden rounded-2xl border border-brand-border bg-white shadow-sm transition-shadow hover:shadow-card">

      {/* Image */}
      {hasImage && (
        <div className="w-full bg-brand-light/30">
          <img
            src={imgUrl}
            alt=""
            loading="lazy"
            className="max-h-64 w-full object-cover sm:max-h-72"
            onError={(e) => { e.currentTarget.parentElement.style.display = "none"; }}
          />
        </div>
      )}

      <div className="space-y-3 p-4">
        {/* ── Meta row ── */}
        <div className="flex flex-wrap items-center gap-2">
          {/* Platform badge */}
          <span className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-2xs font-bold ${pc.bg} ${pc.text}`}>
            <PIcon className="h-3 w-3 shrink-0" />
            {plat}
          </span>

          {/* Status badge */}
          <span className={`inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-2xs font-semibold ${st.className}`}>
            <span className={`h-1.5 w-1.5 shrink-0 rounded-full ${st.dot}`} />
            {st.label}
          </span>

          {/* Date */}
          <span className="ml-auto flex items-center gap-1 text-2xs text-ink-subtle">
            <FiClock className="h-3 w-3 shrink-0" />
            {formatDate(row.created_at)}
          </span>
        </div>

        {/* Caption */}
        <p className="whitespace-pre-wrap text-sm leading-relaxed text-ink">
          {row.caption || "—"}
        </p>

        {/* Published at */}
        {row.status === "published" && row.published_at && (
          <div className="flex items-center gap-1.5 rounded-lg bg-emerald-50 px-3 py-2 text-2xs text-emerald-800">
            <FiCheckCircle className="h-3.5 w-3.5 shrink-0 text-success" />
            Publié le {formatDate(row.published_at)}
          </div>
        )}

        {/* Publish error */}
        {row.status === "publish_failed" && row.publish_error && (
          <div className="flex items-start gap-1.5 rounded-lg bg-red-50 px-3 py-2 text-2xs text-red-700">
            <FiAlertCircle className="mt-0.5 h-3.5 w-3.5 shrink-0 text-red-500" />
            {row.publish_error}
          </div>
        )}
      </div>
    </li>
  );
}

/* ── Composant principal ─────────────────────────────────────────────────── */
export default function GeneratedContentsHistoryModal({ open, onClose, ideaId, token }) {
  const [items, setItems]                     = useState([]);
  const [loading, setLoading]                 = useState(false);
  const [err, setErr]                         = useState(null);
  const [platformFilter, setPlatformFilter]   = useState("");
  const [publicationFilter, setPublicationFilter] = useState("all");

  useEffect(() => {
    if (!open || !ideaId || !token) return;
    let cancelled = false;
    setLoading(true);
    setErr(null);
    apiListGeneratedContents(ideaId, token)
      .then((data) => { if (!cancelled) setItems(data?.items || []); })
      .catch((e)   => { if (!cancelled) setErr(e?.message || "Chargement impossible."); })
      .finally(()  => { if (!cancelled) setLoading(false); });
    return () => { cancelled = true; };
  }, [open, ideaId, token]);

  useEffect(() => {
    if (!open) { setPlatformFilter(""); setPublicationFilter("all"); }
  }, [open]);

  const filteredItems = useMemo(() =>
    items.filter((row) => {
      if (platformFilter && row.platform !== platformFilter) return false;
      return matchesPublicationFilter(row, publicationFilter);
    }),
    [items, platformFilter, publicationFilter]
  );

  if (!open) return null;

  return (
    <div
      className="fixed inset-0 z-[110] flex items-center justify-center bg-black/50 p-4 backdrop-blur-sm"
      role="dialog"
      aria-modal="true"
      aria-labelledby="gc-history-title"
      onClick={(e) => { if (e.target === e.currentTarget) onClose(); }}
    >
      <div className="flex max-h-[88vh] w-full max-w-lg flex-col overflow-hidden rounded-2xl border border-brand-border bg-white shadow-2xl sm:max-w-2xl">

        {/* ── Header ────────────────────────────────────────────────────── */}
        <div className="shrink-0 flex items-center justify-between border-b border-brand-border bg-gradient-to-r from-brand-light/60 to-white px-5 py-4">
          <div className="flex items-center gap-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-brand-light">
              <FiFileText className="h-4.5 w-4.5 text-brand" />
            </div>
            <div>
              <h2 id="gc-history-title" className="text-base font-bold text-brand-dark">
                Historique des publications
              </h2>
              <p className="text-2xs text-brand-muted">
                {items.length > 0 ? `${items.length} post${items.length > 1 ? "s" : ""} généré${items.length > 1 ? "s" : ""}` : "Tous vos contenus générés"}
              </p>
            </div>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="flex h-8 w-8 items-center justify-center rounded-full border border-brand-border bg-white text-ink-muted transition-colors hover:bg-brand-light hover:text-brand-dark"
            aria-label="Fermer"
          >
            <FiX className="h-4 w-4" />
          </button>
        </div>

        {/* ── Filtres ───────────────────────────────────────────────────── */}
        <div className="shrink-0 space-y-3 border-b border-brand-border bg-brand-light/10 px-5 py-3">
          <div className="flex items-center gap-2">
            <FiFilter className="h-3.5 w-3.5 shrink-0 text-ink-subtle" />
            <span className="text-2xs font-semibold uppercase tracking-wider text-ink-subtle">
              Plateforme
            </span>
          </div>
          <FilterPills options={PLATFORM_OPTIONS} value={platformFilter} onChange={setPlatformFilter} />

          <div className="flex items-center gap-2">
            <span className="text-2xs font-semibold uppercase tracking-wider text-ink-subtle">
              Statut
            </span>
          </div>
          <FilterPills options={PUBLICATION_OPTIONS} value={publicationFilter} onChange={setPublicationFilter} />

          <p className="text-2xs text-ink-subtle">
            <span className="font-semibold text-ink-muted">{filteredItems.length}</span>
            {" "}affiché{filteredItems.length !== 1 ? "s" : ""}
            {items.length !== filteredItems.length && (
              <> sur <span className="font-semibold text-ink-muted">{items.length}</span> au total</>
            )}
          </p>
        </div>

        {/* ── Feed ──────────────────────────────────────────────────────── */}
        <div className="min-h-0 flex-1 overflow-y-auto overscroll-contain px-4 py-4 sm:px-5">

          {loading && (
            <div className="flex flex-col items-center justify-center gap-3 py-12 text-center">
              <div className="h-8 w-8 animate-spin rounded-full border-2 border-brand-border border-t-brand" />
              <p className="text-sm text-ink-muted">Chargement…</p>
            </div>
          )}

          {err && (
            <div className="flex items-start gap-2 rounded-xl bg-red-50 border border-red-200 px-4 py-3">
              <FiAlertCircle className="mt-0.5 h-4 w-4 shrink-0 text-red-500" />
              <p className="text-sm text-red-700">{err}</p>
            </div>
          )}

          {!loading && !err && items.length === 0 && (
            <div className="flex flex-col items-center justify-center gap-3 py-12 text-center">
              <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-brand-light">
                <FiFileText className="h-6 w-6 text-brand-muted" />
              </div>
              <div>
                <p className="text-sm font-semibold text-ink-muted">Aucun contenu encore</p>
                <p className="mt-1 text-xs text-ink-subtle">
                  Générez votre premier post pour qu'il apparaisse ici.
                </p>
              </div>
            </div>
          )}

          {!loading && !err && items.length > 0 && filteredItems.length === 0 && (
            <div className="flex flex-col items-center justify-center gap-3 py-12 text-center">
              <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-brand-light">
                <FiFilter className="h-6 w-6 text-brand-muted" />
              </div>
              <div>
                <p className="text-sm font-semibold text-ink-muted">Aucun résultat</p>
                <p className="mt-1 text-xs text-ink-subtle">
                  Modifiez les filtres pour voir d'autres posts.
                </p>
              </div>
            </div>
          )}

          {!loading && !err && filteredItems.length > 0 && (
            <ul className="flex flex-col gap-4 pb-2">
              {filteredItems.map((row) => <PostCard key={row.id} row={row} />)}
            </ul>
          )}

        </div>

        {/* ── Footer ────────────────────────────────────────────────────── */}
        <div className="shrink-0 flex justify-end border-t border-brand-border bg-brand-light/20 px-5 py-3">
          <Button type="button" variant="secondary" size="md" onClick={onClose}>
            Fermer
          </Button>
        </div>

      </div>
    </div>
  );
}
