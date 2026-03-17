const AI_URL = import.meta.env.VITE_AI_URL || "http://localhost:8001/api/ai";
const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000/api";

export const clarifierApi = {
  startUrl: () => `${AI_URL}/clarifier/start`,
  answerUrl: () => `${AI_URL}/clarifier/answer`,
};

/**
 * Sauvegarde le résultat du Clarifier (clarified / refused / questions) en base.
 * @param {number} ideaId
 * @param {object} data - clarity_status, clarity_score, clarity_questions, etc.
 * @param {string} token - JWT
 * @returns {Promise<{ success: boolean, idea_id: number } | null>}
 */
export async function saveClarifierResult(ideaId, data, token) {
  try {
    const res = await fetch(
      `${API_URL}/ideas/${ideaId}/clarifier-result`,
      {
        method: "PATCH",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify(data),
      },
    );
    if (!res.ok) {
      console.error("[clarifier] save failed", res.status);
      return null;
    }
    return res.json();
  } catch (err) {
    console.error("[clarifier] save error", err);
    return null;
  }
}

