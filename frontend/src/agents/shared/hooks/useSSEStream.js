import { useCallback, useEffect, useRef } from "react";

/**
 * useSSEStream
 * Low-level hook that reads a POST-based SSE stream from the AI backend.
 *
 * Changes vs original:
 *   - Added AbortController so navigating away stops the in-flight stream.
 *   - Each new readSSEStream call automatically aborts any previous stream.
 *   - cancelStream() exposed for explicit cancellation (e.g., user clicks "Stop").
 *   - readSSEStream signature is UNCHANGED — all existing callers work without modification.
 */
export function useSSEStream() {
  const abortRef = useRef(null);

  // Abort any active stream when the component using this hook unmounts.
  useEffect(() => {
    return () => {
      abortRef.current?.abort();
    };
  }, []);

  const readSSEStream = useCallback(async (url, body, onEvent, options = {}) => {
    // Cancel any previous in-flight stream before starting a new one.
    abortRef.current?.abort();
    const controller = new AbortController();
    abortRef.current = controller;

    const requestHeaders = {
      "Content-Type": "application/json",
      ...(options.headers || {}),
    };

    const response = await fetch(url, {
      method: "POST",
      headers: requestHeaders,
      body: JSON.stringify(body),
      signal: controller.signal,
    });

    if (!response.ok) {
      const text = await response.text();
      throw new Error(`HTTP ${response.status}: ${text}`);
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder("utf-8");
    let buffer = "";

    // Store the last "result" received — only forward it after "done" arrives.
    let pendingResult = null;

    const parseBlock = (block) => {
      const trimmed = block.trim();
      if (!trimmed) return;

      let eventType = "message";
      const dataLines = [];

      for (const line of trimmed.split("\n")) {
        if (line.startsWith("event:")) {
          eventType = line.slice(6).trim();
        } else if (line.startsWith("data:")) {
          dataLines.push(line.slice(5).trimStart());
        }
      }

      const rawData = dataLines.join("\n").trim();
      if (!rawData) return;

      // Basic structural check — not a full JSON validator, but guards obvious truncation.
      const isComplete =
        (rawData.startsWith("{") && rawData.endsWith("}")) ||
        (rawData.startsWith("[") && rawData.endsWith("]")) ||
        (!rawData.startsWith("{") && !rawData.startsWith("["));

      if (!isComplete) {
        // Incomplete JSON — put back into buffer and wait for more data.
        buffer = block + "\n\n" + buffer;
        return;
      }

      let parsed;
      try {
        parsed = JSON.parse(rawData);
      } catch {
        parsed = rawData;
      }

      if (eventType === "step") {
        onEvent("step", parsed);
        return;
      }

      if (eventType === "result") {
        pendingResult = parsed;
        return;
      }

      if (eventType === "error") {
        onEvent("error", parsed);
        return;
      }

      if (eventType === "done") {
        if (pendingResult !== null) {
          onEvent("result", pendingResult);
          pendingResult = null;
        }
        onEvent("done", parsed);
        return;
      }

      onEvent(eventType, parsed);
    };

    const processBuffer = () => {
      const normalized = buffer.replace(/\r\n/g, "\n");
      const blocks = normalized.split("\n\n");
      buffer = blocks.pop() ?? "";
      for (const block of blocks) {
        parseBlock(block);
      }
    };

    try {
      while (true) {
        const { done, value } = await reader.read();

        if (done) {
          buffer += decoder.decode();
          if (buffer.trim()) {
            buffer += "\n\n";
            processBuffer();
          }
          // Forward any result that arrived without a trailing "done" event.
          if (pendingResult !== null) {
            onEvent("result", pendingResult);
            pendingResult = null;
          }
          break;
        }

        buffer += decoder.decode(value, { stream: true });
        buffer = buffer.replace(/\r\n/g, "\n");

        if (buffer.includes("\n\n")) {
          processBuffer();
        }
      }
    } catch (err) {
      // Suppress AbortError — it is expected when the stream is intentionally cancelled.
      if (err.name !== "AbortError") {
        throw err;
      }
    }
  }, []);

  const cancelStream = useCallback(() => {
    abortRef.current?.abort();
  }, []);

  return { readSSEStream, cancelStream };
}
