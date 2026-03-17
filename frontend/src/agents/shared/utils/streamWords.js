export function createStreamWords(setMessages) {
  return (fullText, onComplete) => {
    if (!fullText || typeof fullText !== "string") {
      if (onComplete) onComplete(null);
      return null;
    }

    const clean = fullText
      .replace(/\bundefined\b/g, "")
      .replace(/\s{2,}/g, " ")
      .trim();

    if (!clean) { if (onComplete) onComplete(null); return null; }

    const words = clean.split(" ");
    const msgId = Date.now() + Math.random();

    setMessages(prev => [...prev, {
      id: msgId,
      role: "agent",
      content: "",
      isStreaming: true,
      timestamp: new Date(),
    }]);

    let i = 0;
    const tick = () => {
      if (i < words.length) {
        setMessages(prev => prev.map(m =>
          m.id === msgId
            ? { ...m, content: m.content + (i === 0 ? "" : " ") + words[i] }
            : m
        ));
        i++;
        setTimeout(tick, 40 + Math.random() * 40);
      } else {
        setMessages(prev => prev.map(m =>
          m.id === msgId ? { ...m, isStreaming: false } : m
        ));
        if (onComplete) onComplete(msgId);
      }
    };
    tick();
    return msgId;
  };
}

