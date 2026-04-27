import { useCallback, useEffect, useRef, useState } from "react";
import {
  FiBell,
  FiCheck,
  FiCheckCircle,
  FiAlertTriangle,
  FiClock,
  FiX,
} from "react-icons/fi";

const TYPE_META = {
  publication_succeeded: {
    icon: FiCheckCircle,
    color: "text-emerald-500",
    bg: "bg-emerald-50",
    border: "border-emerald-200",
  },
  publication_failed: {
    icon: FiAlertTriangle,
    color: "text-red-500",
    bg: "bg-red-50",
    border: "border-red-200",
  },
  publication_upcoming: {
    icon: FiClock,
    color: "text-amber-500",
    bg: "bg-amber-50",
    border: "border-amber-200",
  },
  website_deployed: {
    icon: FiCheckCircle,
    color: "text-emerald-500",
    bg: "bg-emerald-50",
    border: "border-emerald-200",
  },
};

const PLATFORM_COLOR = {
  linkedin: "#0A66C2",
  facebook: "#1877F2",
  instagram: "#E4405F",
  website: "#7C3AED",
};

function timeAgo(iso) {
  if (!iso) return "";
  const diff = (Date.now() - new Date(iso).getTime()) / 1000;
  if (diff < 60) return "à l'instant";
  if (diff < 3600) return `il y a ${Math.floor(diff / 60)} min`;
  if (diff < 86400) return `il y a ${Math.floor(diff / 3600)}h`;
  return `il y a ${Math.floor(diff / 86400)}j`;
}

function NotificationItem({ item, onMarkRead }) {
  const meta = TYPE_META[item.type] || TYPE_META.publication_upcoming;
  const Icon = meta.icon;
  const platformColor = PLATFORM_COLOR[item.platform] || "#7C3AED";

  return (
    <div
      className={`flex gap-3 rounded-xl border px-3.5 py-3 transition-all ${
        item.is_read
          ? "border-gray-100 bg-white opacity-70"
          : `${meta.border} ${meta.bg}`
      }`}
    >
      <div
        className={`mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-full ${
          item.is_read ? "bg-gray-100" : meta.bg
        }`}
      >
        <Icon size={15} className={item.is_read ? "text-gray-400" : meta.color} />
      </div>

      <div className="min-w-0 flex-1">
        <div className="flex items-start justify-between gap-2">
          <p className="text-[13px] font-semibold leading-tight text-gray-800">
            {item.title}
          </p>
          {item.platform && (
            <span
              className="shrink-0 rounded-full px-2 py-0.5 text-[10px] font-bold uppercase text-white"
              style={{ background: platformColor }}
            >
              {item.platform}
            </span>
          )}
        </div>

        <p className="mt-0.5 text-[12px] leading-snug text-gray-500">
          {item.message}
        </p>

        <div className="mt-1.5 flex items-center justify-between">
          <span className="text-[10px] text-gray-400">
            {timeAgo(item.created_at)}
          </span>
          {!item.is_read && (
            <button
              type="button"
              onClick={() => onMarkRead(item.id)}
              className="flex items-center gap-1 rounded-md px-1.5 py-0.5 text-[10px] font-medium text-gray-400 transition-colors hover:bg-white hover:text-gray-600"
            >
              <FiCheck size={10} /> Lu
            </button>
          )}
        </div>
      </div>
    </div>
  );
}

export default function NotificationBell({
  items = [],
  unreadCount = 0,
  onMarkRead,
  onMarkAllRead,
}) {
  const [open, setOpen] = useState(false);
  const ref = useRef(null);

  const handleClickOutside = useCallback((e) => {
    if (ref.current && !ref.current.contains(e.target)) setOpen(false);
  }, []);

  useEffect(() => {
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, [handleClickOutside]);

  return (
    <div ref={ref} className="relative">
      {/* Bell button */}
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        className={`relative flex h-[34px] w-[34px] items-center justify-center rounded-xl border transition-all ${
          open
            ? "border-brand bg-brand-light"
            : "border-brand-border bg-white hover:bg-brand-light"
        }`}
        aria-label="Notifications"
      >
        <FiBell size={16} className="text-brand" />
        {unreadCount > 0 && (
          <span className="absolute -right-1 -top-1 flex h-[18px] min-w-[18px] items-center justify-center rounded-full bg-red-500 px-1 text-[10px] font-bold text-white shadow-sm">
            {unreadCount > 99 ? "99+" : unreadCount}
          </span>
        )}
      </button>

      {/* Dropdown panel */}
      {open && (
        <div className="absolute right-0 top-[calc(100%+8px)] z-50 w-[380px] overflow-hidden rounded-2xl border border-brand-border bg-white shadow-xl">
          {/* Header */}
          <div className="flex items-center justify-between border-b border-gray-100 px-4 py-3">
            <div className="flex items-center gap-2">
              <span className="text-sm font-bold text-gray-800">
                Notifications
              </span>
              {unreadCount > 0 && (
                <span className="rounded-full bg-brand-light px-2 py-0.5 text-[10px] font-bold text-brand">
                  {unreadCount} non lu{unreadCount > 1 ? "es" : "e"}
                </span>
              )}
            </div>
            <div className="flex items-center gap-1">
              {unreadCount > 0 && (
                <button
                  type="button"
                  onClick={onMarkAllRead}
                  className="rounded-lg px-2 py-1 text-[11px] font-semibold text-brand transition-colors hover:bg-brand-light"
                >
                  Tout marquer lu
                </button>
              )}
              <button
                type="button"
                onClick={() => setOpen(false)}
                className="flex h-6 w-6 items-center justify-center rounded-lg text-gray-400 transition-colors hover:bg-gray-100 hover:text-gray-600"
              >
                <FiX size={14} />
              </button>
            </div>
          </div>

          {/* List */}
          <div className="max-h-[400px] overflow-y-auto p-2">
            {items.length === 0 ? (
              <div className="flex flex-col items-center justify-center py-10 text-center">
                <div className="mb-2 flex h-12 w-12 items-center justify-center rounded-full bg-gray-50">
                  <FiBell size={20} className="text-gray-300" />
                </div>
                <p className="text-xs font-medium text-gray-400">
                  Aucune notification
                </p>
              </div>
            ) : (
              <div className="flex flex-col gap-1.5">
                {items.map((n) => (
                  <NotificationItem
                    key={n.id}
                    item={n}
                    onMarkRead={onMarkRead}
                  />
                ))}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
