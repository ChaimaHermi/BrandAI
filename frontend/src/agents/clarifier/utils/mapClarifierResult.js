export function mapClarifierToSections(clarified) {
  return {
    what: clarified?.solution_description ?? "",
    who: clarified?.target_users ?? "",
    problem: clarified?.problem ?? "",
    pitch: clarified?.short_pitch ?? "",
  };
}

export function mapClarifierToSteps(data) {
  return {
    status: data.status ?? "info",
    message: data.message ?? "",
    dimensions: data.dimensions ?? null,
    sector: data.sector ?? null,
    confidence: data.confidence ?? null,
    score: data.score ?? null,
    model: data.model ?? null,
    elapsed_ms: data.elapsed_ms ?? null,
  };
}

