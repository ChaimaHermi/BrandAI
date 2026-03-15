import React from "react";
import { HiOutlineChevronLeft, HiOutlineChevronRight } from "react-icons/hi2";

/**
 * Reusable pagination: Previous | 1 2 3 ... | Next
 * @param {number} currentPage - 1-based current page
 * @param {number} totalPages - total number of pages
 * @param {function} onPageChange - (page: number) => void
 */
export function Pagination({ currentPage, totalPages, onPageChange }) {
  if (totalPages <= 1) return null;

  const showPages = 5;
  let start = Math.max(1, currentPage - Math.floor(showPages / 2));
  let end = Math.min(totalPages, start + showPages - 1);
  if (end - start + 1 < showPages) start = Math.max(1, end - showPages + 1);
  const pages = [];
  for (let i = start; i <= end; i++) pages.push(i);

  return (
    <nav
      className="flex flex-wrap items-center justify-center gap-1"
      aria-label="Pagination"
    >
      <button
        type="button"
        onClick={() => onPageChange(currentPage - 1)}
        disabled={currentPage <= 1}
        className="inline-flex h-8 min-w-[2rem] items-center justify-center gap-1 rounded-[8px] border border-[#E5E7EB] bg-white px-2 text-sm font-medium text-[#6B7280] transition-colors hover:border-[#7C3AED] hover:text-[#7C3AED] disabled:cursor-not-allowed disabled:opacity-50"
        aria-label="Page précédente"
      >
        <HiOutlineChevronLeft className="h-4 w-4" />
        <span className="hidden sm:inline">Précédent</span>
      </button>
      <div className="flex items-center gap-0.5">
        {pages.map((p) => (
          <button
            key={p}
            type="button"
            onClick={() => onPageChange(p)}
            className={`flex h-8 min-w-[2rem] items-center justify-center rounded-[8px] px-2 text-sm font-medium transition-colors ${
              p === currentPage
                ? "bg-[#7C3AED] text-white"
                : "border border-[#E5E7EB] bg-white text-[#6B7280] hover:border-[#7C3AED] hover:text-[#7C3AED]"
            }`}
            aria-label={`Page ${p}`}
            aria-current={p === currentPage ? "page" : undefined}
          >
            {p}
          </button>
        ))}
      </div>
      <button
        type="button"
        onClick={() => onPageChange(currentPage + 1)}
        disabled={currentPage >= totalPages}
        className="inline-flex h-8 min-w-[2rem] items-center justify-center gap-1 rounded-[8px] border border-[#E5E7EB] bg-white px-2 text-sm font-medium text-[#6B7280] transition-colors hover:border-[#7C3AED] hover:text-[#7C3AED] disabled:cursor-not-allowed disabled:opacity-50"
        aria-label="Page suivante"
      >
        <span className="hidden sm:inline">Suivant</span>
        <HiOutlineChevronRight className="h-4 w-4" />
      </button>
    </nav>
  );
}

export default Pagination;
