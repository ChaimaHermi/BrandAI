import { PLATFORM_LABELS } from "../../constants";

/** Limites indicatives — à synchroniser avec get_platform_spec côté backend */
const SOFT_LIMITS = {
  instagram: 2200,
  facebook: 63206,
  linkedin: 3000,
};

export function CharacterCount({ text, platform }) {
  const n = (text || "").length;
  const max = SOFT_LIMITS[platform] ?? 2200;
  const label = PLATFORM_LABELS[platform] || platform;

  return (
    <div className="flex items-center justify-between text-[11px] text-ink-subtle">
      <span>Caractères ({label})</span>
      <span className={n > max ? "font-semibold text-red-600" : "text-ink-muted"}>
        {n} / ~{max.toLocaleString("fr-FR")}
      </span>
    </div>
  );
}

export default CharacterCount;
