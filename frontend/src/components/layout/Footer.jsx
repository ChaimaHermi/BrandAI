import React from "react";
import { Link } from "react-router-dom";
import { HiOutlineBolt } from "react-icons/hi2";

export function Footer() {
  return (
    <footer className="border-t border-[#E5E7EB] bg-white py-8">
      <div className="mx-auto max-w-[1200px] px-4 md:px-6">
        <div className="flex flex-col items-center justify-between gap-6 md:flex-row md:items-center">
          <div className="flex items-center gap-2">
            <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-[#7C3AED]/10 text-[#7C3AED]">
              <HiOutlineBolt className="h-4 w-4" />
            </span>
            <Link to="/" className="font-semibold text-[#111827] hover:text-[#7C3AED]">
              BrandAI
            </Link>
            <span className="text-[#6B7280]">·</span>
            <span className="text-sm text-[#6B7280]">From idea to market.</span>
          </div>
          <nav className="flex flex-wrap items-center justify-center gap-4 text-sm text-[#6B7280]">
            <Link to="/" className="hover:text-[#7C3AED]">Produit</Link>
            <span className="text-[#E5E7EB]">·</span>
            <Link to="/" className="hover:text-[#7C3AED]">Agents</Link>
            <span className="text-[#E5E7EB]">·</span>
            <Link to="/login" className="hover:text-[#7C3AED]">Connexion</Link>
            <span className="text-[#E5E7EB]">·</span>
            <Link to="/" className="hover:text-[#7C3AED]">Contact</Link>
          </nav>
          <div className="text-center text-sm text-[#6B7280] md:text-right">
            <p>© 2026 Chaima Hermi · TALAN · PFE 2026 · BrandAI</p>
            <p className="mt-0.5 text-xs text-[#9CA3AF]">All rights reserved.</p>
          </div>
        </div>
      </div>
    </footer>
  );
}

export default Footer;
