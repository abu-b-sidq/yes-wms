import { useEffect, useRef, useCallback, useState } from 'react';
import auth from '@react-native-firebase/auth';
import { API_BASE_URL } from '../api/client';

export interface WsEvent {
  type: string;
  [key: string]: any;
}

const WS_URL = API_BASE_URL.replace(/^http/, 'ws').replace('/api/v1', '/ws/tasks/');

export function useWebSocket(
  facilityId: string | null,
  onEvent: (event: WsEvent) => void
) {
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimer = useRef<ReturnType<typeof setTimeout>>();
  const [connected, setConnected] = useState(false);
  const retriesRef = useRef(0);

  const connect = useCallback(async () => {
    if (!facilityId) return;

    const user = auth().currentUser;
    if (!user) return;

    const token = await user.getIdToken();
    const url = `${WS_URL}?token=${token}`;

    const ws = new WebSocket(url);
    wsRef.current = ws;

    ws.onopen = () => {
      setConnected(true);
      retriesRef.current = 0;
      // Subscribe to facility
      ws.send(JSON.stringify({
        type: 'subscribe_facility',
        facility_id: facilityId,
      }));
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        onEvent(data);
      } catch {}
    };

    ws.onclose = () => {
      setConnected(false);
      // Exponential backoff reconnect
      const delay = Math.min(1000 * Math.pow(2, retriesRef.current), 30000);
      retriesRef.current += 1;
      reconnectTimer.current = setTimeout(connect, delay);
    };

    ws.onerror = () => {
      ws.close();
    };
  }, [facilityId, onEvent]);

  useEffect(() => {
    connect();
    return () => {
      if (reconnectTimer.current) clearTimeout(reconnectTimer.current);
      wsRef.current?.close();
    };
  }, [connect]);

  const sendPing = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type: 'ping' }));
    }
  }, []);

  return { connected, sendPing };
}
