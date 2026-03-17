import React, { useState } from "react";
import { Link } from "react-router-dom";
import {
  HiOutlineArrowRight,
  HiOutlineCalendar,
  HiOutlineTrash,
} from "react-icons/hi2";
import { Badge } from "../../shared/ui/Badge";
import { STATUS_BADGE, formatIdeaDate } from "./constants";

/**
 * Table: Idea name | Sector | Status | Created date | Action
 */
export function IdeasTable({ ideas, onDelete }) {
  const [deletingId, setDeletingId] = useState(null);
  const handleDeleteClick = async (idea) => {
    if (!onDelete) return;
    if (!window.confirm(`Supprimer l'idée « ${idea.name || "sans nom"} » ?`))
      return;
    setDeletingId(idea.id);
    try {
      await onDelete(idea.id);
    } finally {
      setDeletingId(null);
    }
  };
  return (
    <div className="overflow-x-auto rounded-[10px] border border-[#E5E7EB] bg-white">
      <table className="w-full min-w-[600px] border-collapse text-left text-sm">
        <thead>
          <tr className="border-b border-[#E5E7EB] bg-[#F9FAFB]">
            <th className="px-4 py-3 font-semibold text-[#6B7280]">
              Nom de l&apos;idée
            </th>
            <th className="px-4 py-3 font-semibold text-[#6B7280]">Secteur</th>
            <th className="px-4 py-3 font-semibold text-[#6B7280]">Statut</th>
            <th className="px-4 py-3 font-semibold text-[#6B7280]">
              Date de création
            </th>
            <th className="px-4 py-3 font-semibold text-[#6B7280] text-right">
              Action
            </th>
          </tr>
        </thead>
        <tbody>
          {ideas.map((idea) => {
            const statusConf =
              STATUS_BADGE[idea.status] || STATUS_BADGE.pending;
            const isRunning = idea.status === "running";
            const actionLabel =
              idea.status === "pending"
                ? "Affiner"
                : idea.status === "running"
                  ? "Voir le pipeline"
                  : "Voir les résultats";
            return (
              <tr
                key={idea.id}
                className="border-b border-[#E5E7EB] transition-colors last:border-b-0 hover:bg-[#FAFAFA]"
              >
                <td className="px-4 py-3">
                  <Link
                    to={`/ideas/${idea.id}`}
                    className="font-medium text-[#111827] hover:text-[#7C3AED]"
                  >
                    {idea.name || "—"}
                  </Link>
                </td>
                <td className="px-4 py-3 text-[#6B7280]">
                  {idea.sector || "—"}
                </td>
                <td className="px-4 py-3">
                  <Badge
                    variant={statusConf.variant}
                    className={
                      isRunning ? "inline-flex items-center gap-1" : ""
                    }
                  >
                    {isRunning && (
                      <span
                        className="inline-block h-1.5 w-1.5 animate-pulse rounded-full bg-current"
                        aria-hidden
                      />
                    )}
                    {statusConf.label}
                  </Badge>
                </td>
                <td className="px-4 py-3 text-[#6B7280]">
                  <span className="inline-flex items-center gap-1">
                    <HiOutlineCalendar
                      className="h-3.5 w-3.5 shrink-0"
                      aria-hidden
                    />
                    {formatIdeaDate(idea.created_at)}
                  </span>
                </td>
                <td className="px-4 py-3 text-right">
                  <div className="inline-flex items-center gap-2">
                    <Link
                      to={`/ideas/${idea.id}`}
                      className="inline-flex items-center gap-1 text-sm font-medium text-[#7C3AED] hover:underline"
                    >
                      {actionLabel}
                      <HiOutlineArrowRight className="h-4 w-4" />
                    </Link>
                    {onDelete && (
                      <button
                        type="button"
                        onClick={() => handleDeleteClick(idea)}
                        disabled={deletingId === idea.id}
                        className="inline-flex items-center justify-center rounded-lg p-1.5 text-[#6B7280] hover:bg-red-50 hover:text-red-600 transition-colors disabled:opacity-50"
                        title="Supprimer l'idée"
                        aria-label="Supprimer l'idée"
                      >
                        <HiOutlineTrash className="h-4 w-4" />
                      </button>
                    )}
                  </div>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

export default IdeasTable;
