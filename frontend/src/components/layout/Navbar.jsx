import React from "react";
import { Link } from "react-router-dom";
import { UserAvatar } from "../ui/UserAvatar";
import { useAuth } from "@/shared/hooks/useAuth";
import { useNotifications } from "@/hooks/useNotificationsSSE";
import NotificationBell from "@/components/NotificationBell";

/**
 * Navbar — shared top navigation bar.
 *
 * variant="landing" → public nav (login + register CTAs)
 * variant="app"     → authenticated nav (new idea + user info + logout)
 */
export function Navbar({ variant = "landing" }) {
  const { user, token, logout } = useAuth();
  const notifications = useNotifications(variant === "app" ? token : null);

  return (
    <header className="fixed left-0 top-0 z-50 h-16 w-full border-b border-brand-border bg-white/90 shadow-topbar backdrop-blur-md">
      <div className="mx-auto flex h-full max-w-7xl items-center justify-between px-6">

        {/* Logo */}
        <Link
          to={variant === "landing" ? "/" : "/dashboard"}
          className="flex items-center gap-2"
        >
          <img
            src="/logo%20brand%20ai.png"
            alt="BrandAI"
            className="h-8 w-auto object-contain"
          />
        </Link>

        {variant === "landing" ? (
          /* ── Landing nav ────────────────────────────────────────────── */
          <nav className="flex items-center gap-2">
            <Link
              to="/login"
              className="inline-flex items-center justify-center rounded-full border border-brand-border bg-white px-4 py-1.5 text-sm font-semibold text-ink-body transition-all hover:border-brand-muted hover:text-brand"
            >
              Se connecter
            </Link>
            <Link
              to="/register"
              className="inline-flex items-center justify-center rounded-full bg-gradient-to-br from-brand to-brand-dark px-4 py-1.5 text-sm font-semibold text-white shadow-btn transition-all hover:shadow-btn-hover hover:-translate-y-px"
            >
              Commencer
            </Link>
          </nav>
        ) : (
          /* ── App nav ────────────────────────────────────────────────── */
          <nav className="flex flex-1 items-center justify-end gap-4">
            {/* Breadcrumb pill */}
            <div className="hidden md:flex flex-1 items-center justify-center">
              <div className="inline-flex items-center gap-2 rounded-full border border-brand-border bg-white px-3 py-1 text-xs text-ink-subtle">
                <span className="font-semibold uppercase tracking-widest text-brand-muted">Dashboard</span>
                <span className="text-gray-300">/</span>
                <Link to="/dashboard" className="font-semibold text-brand-dark hover:text-brand">
                  Mes idées
                </Link>
              </div>
            </div>

            {/* Right actions */}
            <div className="flex items-center gap-3">
              <Link
                to="/ideas/new"
                className="inline-flex items-center gap-1.5 rounded-full bg-gradient-to-br from-brand to-brand-dark px-4 py-1.5 text-xs font-bold text-white shadow-btn transition-all hover:shadow-btn-hover hover:-translate-y-px"
              >
                <span className="flex h-4 w-4 items-center justify-center rounded-full bg-white/20 text-xs font-bold">+</span>
                Nouvelle idée
              </Link>

              {variant === "app" && (
                <NotificationBell
                  items={notifications.items}
                  unreadCount={notifications.unreadCount}
                  onMarkRead={notifications.markRead}
                  onMarkAllRead={notifications.markAllRead}
                />
              )}

              <div className="flex items-center gap-2">
                <div className="hidden md:flex flex-col items-end">
                  <span className="text-xs font-semibold text-ink leading-tight">
                    {user?.name || "Utilisateur"}
                  </span>
                  <span className="max-w-[160px] truncate text-2xs text-ink-subtle leading-tight">
                    {user?.email}
                  </span>
                </div>
                <UserAvatar size={28} user={user} />
                <button
                  type="button"
                  onClick={logout}
                  className="inline-flex items-center rounded-full border border-red-200 bg-red-50 px-2.5 py-1 text-xs font-semibold text-red-600 transition-colors hover:bg-red-100"
                >
                  Déconnexion
                </button>
              </div>
            </div>
          </nav>
        )}
      </div>
    </header>
  );
}

export default Navbar;
