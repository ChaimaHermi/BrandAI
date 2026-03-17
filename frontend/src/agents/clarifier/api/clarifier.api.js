const AI_URL = import.meta.env.VITE_AI_URL || "http://localhost:8001/api/ai";

export const clarifierApi = {
  startUrl: () => `${AI_URL}/clarifier/start`,
  answerUrl: () => `${AI_URL}/clarifier/answer`,
};

