import { PLATFORMS, DEFAULT_TONE } from "./constants";

/** État initial par plateforme — champs distincts selon le brief produit */

export function initialInstagramForm() {
  return {
    subject: "",
    tone: DEFAULT_TONE[PLATFORMS.instagram],
    contentType: "feed_post",
    hashtagsEnabled: true,
    includeImage: true,
  };
}

export function initialFacebookForm() {
  return {
    subject: "",
    tone: DEFAULT_TONE[PLATFORMS.facebook],
    contentType: "feed_post",
    callToAction: "learn_more",
    includeImage: true,
  };
}

export function initialLinkedInForm() {
  return {
    subject: "",
    tone: DEFAULT_TONE[PLATFORMS.linkedin],
    contentType: "feed_post",
    callToAction: "learn_more",
    includeImage: true,
  };
}

export function getInitialFormForPlatform(platform) {
  switch (platform) {
    case PLATFORMS.instagram:
      return initialInstagramForm();
    case PLATFORMS.facebook:
      return initialFacebookForm();
    case PLATFORMS.linkedin:
      return initialLinkedInForm();
    default:
      return initialInstagramForm();
  }
}

/**
 * Payload unifié pour l’API content generation (backend-ai).
 * Champs absents selon plateforme → null ou omis.
 * @param {{ alignWithProject?: boolean, previousCaption?: string, regenerationInstruction?: string }} [options]
 */
export function buildGenerationPayload(ideaId, platform, formValues, options = {}) {
  const alignWithProject =
    options.alignWithProject !== undefined ? options.alignWithProject : true;
  const brief = {
    subject: (formValues.subject || "").trim(),
    tone: formValues.tone,
    content_type: formValues.contentType,
    align_with_project: Boolean(alignWithProject),
  };

  if (platform === PLATFORMS.instagram) {
    brief.hashtags = formValues.hashtagsEnabled;
    brief.include_image = formValues.includeImage;
    brief.call_to_action = null;
  } else if (platform === PLATFORMS.facebook) {
    brief.hashtags = null;
    brief.include_image = formValues.includeImage;
    brief.call_to_action = formValues.callToAction;
  } else if (platform === PLATFORMS.linkedin) {
    brief.hashtags = false;
    brief.include_image = formValues.includeImage;
    brief.call_to_action = formValues.callToAction;
  }

  const previousCaption = (options.previousCaption || "").trim();
  const regenerationInstruction = (options.regenerationInstruction || "").trim();

  return {
    idea_id: ideaId,
    platform,
    brief,
    ...(previousCaption
      ? { previous_caption: previousCaption }
      : {}),
    ...(regenerationInstruction
      ? { regeneration_instruction: regenerationInstruction }
      : {}),
  };
}
