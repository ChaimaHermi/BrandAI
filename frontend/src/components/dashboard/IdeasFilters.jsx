import React from "react";
import { HiOutlineMagnifyingGlass } from "react-icons/hi2";

const STATUS_OPTIONS = [
  { value: "", label: "Tous les statuts" },
  { value: "pending", label: "En attente" },
  { value: "running", label: "En cours" },
  { value: "done", label: "Terminé" },
  { value: "error", label: "Erreur" },
];

/**
 * Search + status filter for ideas list
 */
export function IdeasFilters({ search, onSearchChange, statusFilter, onStatusFilterChange }) {
  return (
    <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
      <div className="relative flex-1">
        <HiOutlineMagnifyingGlass
          className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-[#9CA3AF]"
          aria-hidden
        />
        <input
          type="search"
          value={search}
          onChange={(e) => onSearchChange(e.target.value)}
          placeholder="Rechercher par nom ou secteur..."
          className="w-full rounded-[10px] border border-[#E5E7EB] bg-white py-2 pl-9 pr-4 text-sm text-[#111827] placeholder:text-[#9CA3AF] focus:border-[#7C3AED] focus:outline-none focus:ring-1 focus:ring-[#7C3AED]"
          aria-label="Rechercher"
        />
      </div>
      <select
        value={statusFilter}
        onChange={(e) => onStatusFilterChange(e.target.value)}
        className="w-full rounded-[10px] border border-[#E5E7EB] bg-white px-4 py-2 text-sm text-[#111827] focus:border-[#7C3AED] focus:outline-none focus:ring-1 focus:ring-[#7C3AED] sm:w-auto"
        aria-label="Filtrer par statut"
      >
        {STATUS_OPTIONS.map((opt) => (
          <option key={opt.value || "all"} value={opt.value}>
            {opt.label}
          </option>
        ))}
      </select>
    </div>
  );
}

export default IdeasFilters;
