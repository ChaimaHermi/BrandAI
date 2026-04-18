const SOFT_LIMITS = {
  instagram: 2200,
  facebook:  63206,
  linkedin:  3000,
};

export function CharacterCount({ text, platform }) {
  const n   = (text || "").length;
  const max = SOFT_LIMITS[platform] ?? 2200;
  const pct = Math.min((n / max) * 100, 100);

  const isOver   = n > max;
  const isWarn   = !isOver && pct >= 80;

  const barColor = isOver  ? "bg-red-500"
                 : isWarn  ? "bg-amber-400"
                 : "bg-brand";

  const textColor = isOver ? "text-red-600 font-semibold"
                  : isWarn ? "text-amber-700 font-semibold"
                  : "text-ink-muted";

  return (
    <div className="space-y-1">
      <div className="flex items-center justify-between text-[11px]">
        <span className="text-ink-subtle">Caractères</span>
        <span className={textColor}>
          {n.toLocaleString("fr-FR")} / {max.toLocaleString("fr-FR")}
        </span>
      </div>
      <div className="h-1 w-full rounded-full bg-brand-border">
        <div
          className={`h-1 rounded-full transition-all duration-300 ${barColor}`}
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  );
}

export default CharacterCount;
