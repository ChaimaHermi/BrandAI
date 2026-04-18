/**
 * API Content Generation — backend-ai (à brancher).
 * Pour l’instant : mock local pour le développement UI.
 */

const MOCK_DELAY_MS = 900;

function mockCaption(platform, subject) {
  const s = (subject || "Votre sujet").trim();
  const base =
    platform === "linkedin"
      ? `Nous sommes ravis de partager une actualité autour de : ${s}. ` +
        "Découvrez comment notre approche répond aux enjeux de votre secteur. " +
        "Qu’en pensez-vous ?"
      : platform === "facebook"
        ? `✨ ${s}\n\n` +
          "Une nouvelle étape pour notre communauté. Merci pour votre soutien — " +
          "dites-nous ce que vous aimeriez voir ensuite en commentaire ! 👇"
        : `✨ ${s}\n\n` +
          "Swipez pour en voir plus — lien en bio. " +
          "#brand #inspiration #nouveauté";

  return base;
}

function mockImageUrl() {
  return "https://picsum.photos/seed/content-preview/1080/1080";
}

/**
 * @param {object} payload — retour de buildGenerationPayload
 * @param {string} accessToken — Bearer (optionnel pour mock)
 * @returns {Promise<{ caption: string, image_url: string | null, char_count: number, platform: string }>}
 */
export async function postContentGeneration(payload, accessToken) {
  void accessToken;
  await new Promise((r) => setTimeout(r, MOCK_DELAY_MS));

  const platform = payload.platform || "instagram";
  const caption = mockCaption(platform, payload.brief?.subject);
  const inc = payload.brief?.include_image;
  const include =
    platform === "instagram"
      ? inc !== false
      : inc === true;

  return {
    caption,
    image_url: include ? mockImageUrl() : null,
    char_count: caption.length,
    platform,
    mock: true,
  };
}
