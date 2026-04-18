import { useEffect, useMemo, useState } from "react";
import { apiListGeneratedContents } from "@/services/generatedContentApi";
import { Button } from "@/shared/ui/Button";
import { PLATFORMS, PLATFORM_LABELS } from "../constants";

const STATUS_META = {
  generated: { label: "Non publié", className: "bg-slate-100 text-slate-800" },
  published: { label: "Publié", className: "bg-emerald-100 text-emerald-900" },
  publish_failed: { label: "Échec envoi", className: "bg-red-100 text-red-900" },
};

const PLATFORM_OPTIONS = [
  { value: "", label: "Toutes les plateformes" },
  { value: PLATFORMS.instagram, label: PLATFORM_LABELS[PLATFORMS.instagram] },
  { value: PLATFORMS.facebook, label: PLATFORM_LABELS[PLATFORMS.facebook] },
  { value: PLATFORMS.linkedin, label: PLATFORM_LABELS[PLATFORMS.linkedin] },
];

/** Tous | Publiés | Non publiés (brouillon) | Échec */
const PUBLICATION_OPTIONS = [
  { value: "all", label: "Tous les posts" },
  { value: "published", label: "Publiés" },
  { value: "unpublished", label: "Non publiés" },
  { value: "failed", label: "Échec d’envoi" },
];

