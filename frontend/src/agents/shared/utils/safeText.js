export function safeText(value, fallback = "") {
  if (value === null || value === undefined) return fallback;
  const str = typeof value === "string" ? value : String(value);
  return (
    str
      .replace(/:\s*undefined\b/g, "")
      .replace(/\bundefined\b/g, "")
      .replace(/:\s*null\b/g, "")
      .replace(/\s{2,}/g, " ")
      .trim() || fallback
  );
}

