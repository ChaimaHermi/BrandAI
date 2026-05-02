import { FiInfo } from "react-icons/fi";
import { Card } from "@/shared/ui/Card";
import { PLATFORMS } from "../constants";

const COLUMNS = [
  { key: "preview",      label: "Aperçu",       width: "min-w-[200px]" },
  { key: "platform",     label: "Plateforme",   width: "w-28" },
  { key: "likes",        label: "J'aime",       width: "w-20" },
  { key: "comments",     label: "Commentaires", width: "w-28" },
  { key: "reach",        label: "Portée",       width: "w-20" },
  { key: "published_at", label: "Date",         width: "w-28" },
];

function formatNum(n) {
  if (n === null || n === undefined) return "—";
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)} M`;
  if (n >= 1_000) return `${(n / 1_000).toFixed(1)} K`;
  return String(n);
}

function formatDate(str) {
  if (!str) return "—";
  try {
    return new Date(str).toLocaleDateString("fr-FR", {
      day: "2-digit", month: "short", year: "numeric",
    });
  } catch {
    return str;
  }
}

function SkeletonRow() {
  return (
    <tr>
      {COLUMNS.map((col) => (
        <td key={col.key} className="px-4 py-3">
          <div
            className="h-3 animate-pulse rounded-md bg-brand-light/60"
            style={{ width: col.key === "preview" ? "80%" : "50%" }}
          />
        </td>
      ))}
    </tr>
  );
}

function PlatformBadge({ platformKey }) {
  const p = PLATFORMS[platformKey];
  if (!p) return <span className="text-ink-subtle">—</span>;
  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full border px-2 py-0.5 text-[11px] font-semibold ${p.lightBg} ${p.border} ${p.lightText}`}
    >
      <span
        className="flex h-4 w-4 shrink-0 items-center justify-center rounded-full text-white"
        style={{ background: p.color }}
      >
        <p.Icon className="h-2 w-2" />
      </span>
      {p.label}
    </span>
  );
}

/**
 * @param {{
 *   posts: import('../types/optimizer.types').TopPost[],
 *   loading: boolean
 * }} props
 */
export function TopPostsTable({ posts, loading }) {
  const isEmpty = !loading && (!posts || posts.length === 0);

  return (
    <Card padding="p-0" className="overflow-hidden">

      {/* Header */}
      <div className="flex items-center justify-between border-b border-brand-border bg-gradient-to-r from-brand-light/40 to-white px-5 py-3.5">
        <div className="flex items-start gap-3">
          <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-xl bg-brand-light">
            <svg className="h-4 w-4 text-brand" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <rect x="2" y="7" width="20" height="14" rx="2" />
              <path d="M16 3H8a2 2 0 0 0-2 2v2h12V5a2 2 0 0 0-2-2z" />
            </svg>
          </div>
          <div className="min-w-0 flex-1">
            <p className="text-sm font-bold text-ink">Top publications</p>
            <p className="text-2xs text-ink-muted">Posts les plus performants sur la période</p>
          </div>
        </div>

        {!loading && posts?.length > 0 && (
          <span className="rounded-full bg-brand-light px-2.5 py-1 text-2xs font-semibold text-brand-dark">
            {posts.length} post{posts.length > 1 ? "s" : ""}
          </span>
        )}
      </div>

      {/* Table */}
      <div className="overflow-x-auto">
        <table className="w-full border-collapse">
          <thead>
            <tr className="border-b border-brand-border bg-brand-light/20">
              {COLUMNS.map((col) => (
                <th
                  key={col.key}
                  className={`${col.width} px-4 py-2.5 text-left text-2xs font-bold uppercase tracking-wider text-ink-muted`}
                >
                  {col.label}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-brand-border/50">
            {loading && Array.from({ length: 4 }).map((_, i) => <SkeletonRow key={i} />)}

            {isEmpty && (
              <tr>
                <td colSpan={COLUMNS.length} className="px-4 py-10 text-center">
                  <div className="flex flex-col items-center gap-2">
                    <FiInfo className="h-6 w-6 text-ink-muted/30" />
                    <p className="text-xs text-ink-muted">
                      Aucune publication disponible pour cette plateforme
                    </p>
                  </div>
                </td>
              </tr>
            )}

            {!loading && posts?.map((post) => (
              <tr
                key={post.id}
                className="bg-white transition-colors hover:bg-brand-light/10"
              >
                <td className="px-4 py-3 text-xs text-ink">
                  <span className="line-clamp-2 max-w-xs">{post.preview || "—"}</span>
                </td>
                <td className="px-4 py-3">
                  <PlatformBadge platformKey={post.platform} />
                </td>
                <td className="px-4 py-3 text-xs font-semibold text-ink-muted">
                  {formatNum(post.likes)}
                </td>
                <td className="px-4 py-3 text-xs font-semibold text-ink-muted">
                  {formatNum(post.comments)}
                </td>
                <td className="px-4 py-3 text-xs font-semibold text-ink-muted">
                  {formatNum(post.reach)}
                </td>
                <td className="px-4 py-3 text-2xs text-ink-subtle">
                  {formatDate(post.published_at)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

    </Card>
  );
}

export default TopPostsTable;
