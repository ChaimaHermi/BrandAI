export function normalizeArray(value) {
  return Array.isArray(value) ? value : [];
}

export function mapMarketReport(payload) {
  if (!payload) return null;

  // backend-api wraps final report into result_json.
  const report = payload.result_json || payload;
  const overview = report.overview || {};
  const tendances = report.tendances || {};
  const marketVoc = report.market_voc || {};
  const competitor = report.competitor || {};
  const swot = report.swot || {};

  return {
    executiveSummary: report.executive_summary || "",
    overview: {
      demande: overview.demande || {},
      probleme: overview.probleme || {},
      concurrence: overview.concurrence || {},
      tendance: overview.tendance || {},
    },
    tendances: {
      direction: tendances.direction || "-",
      signalStrength: tendances.signal_strength || "-",
      peakPeriod: tendances.peak_period || "-",
      risingQueries: normalizeArray(tendances.rising_queries),
      newsSignals: normalizeArray(tendances.news_signals),
      regulatoryBarriers: normalizeArray(tendances.regulatory_barriers),
      sectorContext: tendances.sector_context || "",
    },
    marketVoc: {
      demandLevel: marketVoc.demand_level || "-",
      demandSummary: marketVoc.demand_summary || "",
      topVoc: normalizeArray(marketVoc.top_voc),
      personas: normalizeArray(marketVoc.personas),
      macro: marketVoc.macro || {},
      newsSignals: normalizeArray(marketVoc.news_signals),
    },
    competitor: {
      topCompetitors: normalizeArray(competitor.top_competitors),
      opportunityLevel: competitor.opportunite_niveau || "-",
      opportunitySummary: competitor.opportunite_summary || "",
    },
    swot: {
      forces: normalizeArray(swot.forces),
      faiblesses: normalizeArray(swot.faiblesses),
      opportunites: normalizeArray(swot.opportunites),
      menaces: normalizeArray(swot.menaces),
    },
    risques: normalizeArray(report.risques),
    recommandations: normalizeArray(report.recommandations),
    dataQuality: report.data_quality || {},
    meta: report.meta || {},
  };
}

