import React from "react";
import { HiOutlineLightBulb, HiOutlineMagnifyingGlass, HiOutlinePaintBrush, HiOutlineDocumentText, HiOutlineGlobeAlt, HiOutlineChartBarSquare, HiOutlineCheckCircle, HiOutlineClock } from "react-icons/hi2";
import { Badge } from "../ui/Badge";

const ICON_MAP = { idea: HiOutlineLightBulb, market: HiOutlineMagnifyingGlass, brand: HiOutlinePaintBrush, content: HiOutlineDocumentText, website: HiOutlineGlobeAlt, optimizer: HiOutlineChartBarSquare };

export function AgentCard({ agent, status, isActive, onClick }) {
  const Icon = ICON_MAP[agent.icon] || HiOutlineLightBulb;

  const baseClass = "flex w-full items-center gap-2.5 rounded-[8px] border p-2.5 text-left transition-all duration-200";
  const statusClasses = {
    done: "border-l-[3px] border-l-[#7C3AED] bg-[#F5F3FF] border-[#E5E7EB]",
    running: "border-[1.5px] border-[#7C3AED] bg-white",
    waiting: "bg-[#F9FAFB] border-[#E5E7EB] opacity-50",
  };
  const activeClass = isActive ? "ring-1 ring-[#7C3AED]" : "";

  return (
    <button
      type="button"
      onClick={onClick}
      className={`${baseClass} ${statusClasses[status]} ${activeClass} hover:border-[#A78BFA]`}
    >
      <span
        className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-md ${
          status === "done" ? "bg-[#DDD6FE] text-[#7C3AED]" : status === "running" ? "bg-[#7C3AED]/10 text-[#7C3AED]" : "bg-[#E5E7EB] text-[#9CA3AF]"
        }`}
      >
        {status === "done" ? <HiOutlineCheckCircle className="h-4 w-4" /> : <Icon className="h-4 w-4" />}
      </span>
      <div className="min-w-0 flex-1">
        <p className="text-sm font-medium text-[#111827]">{agent.name}</p>
        <div className="mt-0.5">
          {status === "done" && <Badge variant="success" className="text-[10px]">Terminé</Badge>}
          {status === "running" && <Badge variant="violet" className="text-[10px]">En cours</Badge>}
          {status === "waiting" && (
            <span className="flex items-center gap-0.5 text-[11px] text-[#9CA3AF]">
              <HiOutlineClock className="h-3 w-3" /> En attente
            </span>
          )}
        </div>
      </div>
    </button>
  );
}

export default AgentCard;
