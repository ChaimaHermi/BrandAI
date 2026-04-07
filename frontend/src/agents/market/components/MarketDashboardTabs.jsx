const tabs = [
  { id: "raw", label: "Raw JSON" },
  { id: "apercu", label: "Aperçu" },
  { id: "competiteurs", label: "Compétiteurs" },
  { id: "voc", label: "VOC" },
  { id: "tendances", label: "Tendances" },
  { id: "strategie", label: "Stratégie" },
  { id: "mots-cles", label: "Mots-clés" },
];

export default function MarketDashboardTabs({ activeTab, onTabChange }) {
  return (
    <div className="rounded-xl bg-[#1E1B4B] p-2">
      <div className="flex flex-wrap gap-2">
        {tabs.map((tab) => {
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              type="button"
              onClick={() => onTabChange?.(tab.id)}
              className={
                isActive
                  ? "rounded-lg bg-white px-3 py-1.5 text-sm font-semibold text-[#7C3AED]"
                  : "rounded-lg bg-transparent px-3 py-1.5 text-sm font-medium text-violet-200 hover:text-violet-100"
              }
            >
              {tab.label}
            </button>
          );
        })}
      </div>
    </div>
  );
}
