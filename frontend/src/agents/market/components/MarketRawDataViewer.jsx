export default function MarketRawDataViewer({ data }) {
  return (
    <div className="rounded-2xl border border-violet-200 bg-white p-4">
      <h2 className="mb-3 text-sm font-bold text-[#1E1B4B]">Market Analysis (raw JSON)</h2>
      <pre className="max-h-[70vh] overflow-auto rounded-xl bg-[#1E1B4B] p-4 text-xs leading-5 text-violet-100">
        {JSON.stringify(data ?? {}, null, 2)}
      </pre>
    </div>
  );
}
