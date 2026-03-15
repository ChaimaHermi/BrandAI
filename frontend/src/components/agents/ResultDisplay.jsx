import React, { useState, useEffect } from "react";
import { Card } from "../ui/Card";

export function TypewriterLines({ lines, className = "" }) {
  const [displayedLines, setDisplayedLines] = useState([]);
  const [currentLineIndex, setCurrentLineIndex] = useState(0);
  const [currentCharIndex, setCurrentCharIndex] = useState(0);

  useEffect(() => {
    if (lines.length === 0) return;
    const line = lines[currentLineIndex];
    const isLastChar = currentCharIndex >= line.length;
    const isLastLine = currentLineIndex === lines.length - 1;
    if (isLastChar && isLastLine) return;
    const timeout = setTimeout(() => {
      if (isLastChar) {
        setDisplayedLines((prev) => [...prev, line]);
        setCurrentLineIndex((i) => i + 1);
        setCurrentCharIndex(0);
      } else {
        const char = line[currentCharIndex];
        setDisplayedLines((prev) => {
          const next = [...prev];
          if (next.length <= currentLineIndex) next.push("");
          next[currentLineIndex] = (next[currentLineIndex] || "") + char;
          return next;
        });
        setCurrentCharIndex((i) => i + 1);
      }
    }, isLastChar ? 400 : 50);
    return () => clearTimeout(timeout);
  }, [lines, currentLineIndex, currentCharIndex]);

  const currentLine = lines[currentLineIndex] || "";
  const currentDisplay = (displayedLines[currentLineIndex] || "").replace(/▌$/, "");
  const showCursor = currentLineIndex < lines.length && currentCharIndex < currentLine.length;

  return (
    <div className={`font-mono text-sm text-[#111827] ${className}`}>
      {displayedLines.slice(0, currentLineIndex).map((line, i) => (
        <div key={i}>{line}</div>
      ))}
      <div>
        {currentDisplay}
        {showCursor && <span className="animate-pulse text-[#7C3AED]">▌</span>}
      </div>
    </div>
  );
}

function StatCard({ label, value, accentColor = "text-[#7C3AED]" }) {
  return (
    <div className="rounded-[10px] border border-[#E5E7EB] border-l-[3px] border-l-[#7C3AED] bg-[#F9FAFB] p-3">
      <p className="text-xs text-[#6B7280]">{label}</p>
      <p className={`mt-0.5 text-base font-semibold ${accentColor}`}>{value}</p>
    </div>
  );
}

function SummaryBlock({ title, children }) {
  return (
    <div className="rounded-lg bg-[#F9FAFB] p-3">
      <p className="text-xs font-medium text-[#111827]">{title}</p>
      <div className="mt-0.5 text-sm text-[#6B7280]">{children}</div>
    </div>
  );
}

export function ResultDisplay({ agentId, data, status }) {
  if (status === "waiting")
    return (
      <Card className="flex flex-col items-center justify-center py-10" hover={false}>
        <p className="text-sm text-[#6B7280]">En attente de génération...</p>
      </Card>
    );

  if (status === "running" && data?.typewriterLines)
    return (
      <Card hover={false} className="border border-[#E5E7EB] bg-white p-3">
        <TypewriterLines lines={data.typewriterLines} />
        <div className="mt-3 h-1 w-full overflow-hidden rounded-full bg-[#F9FAFB]">
          <div className="h-full w-[45%] animate-progress-bar rounded-full bg-[#7C3AED]" />
        </div>
      </Card>
    );

  if (status === "done") {
    if (agentId === "idea")
      return (
        <div className="space-y-3">
          <SummaryBlock title="Idée initiale">{data?.initial}</SummaryBlock>
          <SummaryBlock title="Idée enrichie">{data?.enhanced}</SummaryBlock>
          <SummaryBlock title="Résumé">{data?.summary}</SummaryBlock>
        </div>
      );
    if (agentId === "market")
      return (
        <div className="space-y-3">
          <div className="grid gap-3 sm:grid-cols-3">
            <StatCard label="Taille de marché" value={data?.market_size} />
            <StatCard label="Concurrents" value={data?.competitors} />
            <StatCard label="Croissance" value={data?.growth} accentColor="text-[#16A34A]" />
          </div>
          <SummaryBlock title="Opportunité">{data?.opportunity}</SummaryBlock>
          <SummaryBlock title="Principaux concurrents">
            <ul className="list-inside list-disc">
              {data?.top_competitors?.map((c) => (
                <li key={c}>{c}</li>
              ))}
            </ul>
          </SummaryBlock>
        </div>
      );
    return (
      <Card hover={false}>
        <p className="text-[#6B7280]">Résultats disponibles.</p>
      </Card>
    );
  }
  return null;
}

export default ResultDisplay;
