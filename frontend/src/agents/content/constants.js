/** Plateformes supportées — ids stables pour l’API */
export const PLATFORMS = {
  instagram: "instagram",
  facebook: "facebook",
  linkedin: "linkedin",
};

export const PLATFORM_ORDER = [PLATFORMS.instagram, PLATFORMS.facebook, PLATFORMS.linkedin];

export const PLATFORM_LABELS = {
  [PLATFORMS.instagram]: "Instagram",
  [PLATFORMS.facebook]: "Facebook",
  [PLATFORMS.linkedin]: "LinkedIn",
};

/** Tons — valeurs envoyées au backend */
export const TONE_OPTIONS = [
  { id: "friendly", label: "Friendly" },
  { id: "professional", label: "Professionnel" },
  { id: "inspiring", label: "Inspirant" },
  { id: "educational", label: "Éducatif" },
  { id: "bold", label: "Audacieux" },
];

/** Types de contenu (partagés ; le backend peut filtrer par plateforme) */
export const CONTENT_TYPE_OPTIONS = [
  { id: "feed_post", label: "Post fil d’actualité" },
  { id: "announcement", label: "Annonce" },
  { id: "tip", label: "Astuce / conseil" },
  { id: "story_style", label: "Style story (court)" },
  { id: "promotional", label: "Promotion" },
];

/** Call-to-action (Facebook & LinkedIn) */
export const CTA_OPTIONS = [
  { id: "learn_more", label: "En savoir plus" },
  { id: "sign_up", label: "S’inscrire" },
  { id: "download", label: "Télécharger" },
  { id: "contact", label: "Nous contacter" },
  { id: "book", label: "Réserver" },
  { id: "none", label: "Aucun" },
];

export const DEFAULT_TONE = {
  instagram: "friendly",
  facebook: "friendly",
  linkedin: "professional",
};
