function countItems(arr) {
  return Array.isArray(arr) ? arr.length : 0;
}

export default function MarketVOC({ voc }) {
  const painPoints = voc?.pain_points ?? [];
  const frustrations = voc?.frustrations ?? [];
  const desiredFeatures = voc?.desired_features ?? [];
  const userQuotes = voc?.user_quotes ?? [];
  const marketInsights = voc?.market_insights ?? [];
  const sources = voc?.sources ?? [];

  const hasSummary =
    countItems(painPoints) > 0 ||
    countItems(frustrations) > 0 ||
    countItems(desiredFeatures) > 0 ||
    countItems(userQuotes) > 0;

  const hasPainOrFrustrations =
    countItems(painPoints) > 0 || countItems(frustrations) > 0;
  const hasDesiredFeatures = countItems(desiredFeatures) > 0;
  const hasQuotesInsightsFr =
    countItems(userQuotes) > 0 ||
    countItems(marketInsights) > 0;
  const hasSources = countItems(sources) > 0;

  return (
    <div className="flex flex-col gap-4">
      {hasSummary && (
        <div className="grid grid-cols-4 gap-3">
          <div className="rounded-xl border border-gray-200 bg-white px-4 py-3">
            <div className="text-2xl font-bold text-violet-600">{countItems(painPoints)}</div>
            <div className="text-xs uppercase tracking-wide text-gray-400">Pain points</div>
          </div>
          <div className="rounded-xl border border-gray-200 bg-white px-4 py-3">
            <div className="text-2xl font-bold text-violet-600">{countItems(frustrations)}</div>
            <div className="text-xs uppercase tracking-wide text-gray-400">Frustrations</div>
          </div>
          <div className="rounded-xl border border-gray-200 bg-white px-4 py-3">
            <div className="text-2xl font-bold text-violet-600">
              {countItems(desiredFeatures)}
            </div>
            <div className="text-xs uppercase tracking-wide text-gray-400">
              Fonctionnalités souhaitées
            </div>
          </div>
          <div className="rounded-xl border border-gray-200 bg-white px-4 py-3">
            <div className="text-2xl font-bold text-violet-600">{countItems(userQuotes)}</div>
            <div className="text-xs uppercase tracking-wide text-gray-400">Verbatims</div>
          </div>
        </div>
      )}

      {hasPainOrFrustrations && (
        <div className="grid grid-cols-2 gap-4">
          {countItems(painPoints) > 0 && (
            <div className="rounded-2xl border border-gray-100 bg-white p-6 shadow-sm">
              <div className="mb-4 flex items-center gap-2 text-sm font-bold text-gray-800">
                Pain points
                <span className="rounded-full bg-gray-100 px-2 py-0.5 text-xs text-gray-500">
                  {countItems(painPoints)}
                </span>
              </div>
              {painPoints?.map((item, idx) => (
                <div
                  key={`${item}-${idx}`}
                  className="group flex gap-3 border-b border-gray-50 py-3 last:border-0 hover:border-l-2 hover:border-l-red-200 hover:pl-2"
                >
                  <span className="mt-2 h-2 w-2 flex-shrink-0 rounded-full bg-red-400" />
                  <p className="text-sm leading-relaxed text-gray-600">{item}</p>
                </div>
              ))}
            </div>
          )}

          {countItems(frustrations) > 0 && (
            <div className="rounded-2xl border border-gray-100 bg-white p-6 shadow-sm">
              <div className="mb-4 flex items-center gap-2 text-sm font-bold text-gray-800">
                Frustrations
                <span className="rounded-full bg-gray-100 px-2 py-0.5 text-xs text-gray-500">
                  {countItems(frustrations)}
                </span>
              </div>
              {frustrations?.map((item, idx) => (
                <div
                  key={`${item}-${idx}`}
                  className="group flex gap-3 border-b border-gray-50 py-3 last:border-0 hover:border-l-2 hover:border-l-amber-200 hover:pl-2"
                >
                  <span className="mt-2 h-2 w-2 flex-shrink-0 rounded-full bg-amber-400" />
                  <p className="text-sm leading-relaxed text-gray-600">{item}</p>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {hasDesiredFeatures && (
        <div className="rounded-2xl border border-gray-100 bg-white p-6 shadow-sm">
          <div className="mb-4 flex items-center gap-2 text-sm font-bold text-gray-800">
            Fonctionnalités souhaitées
            <span className="rounded-full bg-gray-100 px-2 py-0.5 text-xs text-gray-500">
              {countItems(desiredFeatures)}
            </span>
          </div>
          <div className="grid grid-cols-2 gap-3">
            {desiredFeatures?.map((feature, idx) => (
              <div
                key={`${feature}-${idx}`}
                className="flex items-start gap-2 rounded-xl border border-violet-100 bg-violet-50 px-4 py-3"
              >
                <span className="flex-shrink-0 font-bold text-violet-500">✓</span>
                <span className="text-sm text-gray-700">{feature}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {hasQuotesInsightsFr && (
        <div className="grid grid-cols-3 gap-4">
          {countItems(userQuotes) > 0 && (
            <div className="rounded-2xl border border-gray-100 bg-white p-6 shadow-sm">
              <div className="mb-4 flex items-center gap-2 text-sm font-bold text-gray-800">
                Verbatims utilisateurs
                <span className="rounded-full bg-gray-100 px-2 py-0.5 text-xs text-gray-500">
                  {countItems(userQuotes)}
                </span>
              </div>
              {userQuotes?.map((quote, idx) => (
                <div key={`${quote}-${idx}`} className="mb-4 border-l-4 border-violet-300 py-2 pl-4">
                  <div className="font-serif text-4xl leading-none text-violet-200">&quot;</div>
                  <p className="text-sm italic leading-relaxed text-gray-600">{quote}</p>
                </div>
              ))}
            </div>
          )}

          {countItems(marketInsights) > 0 && (
            <div className="rounded-2xl border border-gray-100 bg-white p-6 shadow-sm">
              <div className="mb-4 flex items-center gap-2 text-sm font-bold text-gray-800">
                Market insights
                <span className="rounded-full bg-gray-100 px-2 py-0.5 text-xs text-gray-500">
                  {countItems(marketInsights)}
                </span>
              </div>
              {marketInsights?.map((insight, idx) => (
                <div
                  key={`${insight}-${idx}`}
                  className="flex gap-3 border-b border-gray-50 py-3 last:border-0"
                >
                  <span className="flex h-6 w-6 flex-shrink-0 items-center justify-center rounded-full bg-violet-100 text-xs font-bold text-violet-600">
                    {idx + 1}
                  </span>
                  <p className="text-sm text-gray-600">{insight}</p>
                </div>
              ))}
            </div>
          )}

        </div>
      )}

      {hasSources && (
        <div className="rounded-2xl border border-gray-100 bg-white p-6 shadow-sm">
          <div className="mb-4 flex items-center gap-2 text-sm font-bold text-gray-800">
            Sources VOC
            <span className="rounded-full bg-gray-100 px-2 py-0.5 text-xs text-gray-500">
              {countItems(sources)}
            </span>
          </div>
          <div className="grid grid-cols-1 gap-2">
            {sources.map((s, idx) => {
              const source = typeof s?.source === "string" ? s.source : "web";
              const url = typeof s?.url === "string" ? s.url : "";
              if (!url) return null;
              return (
                <a
                  key={`${source}-${url}-${idx}`}
                  href={url}
                  target="_blank"
                  rel="noreferrer"
                  className="flex items-center justify-between rounded-lg border border-gray-100 px-3 py-2 text-sm text-gray-700 hover:bg-gray-50"
                >
                  <span className="font-medium uppercase tracking-wide text-gray-500">{source}</span>
                  <span className="ml-4 truncate text-violet-700">{url}</span>
                </a>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
