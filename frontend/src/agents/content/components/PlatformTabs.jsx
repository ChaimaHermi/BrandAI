import { FaInstagram, FaFacebookF, FaLinkedinIn } from "react-icons/fa";
import { PLATFORM_ORDER, PLATFORM_LABELS } from "../constants";

const ICONS = {
  instagram: FaInstagram,
  facebook: FaFacebookF,
  linkedin: FaLinkedinIn,
};

export function PlatformTabs({ activePlatform, onSelect }) {
  return (
    <div
      className="flex flex-wrap gap-2"
      role="tablist"
      aria-label="Plateforme de publication"
    >
      {PLATFORM_ORDER.map((id) => {
        const Icon = ICONS[id];
        const active = activePlatform === id;
        return (
          <button
            key={id}
            type="button"
            role="tab"
            aria-selected={active}
            id={`platform-tab-${id}`}
            onClick={() => onSelect(id)}
            className={`flex items-center gap-1.5 rounded-full border px-4 py-1.5 text-xs font-semibold transition-all duration-150 ${
              active
                ? "border-brand bg-gradient-to-br from-brand to-brand-dark text-white shadow-btn"
                : "border-brand-border bg-white text-ink-muted hover:border-brand-muted hover:text-brand-dark"
            }`}
          >
            <Icon className="h-3.5 w-3.5 shrink-0" aria-hidden />
            {PLATFORM_LABELS[id]}
          </button>
        );
      })}
    </div>
  );
}

export default PlatformTabs;
