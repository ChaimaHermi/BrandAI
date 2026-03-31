export default function RisksRecoTab({ report }) {
  const risques = report?.risques || [];
  const recos = report?.recommandations || [];

  return (
    <div className="space-y-4">
      <div className="space-y-2">
        <p className="text-xs font-bold uppercase tracking-[0.07em] text-[#a09bc6]">Risques identifiés</p>
        {risques.map((risk, idx) => (
          <div key={`${risk.type}-${idx}`} className="rounded-lg border border-[#e8e4ff] bg-white p-3">
            <p className="font-semibold uppercase text-[#3C3489]">{risk.type}</p>
            <p className="text-sm text-[#5f5a84]">{risk.cause}</p>
            <p className="text-sm text-[#7a76a3]">Mitigation: {risk.mitigation || "-"}</p>
          </div>
        ))}
      </div>

      <div className="space-y-2">
        <p className="text-xs font-bold uppercase tracking-[0.07em] text-[#a09bc6]">Recommandations</p>
        {recos.map((reco, idx) => (
          <div key={`${reco.action}-${idx}`} className="rounded-lg border border-[#e8e4ff] bg-white p-3">
            <p className="font-semibold text-[#3C3489]">{reco.action}</p>
            <p className="text-sm text-[#5f5a84]">{reco.impact_attendu || "-"}</p>
            <p className="text-xs uppercase text-[#9a96bf]">{reco.horizon || "-"}</p>
          </div>
        ))}
      </div>
    </div>
  );
}

