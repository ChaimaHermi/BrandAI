import { PLATFORM_ORDER, PLATFORMS } from "../constants";

/**
 * Tabs de plateforme — même pattern que PlatformTabs.jsx du Content Creator.
 * @param {{ activePlatform: string, onPlatformChange: (p: string) => void }} props
 */
export function PlatformNav({ activePlatform, onPlatformChange }) {
  return (
    <div className="flex flex-wrap gap-2" role="tablist" aria-label="Plateforme d'analyse">
      {PLATFORM_ORDER.map((key) => {
        const p = PLATFORMS[key];
        const active = activePlatform === key;
        const variant = active ? p.activeStyle : p.inactiveStyle;

        return (
          <button
            key={key}
            type="button"
            role="tab"
            aria-selected={active}
            onClick={() => onPlatformChange(key)}
            style={variant}
            className={`flex items-center gap-2 rounded-full border px-4 py-2 text-xs font-semibold transition-all duration-200 ${
              active ? "text-white shadow-md scale-[1.03]" : "hover:scale-[1.02]"
            }`}
          >
            <p.Icon className="h-3.5 w-3.5 shrink-0" aria-hidden />
            {p.label}
          </button>
        );
      })}
    </div>
  );
}

export default PlatformNav;
