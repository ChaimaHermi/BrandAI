const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000/api";

export const marketingApi = {
  latestUrl: (ideaId) => `${API_URL}/marketing-plans/${ideaId}/latest`,
};

export async function getLatestMarketingPlan(ideaId, token) {
  const res = await fetch(marketingApi.latestUrl(ideaId), {
    method: "GET",
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });

  if (res.status === 404) return null;
  if (res.status === 204) return null;
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`Erreur lecture marketing latest (${res.status}): ${text}`);
  }

  return res.json();
}
