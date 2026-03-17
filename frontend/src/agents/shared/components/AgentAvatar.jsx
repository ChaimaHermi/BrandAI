import React from "react";
import {
  HiOutlineMagnifyingGlassCircle,
  HiOutlineSparkles,
  HiOutlineChartBar,
  HiOutlinePaintBrush,
  HiOutlineDocumentText,
  HiOutlineGlobeAlt,
  HiOutlineAdjustmentsHorizontal,
} from "react-icons/hi2";

const agentConfig = {
  idea_clarifier: {
    label: "Idea Clarifier Agent",
    gradient: "from-[#7C3AED] to-[#4F46E5]",
    Icon: HiOutlineMagnifyingGlassCircle,
  },
  idea_enhancer: {
    label: "Idea Enhancer Agent",
    gradient: "from-[#059669] to-[#0891B2]",
    Icon: HiOutlineSparkles,
  },
  market_analysis: {
    label: "Market Analysis Agent",
    gradient: "from-[#2563EB] to-[#0891B2]",
    Icon: HiOutlineChartBar,
  },
  brand_identity: {
    label: "Brand Identity Agent",
    gradient: "from-[#DB2777] to-[#EA580C]",
    Icon: HiOutlinePaintBrush,
  },
  content_creator: {
    label: "Content Creator Agent",
    gradient: "from-[#D97706] to-[#CA8A04]",
    Icon: HiOutlineDocumentText,
  },
  website_builder: {
    label: "Website Builder Agent",
    gradient: "from-[#0EA5E9] to-[#6366F1]",
    Icon: HiOutlineGlobeAlt,
  },
  optimizer: {
    label: "Optimizer Agent",
    gradient: "from-[#6D28D9] to-[#22C55E]",
    Icon: HiOutlineAdjustmentsHorizontal,
  },
};

export function AgentAvatar({ agentType = "idea_clarifier", size = 32 }) {
  const config = agentConfig[agentType] || agentConfig.idea_clarifier;
  const { Icon } = config;

  return (
    <div
      className={`inline-flex items-center justify-center rounded-full bg-gradient-to-br ${config.gradient} text-white shadow-sm`}
      style={{ width: size, height: size }}
    >
      <Icon className="h-[60%] w-[60%]" aria-hidden />
    </div>
  );
}

export function getAgentMeta(agentType = "idea_clarifier") {
  const cfg = agentConfig[agentType] || agentConfig.idea_clarifier;
  return { label: cfg.label, gradient: cfg.gradient };
}

export default AgentAvatar;

