import React from "react";

/**
 * Single fixed aurora blob layer per page. No per-section blobs.
 * position: fixed, inset: 0, z-index: 0, blur(120px).
 * @param {number} opacity - Max 0.25 landing, 0.18 others, 0.15 Results
 */
export function AuroraBackground({ opacity = 0.2 }) {
  return (
    <div
      className="pointer-events-none fixed inset-0 overflow-hidden"
      style={{ zIndex: 0 }}
      aria-hidden
    >
      <div
        className="absolute inset-0 aurora-blob-inner"
        style={{ filter: "blur(120px)", opacity }}
      >
        <div
          className="absolute rounded-full aurora-blob aurora-blob-1"
          style={{
            background: "radial-gradient(circle, #c4b5fd 0%, #8b5cf6 40%, transparent 70%)",
            top: "-200px",
            left: "-200px",
            width: "700px",
            height: "700px",
            animation: "blobFloat1 12s ease-in-out infinite",
          }}
        />
        <div
          className="absolute rounded-full aurora-blob aurora-blob-2"
          style={{
            background: "radial-gradient(circle, #fbcfe8 0%, #f472b6 40%, transparent 70%)",
            top: "-150px",
            right: "-200px",
            width: "600px",
            height: "600px",
            animation: "blobFloat2 15s ease-in-out infinite",
          }}
        />
        <div
          className="absolute rounded-full aurora-blob aurora-blob-3"
          style={{
            background: "radial-gradient(circle, #bfdbfe 0%, #93c5fd 40%, transparent 70%)",
            bottom: "-150px",
            left: "30%",
            width: "500px",
            height: "500px",
            animation: "blobFloat3 10s ease-in-out infinite",
          }}
        />
      </div>
    </div>
  );
}

export default AuroraBackground;
