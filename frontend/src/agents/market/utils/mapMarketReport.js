function asObject(value) {
  return value && typeof value === "object" ? value : {};
}

function pickObject(...candidates) {
  for (const candidate of candidates) {
    if (candidate && typeof candidate === "object" && !Array.isArray(candidate)) {
      return candidate;
    }
  }
  return {};
}

export function mapMarketReport(input) {
  const raw = asObject(input);
  const normalizedRoot = pickObject(raw.market_analysis, raw.result_json, raw);
  const overview = asObject(normalizedRoot.overview);
  const market = asObject(normalizedRoot.market);
  const competitor = asObject(normalizedRoot.competitor);
  const voc = asObject(normalizedRoot.voc);
  const trends = asObject(normalizedRoot.trends);
  const strategy = asObject(normalizedRoot.strategy);

  return {
    raw: normalizedRoot,
    meta: {
      generatedAt: normalizedRoot.generated_at || raw.generated_at || null,
      sourceCount: Array.isArray(normalizedRoot.sources)
        ? normalizedRoot.sources.length
        : Array.isArray(raw.sources)
          ? raw.sources.length
          : 0,
    },
    overview: overview,
    market,
    competitor,
    voc,
    trends,
    strategy,
    sources: Array.isArray(normalizedRoot.sources)
      ? normalizedRoot.sources
      : Array.isArray(raw.sources)
        ? raw.sources
        : [],
  };
}
