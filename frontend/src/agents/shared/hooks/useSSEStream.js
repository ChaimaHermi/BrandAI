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

    // Stocker le dernier "result" reçu
    // On ne l'envoie à onEvent qu'après "done"
    let pendingResult = null;

    const parseBlock = (block) => {
      const trimmed = block.trim();
      if (!trimmed) return;

      let eventType = "message";
      let rawData = "";

      for (const line of trimmed.split("\n")) {
        if (line.startsWith("event:")) {
          eventType = line.slice(6).trim();
        } else if (line.startsWith("data:")) {
          rawData = line.slice(5).trim();
        }
      }

      if (!rawData) return;

      // Vérifier que le JSON est complet
      const isComplete =
        (rawData.startsWith("{") && rawData.endsWith("}")) ||
        (rawData.startsWith("[") && rawData.endsWith("]")) ||
        (!rawData.startsWith("{") && !rawData.startsWith("["));

      if (!isComplete) {
        // JSON incomplet → remettre dans buffer
        buffer = block + "\n\n" + buffer;
        return;
      }

      let parsed;
      try {
        parsed = JSON.parse(rawData);
      } catch {
        parsed = rawData;
      }

      // step → immédiat (XAI terminal)
      if (eventType === "step") {
        onEvent("step", parsed);
        return;
      }

      // result → stocker, attendre "done"
      if (eventType === "result") {
        pendingResult = parsed;
        return;
      }

      // error → immédiat
      if (eventType === "error") {
        onEvent("error", parsed);
        return;
      }

      // done → maintenant on envoie le result
      if (eventType === "done") {
        if (pendingResult !== null) {
          onEvent("result", pendingResult);
          pendingResult = null;
        }
        onEvent("done", parsed);
        return;
      }

      // autres événements → immédiat
      onEvent(eventType, parsed);
    };

    const processBuffer = () => {
      // Normaliser les retours chariot SSE (CRLF) vers LF pour
      // détecter correctement les blocs séparés.
      const normalized = buffer.replace(/\r\n/g, "\n");
      const blocks = normalized.split("\n\n");
      buffer = blocks.pop() ?? "";
      for (const block of blocks) {
        parseBlock(block);
      }
    };

    // Lire le flux
    while (true) {
      const { done, value } = await reader.read();

      if (done) {
        // Flush final
        buffer += decoder.decode();
        if (buffer.trim()) {
          buffer += "\n\n";
          processBuffer();
        }
        // Si result jamais suivi de done → l'envoyer quand même
        if (pendingResult !== null) {
          onEvent("result", pendingResult);
          pendingResult = null;
        }
        break;
      }

      buffer += decoder.decode(value, { stream: true });
      // Important : normaliser CRLF pour que `.includes("\n\n")` marche
      // même si le serveur envoie `\r\n\r\n`.
      buffer = buffer.replace(/\r\n/g, "\n");

      // Ne parser que si on a au moins un bloc complet
      if (buffer.includes("\n\n")) {
        processBuffer();
      }
    }
  }, []);

  return { readSSEStream };
}

