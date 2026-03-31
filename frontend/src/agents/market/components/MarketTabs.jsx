import { MARKET_TABS } from "../constants";

export default function MarketTabs({ activeTab, onChange }) {
  return (
    <div className="flex flex-wrap gap-2 border-b border-[#e8e4ff] pb-2">
      {MARKET_TABS.map((tab) => {
        const isActive = tab.id === activeTab;
        return (
          <button
            key={tab.id}
            type="button"
            onClick={() => onChange(tab.id)}
            className={`rounded-md px-3 py-1 text-sm font-semibold transition ${
              isActive
                ? "bg-[#f0eeff] text-[#534AB7]"
                : "text-[#8c89ad] hover:bg-[#f8f7ff]"
            }`}
          >
            {tab.label}
          </button>
        );
      })}
    </div>
  );
}

