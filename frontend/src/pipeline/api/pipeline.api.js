// Pipeline API stubs for BrandAI multi-agent pipeline.
// TODO: implement real backend calls when pipeline is wired.

/**
 * Trigger a full pipeline run for a given idea.
 * @param {string|number} ideaId
 * @param {object} options
 */
export async function runPipeline(ideaId, options = {}) {
  console.warn("[pipeline.api] runPipeline not implemented yet", {
    ideaId,
    options,
  });
  return {
    status: "not_implemented",
    ideaId,
  };
}

/**
 * Fetch the current pipeline status and results for a given idea.
 * @param {string|number} ideaId
 */
export async function getPipelineStatus(ideaId) {
  console.warn("[pipeline.api] getPipelineStatus not implemented yet", {
    ideaId,
  });
  return {
    status: "not_implemented",
    ideaId,
    results: null,
  };
}

