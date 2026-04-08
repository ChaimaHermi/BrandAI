const AVATAR_STYLES = [
  "bg-violet-100 text-violet-700",
  "bg-blue-100 text-blue-700",
  "bg-emerald-100 text-emerald-700",
  "bg-amber-100 text-amber-700",
  "bg-rose-100 text-rose-700",
];

function hasText(value) {
  return typeof value === "string" && value.trim().length > 0;
}

function hasArray(value) {
  return Array.isArray(value) && value.length > 0;
}

function normalizeExternalUrl(url) {
  if (!hasText(url)) return null;
  const trimmed = url.trim();
  if (/^https?:\/\//i.test(trimmed)) return trimmed;
  return `https://${trimmed}`;
}

export default function MarketCompetitors({ competitors }) {
  const list = Array.isArray(competitors) ? competitors : [];

  const total = list.length;
  const direct = list.filter((c) => c?.type === "direct").length;
  const indirect = list.filter((c) => c?.type === "indirect").length;
  const local = list.filter((c) => c?.scope === "local").length;
  const global = list.filter((c) => c?.scope === "global").length;

  return (
    <div className="bg-gray-50 p-4">
      <div className="mb-4 flex flex-wrap gap-2">
        <div className="rounded-lg border border-gray-200 bg-white px-4 py-2 text-sm">
          Total competitors: {total}
        </div>
        <div className="rounded-lg border border-gray-200 bg-white px-4 py-2 text-sm">
          Direct: {direct}
        </div>
        <div className="rounded-lg border border-gray-200 bg-white px-4 py-2 text-sm">
          Indirect: {indirect}
        </div>
        <div className="rounded-lg border border-gray-200 bg-white px-4 py-2 text-sm">
          Local: {local}
        </div>
        <div className="rounded-lg border border-gray-200 bg-white px-4 py-2 text-sm">
          Global: {global}
        </div>
      </div>

      {list.map((competitor, index) => {
        const avatarClass = AVATAR_STYLES[index % AVATAR_STYLES.length];
        const name = competitor?.name ?? "";
        const firstLetter = hasText(name) ? name.trim().charAt(0).toUpperCase() : "?";
        const type = competitor?.type ?? "";
        const scope = competitor?.scope ?? "";
        const website = competitor?.website;
        const websiteHref = normalizeExternalUrl(website);

        return (
          <div
            key={`${name}-${index}`}
            className="mb-4 rounded-2xl border border-gray-100 bg-white p-6 shadow-sm"
          >
            <div className="flex flex-wrap items-start justify-between gap-4">
              <div className="flex items-start gap-3">
                <div
                  className={`flex h-10 w-10 items-center justify-center rounded-full text-sm font-bold ${avatarClass}`}
                >
                  {firstLetter}
                </div>
                <div>
                  <div className="text-lg font-bold text-gray-900">{name}</div>
                  {hasText(website) && websiteHref && (
                    <a
                      href={websiteHref}
                      target="_blank"
                      rel="noreferrer"
                      className="text-sm text-violet-600 hover:underline"
                    >
                      {website}
                    </a>
                  )}
                </div>
              </div>

              <div className="flex flex-wrap gap-2">
                {hasText(type) && (
                  <span
                    className={
                      type === "direct"
                        ? "rounded-full bg-violet-100 px-2 py-0.5 text-xs font-semibold text-violet-700"
                        : "rounded-full bg-gray-100 px-2 py-0.5 text-xs font-semibold text-gray-600"
                    }
                  >
                    {type}
                  </span>
                )}
                {hasText(scope) && (
                  <span
                    className={
                      scope === "local"
                        ? "rounded-full bg-blue-100 px-2 py-0.5 text-xs font-semibold text-blue-700"
                        : "rounded-full bg-emerald-100 px-2 py-0.5 text-xs font-semibold text-emerald-700"
                    }
                  >
                    {scope}
                  </span>
                )}
              </div>
            </div>

            <div className="mt-4 space-y-3">
              {hasText(competitor?.description) && (
                <p className="text-sm leading-relaxed text-gray-700">
                  {competitor?.description}
                </p>
              )}

              {hasText(competitor?.positioning) && (
                <div>
                  <div className="mb-1 text-xs font-bold uppercase tracking-wider text-gray-400">
                    Positionnement
                  </div>
                  <p className="text-sm text-gray-700">{competitor?.positioning}</p>
                </div>
              )}

              {hasText(competitor?.target_users) && (
                <div>
                  <div className="mb-1 text-xs font-bold uppercase tracking-wider text-gray-400">
                    Utilisateurs cibles
                  </div>
                  <p className="text-sm text-gray-700">{competitor?.target_users}</p>
                </div>
              )}
            </div>

            {(hasArray(competitor?.key_features) ||
              hasArray(competitor?.strengths) ||
              hasArray(competitor?.weaknesses)) && (
              <div className="mt-4 grid grid-cols-3 gap-4">
                {hasArray(competitor?.key_features) && (
                  <div>
                    <div className="mb-2 text-xs font-bold uppercase tracking-wider text-gray-400">
                      Fonctionnalités
                    </div>
                    <ul className="space-y-1 text-sm text-gray-700">
                      {competitor?.key_features?.map((item, i) => (
                        <li key={`${item}-${i}`} className="flex items-start gap-2">
                          <span className="mt-1 text-gray-400">•</span>
                          <span>{item}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {hasArray(competitor?.strengths) && (
                  <div>
                    <div className="mb-2 text-xs font-bold uppercase tracking-wider text-gray-400">
                      Forces
                    </div>
                    <ul className="space-y-1 text-sm text-gray-700">
                      {competitor?.strengths?.map((item, i) => (
                        <li key={`${item}-${i}`} className="flex items-start gap-2">
                          <span className="mt-1 text-emerald-600">•</span>
                          <span>{item}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {hasArray(competitor?.weaknesses) && (
                  <div>
                    <div className="mb-2 text-xs font-bold uppercase tracking-wider text-gray-400">
                      Faiblesses
                    </div>
                    <ul className="space-y-1 text-sm text-gray-700">
                      {competitor?.weaknesses?.map((item, i) => (
                        <li key={`${item}-${i}`} className="flex items-start gap-2">
                          <span className="mt-1 text-red-500">•</span>
                          <span>{item}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            )}

            {(hasText(competitor?.differentiation) ||
              hasText(competitor?.pricing) ||
              hasText(competitor?.business_model)) && (
              <div className="mt-4">
                {hasText(competitor?.differentiation) && (
                  <p className="mt-3 border-l-2 border-violet-200 pl-3 text-sm italic text-gray-500">
                    <span className="font-semibold not-italic">Différenciation</span>:{" "}
                    {competitor?.differentiation}
                  </p>
                )}

                <div className="mt-3 flex flex-wrap gap-4 text-sm text-gray-700">
                  {hasText(competitor?.pricing) && (
                    <div>
                      <span className="font-semibold">Pricing</span>: {competitor?.pricing}
                    </div>
                  )}
                  {hasText(competitor?.business_model) && (
                    <div>
                      <span className="font-semibold">Modèle</span>:{" "}
                      {competitor?.business_model}
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}
