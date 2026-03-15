export const STATUS_BADGE = {
  pending: { variant: "waiting", label: "En attente" },
  running: { variant: "violet", label: "En cours" },
  done: { variant: "success", label: "Terminé" },
  error: { variant: "danger", label: "Erreur" },
};

export function formatIdeaDate(d) {
  if (!d) return "—";
  const date = typeof d === "string" ? new Date(d) : d;
  return date.toLocaleDateString("fr-FR", {
    day: "numeric",
    month: "short",
    year: "numeric",
  });
}
