const AI_URL = import.meta.env.VITE_AI_URL || "http://localhost:8001/api/ai";
const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000/api";

export const marketApi = {
  streamUrl: () => `${AI_URL}/pipeline/stream`,
  marketOnlyStreamUrl: () => `${AI_URL}/market-analysis/stream`,
  latestUrl: (ideaId) => `${API_URL}/market-analysis/${ideaId}/latest`,
};

export async function getLatestMarketAnalysis(ideaId, token) {
  const res = await fetch(marketApi.latestUrl(ideaId), {
    method: "GET",
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });

  if (res.status === 404) return null;
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`Erreur lecture market latest (${res.status}): ${text}`);
  }

  return res.json();
}

