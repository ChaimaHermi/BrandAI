import { Link } from "react-router-dom";

export function Footer() {
  return (
    <footer className="border-t border-brand-border bg-white py-8">
      <div className="mx-auto max-w-6xl px-4 md:px-6">
        <div className="flex flex-col items-center justify-between gap-6 md:flex-row">

          {/* Logo + tagline */}
          <div className="flex items-center gap-2.5">
            <Link to="/" className="flex items-center transition-opacity hover:opacity-80">
              <img src="/logo%20brand%20ai.png" alt="BrandAI" className="h-8 w-auto object-contain" />
            </Link>
            <span className="text-brand-muted">·</span>
            <span className="text-sm text-ink-muted">From idea to market.</span>
          </div>

          {/* Nav links */}
          <nav className="flex flex-wrap items-center justify-center gap-1 text-sm text-ink-muted">
            {[
              { to: "/",         label: "Produit"  },
              { to: "/",         label: "Agents"   },
              { to: "/login",    label: "Connexion"},
              { to: "/privacy",  label: "Confidentialité" },
            ].map(({ to, label }, i, arr) => (
              <span key={label} className="flex items-center gap-1">
                <Link to={to} className="px-1 transition-colors hover:text-brand">
                  {label}
                </Link>
                {i < arr.length - 1 && <span className="text-brand-border">·</span>}
              </span>
            ))}
          </nav>

          {/* Copyright */}
          <div className="text-center text-sm text-ink-muted md:text-right">
            <p>© 2026 Chaima Hermi · TALAN · PFE 2026 · BrandAI</p>
            <p className="mt-0.5 text-xs text-ink-subtle">All rights reserved.</p>
          </div>

        </div>
      </div>
    </footer>
  );
}

export default Footer;
