import { useEffect, useRef, useCallback, useState } from 'react';
import { auth } from '../api/firebase';

export interface WsEvent {
  type: string;
  [key: string]: unknown;
}

export function useWebSocket(
  facilityId: string | null,
  onEvent: (event: WsEvent) => void
) {
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimer = useRef<ReturnType<typeof setTimeout>>();
  const retryCount = useRef(0);
  const [connected, setConnected] = useState(false);

  const connect = useCallback(async () => {
    if (!facilityId) return;

    const user = auth.currentUser;
    if (!user) return;

    const token = await user.getIdToken();
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = window.location.host;
    const url = `${protocol}//${host}/ws/tasks/?token=${token}`;

    const ws = new WebSocket(url);
    wsRef.current = ws;

    ws.onopen = () => {
      setConnected(true);
      retryCount.current = 0;
      // Subscribe to facility
      ws.send(JSON.stringify({ type: 'subscribe_facility', facility_id: facilityId }));
    };

    ws.onmessage = (evt) => {
      try {
        const data = JSON.parse(evt.data);
        onEvent(data);
      } catch {
        // Ignore malformed messages
      }
    };

    ws.onclose = () => {
      setConnected(false);
      // Exponential backoff reconnection (max 30s)
      const delay = Math.min(1000 * Math.pow(2, retryCount.current), 30000);
      retryCount.current += 1;
      reconnectTimer.current = setTimeout(connect, delay);
    };

    ws.onerror = () => {
      ws.close();
    };
  }, [facilityId, onEvent]);

  useEffect(() => {
    connect();
    return () => {
      clearTimeout(reconnectTimer.current);
      wsRef.current?.close();
    };
  }, [connect]);

  // Ping keep-alive
  useEffect(() => {
    const interval = setInterval(() => {
      if (wsRef.current?.readyState === WebSocket.OPEN) {
        wsRef.current.send(JSON.stringify({ type: 'ping' }));
      }
    }, 30000);
    return () => clearInterval(interval);
  }, []);

  return { connected };
}
