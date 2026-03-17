import React from "react";
import { Link } from "react-router-dom";
import { Button } from "../ui/Button";
import { UserAvatar } from "../ui/UserAvatar";
import { useAuth } from "@/shared/hooks/useAuth";

export function Navbar({ variant = "landing" }) {
  const { user, logout } = useAuth();

  return (
    <header className="fixed top-0 left-0 z-50 h-16 w-full bg-white/80 backdrop-blur-md shadow-sm border-b border-gray-200">
      <div className="mx-auto flex h-full max-w-7xl items-center justify-between px-6">
        {/* LEFT: Logo */}
        <Link
          to={variant === "landing" ? "/" : "/dashboard"}
          className="flex items-center gap-2 text-[#111827]"
        >
          <img
            src="/logo%20brand%20ai.png"
            alt="BrandAI"
            className="h-8 w-auto object-contain"
          />
        </Link>

        {variant === "landing" ? (
          /* Landing navbar */
          <nav className="flex items-center gap-2">
            <Link
              to="/login"
              className="inline-flex items-center justify-center gap-1.5 rounded-full border border-[#E5E7EB] bg-white px-4 py-1.5 text-sm font-medium text-[#111827] transition-all duration-200 hover:border-[#7F77DD] hover:text-[#7F77DD]"
            >
              Se connecter
            </Link>
            <Link
              to="/register"
              className="inline-flex items-center justify-center gap-1.5 rounded-full bg-[#7F77DD] px-4 py-1.5 text-sm font-medium text-white shadow-sm transition-all duration-200 hover:scale-[1.02] hover:bg-[#6D28D9] active:scale-[0.98]"
            >
              Commencer
            </Link>
          </nav>
        ) : (
          /* App / dashboard navbar */
          <nav className="flex flex-1 items-center justify-end gap-4">
            {/* CENTER: breadcrumb (hidden on very small screens) */}
            <div className="hidden md:flex flex-1 items-center justify-center">
              <div className="inline-flex items-center gap-2 rounded-full border border-[#ECE7FF] bg-white px-3 py-1 text-[11px] text-[#6B7280]">
                <span className="uppercase tracking-[0.14em] text-[#9CA3AF]">
                  Dashboard
                </span>
                <span className="text-[#D1D5DB]">/</span>
                <Link
                  to="/dashboard"
                  className="font-semibold text-[#534AB7] hover:text-[#7F77DD]"
                >
                  Mes idées
                </Link>
              </div>
            </div>

            {/* RIGHT: CTA + user */}
            <div className="flex items-center gap-3">
              <Link to="/ideas/new">
                <Button
                  variant="primary"
                  className="flex items-center gap-1.5 rounded-full bg-gradient-to-r from-[#7F77DD] to-[#534AB7] px-4 py-1.5 text-xs font-semibold shadow-sm hover:shadow-md"
                >
                  <span className="flex h-4 w-4 items-center justify-center rounded-full bg-white/20 text-[11px]">
                    +
                  </span>
                  Nouvelle idée
                </Button>
              </Link>

              <div className="flex items-center gap-2">
                <div className="hidden md:flex flex-col items-end">
                  <span className="text-[11px] font-medium text-[#111827] leading-tight">
                    {user?.name || "Utilisateur"}
                  </span>
                  <span className="text-[10px] text-[#9CA3AF] leading-tight truncate max-w-[180px]">
                    {user?.email}
                  </span>
                </div>
                <UserAvatar size={28} user={user} />
                <button
                  type="button"
                  onClick={logout}
                  className="inline-flex items-center rounded-full border border-[#FECACA] bg-[#FFF5F5] px-2.5 py-1 text-[10px] font-semibold text-[#DC2626] hover:bg-[#FEE2E2] transition-colors"
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
