import { MARKET_TABS } from "../constants";

export default function MarketTabs({ activeTab, onChange }) {
  return (
    <div className="flex flex-wrap gap-2 border-b border-slate-200 pb-2 dark:border-slate-700">
      {MARKET_TABS.map((tab) => {
        const isActive = tab.id === activeTab;
        return (
          <button
            key={tab.id}
            type="button"
            onClick={() => onChange(tab.id)}
            className={`rounded-md border px-3 py-1 text-sm font-semibold transition ${
              isActive
                ? "border-blue-300 bg-blue-50 text-blue-700 dark:border-blue-700 dark:bg-blue-950/40 dark:text-blue-300"
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

