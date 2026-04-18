import { FiDatabase, FiSettings, FiEdit3, FiCamera, FiImage } from "react-icons/fi";

/**
 * Metadata for each ReAct agent tool — used to display human-friendly step labels.
 */
export const TOOL_META = {
  merge_context: {
    label: "Chargement du contexte",
    description: "Brief + données projet",
    Icon: FiDatabase,
  },
  get_platform_spec: {
    label: "Spécifications plateforme",
    description: "Formats et contraintes",
    Icon: FiSettings,
  },
  draft_post: {
    label: "Rédaction du post",
    description: "Génération via LLM",
    Icon: FiEdit3,
  },
  build_image_prompt: {
    label: "Prompt image",
    description: "Construction du prompt",
    Icon: FiCamera,
  },
  image_client: {
    label: "Génération de l'image",
    description: "Création et upload",
    Icon: FiImage,
  },
};

/** Always shown in the progress stepper, even before they start. */
export const GUARANTEED_TOOLS = ["merge_context", "get_platform_spec", "draft_post"];

/** Shown only once the agent actually invokes them. */
export const OPTIONAL_TOOLS = ["build_image_prompt", "image_client"];
