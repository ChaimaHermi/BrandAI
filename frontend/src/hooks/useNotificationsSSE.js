import { useCallback, useEffect, useRef, useState } from "react";
import { apiListNotifications, apiMarkRead, apiMarkAllRead } from "@/services/notificationsApi";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000/api";

/**
 * Hook for real-time notifications via SSE + REST fallback.
 * @param {string|null} token  JWT token
 */
export function useNotifications(token) {
  const [items, setItems] = useState([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const esRef = useRef(null);

  const refresh = useCallback(async () => {
    if (!token) return;
    try {
      const data = await apiListNotifications(token);
      setItems(data.items || []);
      setUnreadCount(data.unread_count ?? 0);
    } catch {
      /* silent */
    }
  }, [token]);

  useEffect(() => {
    if (!token) return;
    refresh();

    const url = `${API_URL}/notifications/stream?token=${encodeURIComponent(token)}`;
    const es = new EventSource(url);
    esRef.current = es;

    es.addEventListener("notification", (e) => {
      try {
        const payload = JSON.parse(e.data);
        setItems((prev) => [payload, ...prev].slice(0, 100));
        setUnreadCount((c) => c + 1);
      } catch {
        /* ignore malformed */
      }
    });

    es.onerror = () => {
      es.close();
      setTimeout(() => {
        if (esRef.current === es) refresh();
      }, 5000);
    };

    return () => {
      es.close();
      esRef.current = null;
    };
  }, [token, refresh]);

  const markRead = useCallback(
    async (id) => {
      if (!token) return;
      await apiMarkRead(token, id).catch(() => {});
      setItems((prev) =>
        prev.map((n) => (n.id === id ? { ...n, is_read: true } : n)),
      );
      setUnreadCount((c) => Math.max(0, c - 1));
    },
    [token],
  );

  const markAllRead = useCallback(async () => {
    if (!token) return;
    await apiMarkAllRead(token).catch(() => {});
    setItems((prev) => prev.map((n) => ({ ...n, is_read: true })));
    setUnreadCount(0);
  }, [token]);

  return { items, unreadCount, markRead, markAllRead, refresh };
}
