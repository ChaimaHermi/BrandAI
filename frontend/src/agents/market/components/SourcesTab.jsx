export default function SourcesTab({ report }) {
  const sources = report?.meta?.sources || [];
  const dq = report?.dataQuality || {};

  return (
    <div className="space-y-3">
      <div className="rounded-lg border border-[#e8e4ff] bg-white p-4">
        <p className="text-xs font-bold uppercase tracking-[0.07em] text-[#a09bc6]">Score qualité</p>
        <p className="mt-1 text-2xl font-bold text-[#534AB7]">{dq?.score_global ?? "-"}</p>
        <p className="text-sm text-[#5f5a84]">{dq?.interpretation || "-"}</p>
      </div>

      <div className="grid gap-2 md:grid-cols-2">
        {sources.map((src) => (
          <div key={src} className="rounded-lg border border-[#e8e4ff] bg-white px-3 py-2 text-sm text-[#5f5a84]">
            {src}
          </div>
        ))}
      </div>
    </div>
  );
}

