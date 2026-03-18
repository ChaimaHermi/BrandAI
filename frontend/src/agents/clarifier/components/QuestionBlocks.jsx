export default function QuestionBlocks({ questions }) {
  if (!Array.isArray(questions) || questions.length === 0) return null;
  const getText = (q) => {
    if (typeof q === "string") return q;
    return q?.text || q?.question || "";
  };
  return (
    <div className="mt-2 flex flex-col gap-1.5">
      {questions.map((q, i) => (
        <div
          key={i}
          className="flex gap-2 rounded-lg bg-[#EDE9FE] p-2 text-sm text-[#111827]"
        >
          <span className="text-xs font-semibold text-[#4C1D95]">
            {i + 1}.
          </span>
          <span>{getText(q)}</span>
        </div>
      ))}
    </div>
  );
}

