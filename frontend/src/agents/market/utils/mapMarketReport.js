function asObject(value) {
  return value && typeof value === "object" ? value : {};
}

export function mapMarketReport(input) {
  const raw = asObject(input);
  const overview = asObject(raw.overview);
  const market = asObject(raw.market);
  const competitor = asObject(raw.competitor);
  const voc = asObject(raw.voc);
  const trends = asObject(raw.trends);
  const strategy = asObject(raw.strategy);

  return {
    raw,
    meta: {
      generatedAt: raw.generated_at || null,
      sourceCount: Array.isArray(raw.sources) ? raw.sources.length : 0,
    },
    overview: overview,
    market,
    competitor,
    voc,
    trends,
    strategy,
    sources: Array.isArray(raw.sources) ? raw.sources : [],
  };
}
