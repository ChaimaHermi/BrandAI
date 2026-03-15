import React from "react";
import { Link } from "react-router-dom";
import { Button } from "../ui/Button";
import { UserAvatar } from "../ui/UserAvatar";
import { useAuth } from "../../hooks/useAuth";

export function Navbar({ variant = "landing" }) {
  const { user, logout } = useAuth();

  return (
    <header className="sticky top-0 z-50 border-b border-[#E5E7EB] bg-white/80 backdrop-blur-sm">
      <div className="mx-auto flex max-w-[1200px] items-center justify-between px-4 py-2 md:px-6">
        <Link to="/" className="flex items-center text-[#111827] transition-opacity hover:opacity-80">
          <img src="/logo%20brand%20ai.png" alt="BrandAI" className="h-9 w-auto object-contain" />
        </Link>
        {variant === "landing" ? (
          <nav className="flex items-center gap-2">
            <Link
              to="/login"
              className="inline-flex items-center justify-center gap-1.5 rounded-[8px] border border-[#E5E7EB] bg-white px-4 py-2 text-sm font-medium text-[#111827] transition-all duration-200 hover:border-[#7C3AED] hover:text-[#7C3AED]"
            >
              Se connecter
            </Link>
            <Link
              to="/register"
              className="inline-flex items-center justify-center gap-1.5 rounded-[8px] bg-[#7C3AED] px-4 py-2 text-sm font-medium text-white transition-all duration-200 hover:scale-[1.02] hover:bg-[#6D28D9] active:scale-[0.98]"
            >
              Commencer
            </Link>
          </nav>
        ) : (
          <nav className="flex items-center gap-3">
            <Link
              to="/dashboard"
              className="text-sm font-medium text-[#6B7280] transition-colors hover:text-[#7C3AED]"
            >
              Mes idées
            </Link>
            <Link to="/ideas/new">
              <Button variant="primary" className="px-3 py-1.5 text-sm">+ Nouvelle idée</Button>
            </Link>
            <div className="flex items-center gap-2 border-l border-[#E5E7EB] pl-3">
              <span className="hidden text-xs text-[#6B7280] sm:block">{user?.name}</span>
              <UserAvatar size={28} user={user} />
              <button type="button" onClick={logout} className="text-xs text-[#6B7280] transition-colors hover:text-[#7C3AED]">Déconnexion</button>
            </div>
          </nav>
        )}
      </div>
    </header>
  );
}

export default Navbar;
