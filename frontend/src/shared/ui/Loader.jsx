import React from "react";

export function Loader({ className = "" }) {
  return <div className={`inline-block h-6 w-6 animate-spin rounded-full border-2 border-[#7C3AED] border-t-transparent ${className}`} role="status" aria-label="Chargement" />;
}

export default Loader;