function formatDate(iso) {
  if (!iso) return "—";
  try {
    return new Date(iso).toLocaleString("fr-FR", {
      day: "numeric",
      month: "short",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  } catch {
    return "—";
  }
}

function matchesPublicationFilter(row, pubFilter) {
  if (pubFilter === "all") return true;
  if (pubFilter === "published") return row.status === "published";
  if (pubFilter === "unpublished") return row.status === "generated";
  if (pubFilter === "failed") return row.status === "publish_failed";
  return true;
}

/**
 * Historique des contenus générés — affichage type feed (scroll), image, filtres plateforme + publication.
 */
export default function GeneratedContentsHistoryModal({
  open,
  onClose,
  ideaId,
  token,
}) {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState(null);
  const [platformFilter, setPlatformFilter] = useState("");
  const [publicationFilter, setPublicationFilter] = useState("all");

  useEffect(() => {
    if (!open || !ideaId || !token) return;
    let cancelled = false;
    setLoading(true);
    setErr(null);
    apiListGeneratedContents(ideaId, token)
      .then((data) => {
        if (!cancelled) setItems(data?.items || []);
      })
      .catch((e) => {
        if (!cancelled) setErr(e?.message || "Chargement impossible.");
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [open, ideaId, token]);

  useEffect(() => {
    if (!open) {
      setPlatformFilter("");
      setPublicationFilter("all");
    }
  }, [open]);

  const filteredItems = useMemo(() => {
    return items.filter((row) => {
      if (platformFilter && row.platform !== platformFilter) return false;
      return matchesPublicationFilter(row, publicationFilter);
    });
  }, [items, platformFilter, publicationFilter]);

  if (!open) return null;

  return (
    <div
      className="fixed inset-0 z-[110] flex items-center justify-center bg-black/45 p-4"
      role="dialog"
      aria-modal="true"
      aria-labelledby="gc-history-title"
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
    >
      <div className="flex max-h-[88vh] w-full max-w-lg flex-col overflow-hidden rounded-2xl border border-brand-border bg-white shadow-xl sm:max-w-2xl">
        <div className="shrink-0 border-b border-brand-border bg-brand-light/50 px-5 py-4">
          <h2 id="gc-history-title" className="text-lg font-bold text-brand-dark">
            Publications générées
          </h2>
          <p className="mt-1 text-xs text-brand-muted">
            Filtrez par réseau et par statut ; défilez le fil comme un feed.
          </p>
        </div>

        {/* Filtres — sticky sous le titre */}
        <div className="shrink-0 space-y-2 border-b border-brand-border bg-[#FAFAFC] px-5 py-3">
          <div className="flex flex-wrap items-center gap-2">
            <label className="text-2xs font-semibold uppercase text-brand-muted">
              Plateforme
            </label>
            <select
              value={platformFilter}
              onChange={(e) => setPlatformFilter(e.target.value)}
              className="min-w-[10rem] flex-1 rounded-lg border border-brand-border bg-white px-3 py-2 text-sm text-brand-dark sm:flex-none"
            >
              {PLATFORM_OPTIONS.map((o) => (
                <option key={o.value || "all"} value={o.value}>
                  {o.label}
                </option>
              ))}
            </select>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <label className="text-2xs font-semibold uppercase text-brand-muted">
              Publication
            </label>
            <select
              value={publicationFilter}
              onChange={(e) => setPublicationFilter(e.target.value)}
              className="min-w-[10rem] flex-1 rounded-lg border border-brand-border bg-white px-3 py-2 text-sm text-brand-dark sm:flex-none"
            >
              {PUBLICATION_OPTIONS.map((o) => (
                <option key={o.value} value={o.value}>
                  {o.label}
                </option>
              ))}
            </select>
          </div>
          <p className="text-2xs text-brand-muted">
            {filteredItems.length} affiché{filteredItems.length !== 1 ? "s" : ""}
            {items.length !== filteredItems.length
              ? ` sur ${items.length} au total`
              : items.length > 0
                ? ""
                : ""}
          </p>
        </div>

        {/* Feed scrollable */}
        <div className="min-h-0 flex-1 overflow-y-auto overscroll-contain px-4 py-4 sm:px-5">
          {loading && (
            <p className="text-sm text-brand-muted">Chargement…</p>
          )}
          {err && <p className="text-sm text-red-700">{err}</p>}
          {!loading && !err && items.length === 0 && (
            <p className="text-sm text-brand-muted">
              Aucun contenu enregistré pour cette idée.
            </p>
          )}
          {!loading &&
            !err &&
            items.length > 0 &&
            filteredItems.length === 0 && (
              <p className="text-sm text-brand-muted">
                Aucun post ne correspond aux filtres. Modifiez la plateforme ou le
                statut de publication.
              </p>
            )}
          {!loading && !err && filteredItems.length > 0 && (
            <ul className="flex flex-col gap-4 pb-2">
              {filteredItems.map((row) => {
                const plat = PLATFORM_LABELS[row.platform] || row.platform;
                const st = STATUS_META[row.status] || STATUS_META.generated;
                const imgUrl = row.image_url ? String(row.image_url).trim() : "";
                const hasImage =
                  imgUrl &&
                  (imgUrl.startsWith("https://") || imgUrl.startsWith("http://"));
                return (
                  <li
                    key={row.id}
                    className="overflow-hidden rounded-2xl border border-brand-border bg-white shadow-sm"
                  >
                    {hasImage && (
                      <div className="relative w-full bg-brand-light/40">
                        <img
                          src={imgUrl}
                          alt=""
                          loading="lazy"
                          className="max-h-72 w-full object-cover sm:max-h-80"
                          onError={(e) => {
                            e.currentTarget.style.display = "none";
                          }}
                        />
                      </div>
                    )}
                    <div className="space-y-2 p-4">
                      <div className="flex flex-wrap items-center gap-2">
                        <span className="rounded-full bg-brand-light px-2.5 py-0.5 text-xs font-bold text-brand-dark">
                          {plat}
                        </span>
                        <span
                          className={`rounded-full px-2.5 py-0.5 text-2xs font-semibold ${st.className}`}
                        >
                          {st.label}
                        </span>
                        <span className="ml-auto text-2xs text-brand-muted">
                          {formatDate(row.created_at)}
                        </span>
                      </div>
                      <p className="whitespace-pre-wrap text-sm leading-relaxed text-brand-dark">
                        {row.caption || "—"}
                      </p>
                      {row.status === "published" && row.published_at && (
                        <p className="text-2xs text-emerald-800">
                          Publié le {formatDate(row.published_at)}
                        </p>
                      )}
                      {row.status === "publish_failed" && row.publish_error && (
                        <p className="rounded-lg bg-red-50 px-2 py-1.5 text-2xs text-red-800">
                          {row.publish_error}
                        </p>
                      )}
                    </div>
                  </li>
                );
              })}
            </ul>
          )}
        </div>

        <div className="flex shrink-0 justify-end border-t border-brand-border bg-[#FAFCFF] px-5 py-3">
          <Button type="button" variant="secondary" size="md" onClick={onClose}>
            Fermer
          </Button>
        </div>
      </div>
    </div>
  );
}
