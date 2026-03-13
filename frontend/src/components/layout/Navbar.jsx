import React from "react";
import { Link } from "react-router-dom";
import { HiOutlineBolt } from "react-icons/hi2";
import { Button } from "../ui/Button";
import { UserAvatar } from "../ui/UserAvatar";
import { useAuth } from "../../hooks/useAuth";

export function Navbar({ variant = "landing" }) {
  const { user, logout } = useAuth();

  return (
    <header className="sticky top-0 z-50 border-b border-[#E5E7EB] bg-white/80 backdrop-blur-sm">
      <div className="mx-auto flex max-w-[1200px] items-center justify-between px-4 py-4 md:px-6">
        <Link to="/" className="flex items-center gap-2 text-[#111827] transition-colors hover:text-[#7C3AED]">
          <span className="flex h-9 w-9 items-center justify-center rounded-lg bg-[#7C3AED]/10 text-[#7C3AED]"><HiOutlineBolt className="h-5 w-5" /></span>
          <span className="font-semibold">BrandAI</span>
        </Link>
        {variant === "landing" ? (
          <nav className="flex items-center gap-3">
            <Link
              to="/login"
              className="inline-flex items-center justify-center gap-2 rounded-[10px] border border-[#E5E7EB] bg-white px-5 py-2.5 font-medium text-[#111827] transition-all duration-200 hover:border-[#7C3AED] hover:text-[#7C3AED]"
            >
              Se connecter
            </Link>
            <Link
              to="/register"
              className="inline-flex items-center justify-center gap-2 rounded-[10px] bg-[#7C3AED] px-5 py-2.5 font-medium text-white transition-all duration-200 hover:scale-[1.02] hover:bg-[#6D28D9] active:scale-[0.98]"
            >
              Commencer
            </Link>
          </nav>
        ) : (
          <nav className="flex items-center gap-4">
            <Link to="/projects/new"><Button variant="primary">+ Nouveau projet</Button></Link>
            <div className="flex items-center gap-3 border-l border-[#E5E7EB] pl-4">
              <span className="hidden text-sm text-[#6B7280] sm:block">{user?.name}</span>
              <UserAvatar size={32} user={user} />
              <button type="button" onClick={logout} className="text-sm text-[#6B7280] transition-colors hover:text-[#7C3AED]">Déconnexion</button>
            </div>
          </nav>
        )}
      </div>
    </header>
  );
}

export default Navbar;
