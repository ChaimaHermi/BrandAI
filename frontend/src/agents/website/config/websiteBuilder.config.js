export const WEBSITE_BUILDER_ENDPOINTS = {
  aiBaseUrl: import.meta.env.VITE_AI_URL || "http://localhost:8001/api/ai",
  apiBaseUrl: import.meta.env.VITE_API_URL || "http://localhost:8000/api",
};

export const WEBSITE_BUILDER_TIMEOUTS_MS = {
  default: 25000,
  context: 45000,
  description: 90000,
  generation: 320000,
  /** Révision LLM (chat) — peut dépasser 3 min sur gros HTML. */
  revision: 300000,
  deploy: 240000,
  save: 30000,
};
