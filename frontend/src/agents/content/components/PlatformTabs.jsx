import { FaInstagram, FaFacebookF, FaLinkedinIn } from "react-icons/fa";
import { PLATFORM_ORDER, PLATFORM_LABELS } from "../constants";

const ICONS = {
  instagram: FaInstagram,
  facebook:  FaFacebookF,
  linkedin:  FaLinkedinIn,
};

const PLATFORM_STYLE = {
  instagram: {
    active: {
      style: { background: "linear-gradient(135deg,#833AB4,#E1306C,#FCB045)", borderColor: "transparent" },
      className: "border-transparent text-white shadow-md scale-[1.03]",
    },
    inactive: {
      style: {
        background: "linear-gradient(135deg,rgba(131,58,180,.08),rgba(225,48,108,.08),rgba(252,176,69,.08))",
        borderColor: "rgba(225,48,108,.35)",
        color: "#C2185B",
      },
      className: "hover:scale-[1.02]",
    },
  },
  facebook: {
    active: {
      style: { background: "#1877F2", borderColor: "#1877F2" },
      className: "text-white shadow-md scale-[1.03]",
    },
    inactive: {
      style: {
        background: "rgba(24,119,242,.07)",
        borderColor: "rgba(24,119,242,.35)",
        color: "#1877F2",
      },
      className: "hover:scale-[1.02]",
    },
  },
  linkedin: {
    active: {
      style: { background: "#0A66C2", borderColor: "#0A66C2" },
      className: "text-white shadow-md scale-[1.03]",
    },
    inactive: {
      style: {
        background: "rgba(10,102,194,.07)",
        borderColor: "rgba(10,102,194,.35)",
        color: "#0A66C2",
      },
      className: "hover:scale-[1.02]",
    },
  },
};

export function PlatformTabs({ activePlatform, onSelect }) {
  return (
    <div className="flex flex-wrap gap-2" role="tablist" aria-label="Plateforme de publication">
      {PLATFORM_ORDER.map((id) => {
        const Icon    = ICONS[id];
        const active  = activePlatform === id;
        const ps      = PLATFORM_STYLE[id];
        const variant = active ? ps.active : ps.inactive;

        return (
          <button
            key={id}
            type="button"
            role="tab"
            aria-selected={active}
            id={`platform-tab-${id}`}
            onClick={() => onSelect(id)}
            style={variant.style}
            className={`flex items-center gap-2 rounded-full border px-4 py-2 text-xs font-semibold transition-all duration-200 ${variant.className}`}
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
