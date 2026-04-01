import { MARKET_TABS } from "../constants";

export default function MarketTabs({ activeTab, onChange }) {
  return (
    <div className="app-tabs-row border-b border-slate-200 pb-2 dark:border-slate-700">
      {MARKET_TABS.map((tab) => {
        const isActive = tab.id === activeTab;
        return (
          <button
            key={tab.id}
            type="button"
            onClick={() => onChange(tab.id)}
            className={`min-w-max flex-1 rounded-md border px-3 py-1 text-[13px] font-medium transition ${
              isActive
                ? "border-[#378ADD] bg-[#378ADD] text-white"
                : "border-slate-200 bg-white text-slate-600 hover:bg-slate-50 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-300 dark:hover:bg-slate-800"
            }`}
          >
            {tab.label}
          </button>
        );
      })}
    </div>
  );
}

