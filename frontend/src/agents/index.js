export const AGENTS = [
  { id: "clarifier", label: "Idea Clarifier", color: "#7F77DD", order: 0 },
  { id: "enhancer", label: "Idea Enhancer", color: "#1D9E75", order: 1 },
  { id: "market", label: "Market Analysis", color: "#378ADD", order: 2 },
  { id: "brand", label: "Brand Identity", color: "#D4537E", order: 3 },
  { id: "content", label: "Content Creator", color: "#D85A30", order: 4 },
  { id: "website", label: "Website Builder", color: "#378ADD", order: 5 },
];

export const getAgent = (id) => AGENTS.find((a) => a.id === id);

