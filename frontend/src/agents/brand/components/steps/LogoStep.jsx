import SectionHeader from "../SectionHeader";
import {
  LOGO_STYLE_OPTIONS,
  LOGO_TYPE_OPTIONS,
} from "../../constants/brandFormOptions";

export default function LogoStep({ logoStyle, logoType, onLogoStyle, onLogoType }) {
  return (
    <div className="bi-fade-up">
      <SectionHeader
        step={5}
        title="Direction logo"
        sub="Style et format pour guider la création ou la génération du logo."
      />

      <p className="bi-lbl">Style</p>
      <div className="mb-6 grid grid-cols-2 gap-2.5 sm:grid-cols-4">
        {LOGO_STYLE_OPTIONS.map((s) => (
          <button
            key={s}
            type="button"
            onClick={() => onLogoStyle(s)}
            className={`bi-name-card bi-card py-3.5 text-center ${
              logoStyle === s
                ? "border-[#6366f1] bg-[#eef2ff]"
                : "border-[#e5e7eb]"
            }`}
          >
            <span
              className={`text-[13px] font-semibold ${
                logoStyle === s ? "text-[#4f46e5]" : "text-[#374151]"
              }`}
            >
              {s}
            </span>
          </button>
        ))}
      </div>

      <p className="bi-lbl">Format</p>
      <div className="grid grid-cols-2 gap-2.5 sm:grid-cols-4">
        {LOGO_TYPE_OPTIONS.map((t) => (
          <button
            key={t}
            type="button"
            onClick={() => onLogoType(t)}
            className={`bi-name-card bi-card py-3.5 text-center ${
              logoType === t ? "border-[#6366f1] bg-[#eef2ff]" : "border-[#e5e7eb]"
            }`}
          >
            <span
              className={`text-[13px] font-semibold ${
                logoType === t ? "text-[#4f46e5]" : "text-[#374151]"
              }`}
            >
              {t}
            </span>
          </button>
        ))}
      </div>
    </div>
  );
}
