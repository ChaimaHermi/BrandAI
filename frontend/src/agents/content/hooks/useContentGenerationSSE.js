/**
 * React hook — wraps the SSE streaming API for AI content generation.
 *
 * State exposed:
 *   steps      — array of { tool: string, status: 'running' | 'done' }
 *   isStreaming — boolean, true while the SSE connection is open
 *   sseError   — string | null, last error message
 *
 * Methods:
 *   startStream(payload, token, { onResult, onError })
 *   cancelStream()
 *   resetSSE()
 */

import { useCallback, useRef, useState } from "react";
import { streamContentGeneration } from "../api/contentGenerationStream.api";

/**
 * @returns {{
 *   steps: Array<{ tool: string, status: 'running' | 'done' }>,
 *   isStreaming: boolean,
 *   sseError: string | null,
 *   startStream: (payload: object, token: string | null, callbacks: { onResult?: (data: object) => Promise<void> | void, onError?: (msg: string) => void }) => Promise<void>,
 *   cancelStream: () => void,
 *   resetSSE: () => void,
 * }}
 */
export function useContentGenerationSSE() {
  const [steps, setSteps] = useState([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const [sseError, setSseError] = useState(null);

  // Abort flag — set to true to break out of the for-await loop early
  const cancelledRef = useRef(false);

  const resetSSE = useCallback(() => {
    setSteps([]);
    setSseError(null);
    setIsStreaming(false);
    cancelledRef.current = false;
  }, []);

  const cancelStream = useCallback(() => {
    cancelledRef.current = true;
    setIsStreaming(false);
  }, []);

  /**
   * Start the SSE stream.
   *
   * @param {object} payload
   * @param {string | null} token
   * @param {{ onResult?: (data: object) => Promise<void> | void, onError?: (msg: string) => void }} callbacks
   */
  const startStream = useCallback(
    async (payload, token, { onResult, onError } = {}) => {
      cancelledRef.current = false;
      setSteps([]);
      setSseError(null);
      setIsStreaming(true);

      try {
        for await (const { event, data } of streamContentGeneration(payload, token)) {
          if (cancelledRef.current) break;

          switch (event) {
            case "tool_start": {
              const toolName = data?.tool ?? "";
              setSteps((prev) => {
                // Avoid duplicating a tool that is already tracked
                const exists = prev.some((s) => s.tool === toolName);
                if (exists) return prev;
                return [...prev, { tool: toolName, status: "running" }];
              });
              break;
            }

            case "tool_end": {
              const toolName = data?.tool ?? "";
              setSteps((prev) =>
                prev.map((s) =>
                  s.tool === toolName ? { ...s, status: "done" } : s
                )
              );
              break;
            }

            case "error": {
              const msg = data?.message || "Erreur inconnue lors de la génération.";
              setSseError(msg);
              onError?.(msg);
              break;
            }

            case "done": {
              if (data?.success) {
                // Await so the DB save completes before isStreaming becomes false
                await onResult?.(data);
              }
              // Stream is complete — exit the loop
              cancelledRef.current = true;
              break;
            }

            default:
              break;
          }
        }
      } catch (err) {
        if (!cancelledRef.current) {
          const msg = err?.message || "Erreur de connexion SSE.";
          setSseError(msg);
          onError?.(msg);
        }
      } finally {
        setIsStreaming(false);
      }
    },
    []
  );

  return {
    steps,
    isStreaming,
    sseError,
    startStream,
    cancelStream,
    resetSSE,
  };
}
