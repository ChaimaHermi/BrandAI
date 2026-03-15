import React from "react";

const ROWS = 10;

/**
 * Loading skeleton for ideas table
 */
export function IdeasTableSkeleton() {
  return (
    <div className="overflow-x-auto rounded-[10px] border border-[#E5E7EB] bg-white">
      <table className="w-full min-w-[600px] border-collapse text-left text-sm">
        <thead>
          <tr className="border-b border-[#E5E7EB] bg-[#F9FAFB]">
            <th className="px-4 py-3 font-semibold text-[#6B7280]">Nom de l&apos;idée</th>
            <th className="px-4 py-3 font-semibold text-[#6B7280]">Secteur</th>
            <th className="px-4 py-3 font-semibold text-[#6B7280]">Statut</th>
            <th className="px-4 py-3 font-semibold text-[#6B7280]">Date de création</th>
            <th className="px-4 py-3 font-semibold text-[#6B7280] text-right">Action</th>
          </tr>
        </thead>
        <tbody>
          {Array.from({ length: ROWS }).map((_, i) => (
            <tr key={i} className="border-b border-[#E5E7EB] last:border-b-0">
              <td className="px-4 py-3">
                <div className="h-4 w-32 animate-pulse rounded bg-[#E5E7EB]" />
              </td>
              <td className="px-4 py-3">
                <div className="h-4 w-24 animate-pulse rounded bg-[#E5E7EB]" />
              </td>
              <td className="px-4 py-3">
                <div className="h-5 w-20 animate-pulse rounded-full bg-[#E5E7EB]" />
              </td>
              <td className="px-4 py-3">
                <div className="h-4 w-28 animate-pulse rounded bg-[#E5E7EB]" />
              </td>
              <td className="px-4 py-3 text-right">
                <div className="ml-auto h-4 w-16 animate-pulse rounded bg-[#E5E7EB]" />
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default IdeasTableSkeleton;
