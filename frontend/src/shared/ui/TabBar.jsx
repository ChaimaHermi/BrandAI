import React from "react";

/**
 * TabBar
 * Standardized tab navigation bar used across all agent modules.
 * Replaces the three separate tab implementations in Market, Marketing, and Brand.
 *
 * Props:
 *   tabs      — Array of { id: string, label: string }
 *   activeId  — id of the currently active tab
 *   onChange  — (id: string) => void
 *   className — extra classes on the wrapper (optional)
 */
export function TabBar({ tabs, activeId, onChange, className = "" }) {
  return (
    <div className={`flex flex-wrap gap-2 ${className}`}>
      {tabs.map((tab) => (
        <button
          key={tab.id}
          type="button"
          onClick={() => onChange(tab.id)}
          className={`rounded-full border px-4 py-1.5 text-[12px] font-semibold transition-all duration-150 ${
            activeId === tab.id
              ? "border-[#AFA9EC] bg-[#f0eeff] text-[#3C3489]"
              : "border-[#e8e4ff] bg-white text-gray-500 hover:border-[#AFA9EC] hover:text-[#534AB7]"
          }`}
        >
          {tab.label}
        </button>
      ))}
    </div>
  );
}

export default TabBar;
