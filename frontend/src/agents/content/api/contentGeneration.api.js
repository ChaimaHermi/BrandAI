/**
 * Content generation — backend-ai (LLM réel). Pas de données mock.
 */

const AI_URL =
  import.meta.env.VITE_AI_URL || "http://localhost:8001/api/ai";

/**
 * Délai client pour POST /content/generate.
 * - Non défini ou vide : **aucune limite** (attente jusqu’à la réponse du serveur).
 * - Nombre > 0 : abort après N millisecondes (ex. 120000 = 2 min).
 * - 0 : traité comme illimité.
 */
function getContentGenerateTimeoutMs() {
  const raw = import.meta.env.VITE_CONTENT_GENERATE_TIMEOUT_MS;
  if (raw === undefined || raw === "") return null;
  const n = Number(raw);
  if (!Number.isFinite(n) || n <= 0) return null;
  return n;
}

/**
 * @param {object} payload — retour de buildGenerationPayload
 * @param {string | null} accessToken — JWT (Authorization Bearer)
 * @returns {Promise<{ caption: string, image_url: string | null, char_count: number, platform: string }>}
 */
export async function postContentGeneration(payload, accessToken) {
  if (!payload?.idea_id) {
    throw new Error("idea_id requis");
  }

  const headers = { "Content-Type": "application/json" };
  if (accessToken) {
    headers.Authorization = `Bearer ${accessToken}`;
  }

  const controller = new AbortController();
  const timeoutMs = getContentGenerateTimeoutMs();
  const tid =
    timeoutMs != null
      ? setTimeout(() => controller.abort(), timeoutMs)
      : null;

  const body = {
    ...payload,
    ...(accessToken ? { access_token: accessToken } : {}),
  };

  let res;
  try {
    res = await fetch(`${AI_URL}/content/generate`, {
      method: "POST",
      headers,
      signal: controller.signal,
      body: JSON.stringify(body),
    });
  } catch (e) {
    if (e?.name === "AbortError") {
      if (timeoutMs != null) {
        throw new Error(
          `Délai dépassé (${Math.round(timeoutMs / 1000)} s). Vérifiez que backend-ai est démarré.`,
        );
      }
      throw new Error("Requête annulée.");
    }
    throw e;
  } finally {
    if (tid != null) clearTimeout(tid);
  }

  const data = await res.json().catch(() => ({}));

  if (!res.ok) {
    const detail =
      typeof data?.detail === "string"
        ? data.detail
        : Array.isArray(data?.detail)
          ? data.detail.map((x) => x?.msg || JSON.stringify(x)).join("; ")
          : typeof data?.message === "string"
            ? data.message
            : null;
    throw new Error(detail || `Génération échouée (${res.status})`);
  }

  return {
    caption: data.caption,
    image_url: data.image_url ?? null,
    char_count: data.char_count ?? (data.caption || "").length,
    platform: data.platform,
  };
}
