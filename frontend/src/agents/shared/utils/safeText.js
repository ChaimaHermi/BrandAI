export function safeText(value, fallback = "") {
  if (value === null || value === undefined) return fallback;
  if (typeof value !== "string") return String(value);
  return value
    .replace(/\bundefined\b/g, "")
    .replace(/\s{2,}/g, " ")
    .trim() || fallback;
}

