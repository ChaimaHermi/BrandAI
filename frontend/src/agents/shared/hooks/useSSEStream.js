import { useCallback } from "react";

export function useSSEStream() {
  const readSSEStream = useCallback(async (url, body, onEvent) => {
    const response = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });

    if (!response.ok) {
      const text = await response.text();
      throw new Error(`HTTP ${response.status}: ${text}`);
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder("utf-8");
    let buffer = "";

    const processBuffer = () => {
      const blocks = buffer.split("\n\n");
      buffer = blocks.pop() ?? "";

      for (const block of blocks) {
        const trimmed = block.trim();
        if (!trimmed) continue;

        let eventType = "message";
        let rawData = "";

        for (const line of trimmed.split("\n")) {
          if (line.startsWith("event:"))
            eventType = line.slice(6).trim();
          else if (line.startsWith("data:"))
            rawData = line.slice(5).trim();
        }

        if (!rawData) continue;

        const isComplete =
          (rawData.startsWith("{") && rawData.endsWith("}")) ||
          !rawData.startsWith("{");

        if (!isComplete) {
          buffer = block + "\n\n" + buffer;
          continue;
        }

        let parsed;
        try { parsed = JSON.parse(rawData); }
        catch { parsed = rawData; }

        onEvent(eventType, parsed);
      }
    };

    while (true) {
      const { done, value } = await reader.read();
      if (done) {
        buffer += decoder.decode();
        if (buffer.trim()) { buffer += "\n\n"; processBuffer(); }
        break;
      }
      buffer += decoder.decode(value, { stream: true });
      if (buffer.includes("\n\n")) processBuffer();
    }
  }, []);

  return { readSSEStream };
}

