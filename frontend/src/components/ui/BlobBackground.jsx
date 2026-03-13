import React from "react";

/**
 * Aurora-style blob background. Use only in:
 * - Landing hero (opacity 0.40, inside hero section)
 * - Login / Register full page (opacity 0.35, pointer-events-none z-0)
 */
export function BlobBackground({ opacity = 0.35, className = "" }) {
  return (
    <div
      className={`absolute inset-0 overflow-hidden ${className}`}
      style={{ filter: "blur(120px)", opacity }}
      aria-hidden
    >
      {/* Blob 1 violet */}
      <div
        className="absolute h-[600px] w-[600px]"
        style={{
          top: "-150px",
          left: "-150px",
          background: "radial-gradient(circle, #c4b5fd 0%, #8b5cf6 40%, transparent 70%)",
          animation: "blobFloat1 12s ease-in-out infinite",
        }}
      />
      {/* Blob 2 pink */}
      <div
        className="absolute h-[500px] w-[500px]"
        style={{
          top: "-100px",
          right: "-150px",
          background: "radial-gradient(circle, #fbcfe8 0%, #f472b6 40%, transparent 70%)",
          animation: "blobFloat2 15s ease-in-out infinite",
        }}
      />
      {/* Blob 3 blue */}
      <div
        className="absolute h-[400px] w-[400px]"
        style={{
          bottom: "-100px",
          left: "30%",
          background: "radial-gradient(circle, #bfdbfe 0%, #93c5fd 40%, transparent 70%)",
          animation: "blobFloat3 10s ease-in-out infinite",
        }}
      />
    </div>
  );
}

export default BlobBackground;
