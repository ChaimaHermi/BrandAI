import React from "react";

export function TypingIndicator() {
  return (
    <div className="mt-2 inline-flex items-center gap-2 rounded-full bg-[#F3F4F6] px-3 py-1 text-[11px] text-[#4B5563]">
      <span className="relative flex h-2 w-6 items-center justify-between">
        <span className="h-1.5 w-1.5 rounded-full bg-[#9CA3AF] animate-bounce [animation-delay:-0.2s]" />
        <span className="h-1.5 w-1.5 rounded-full bg-[#9CA3AF] animate-bounce [animation-delay:-0.1s]" />
        <span className="h-1.5 w-1.5 rounded-full bg-[#9CA3AF] animate-bounce" />
      </span>
      <span>L&apos;agent réfléchit...</span>
    </div>
  );
}

export default TypingIndicator;

