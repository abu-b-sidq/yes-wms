import React, { useState, useCallback } from 'react';
import { useWebSocket, type WsEvent } from '../../hooks/useWebSocket';

interface Notification {
  id: string;
  type: string;
  message: string;
  timestamp: Date;
}

interface NotificationPanelProps {
  facilityId: string | null;
}

export default function NotificationPanel({ facilityId }: NotificationPanelProps) {
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [isOpen, setIsOpen] = useState(false);

  const handleEvent = useCallback((event: WsEvent) => {
    if (event.type === 'pong' || event.type === 'connected' || event.type === 'subscribed') return;

    const notification: Notification = {
      id: `${Date.now()}-${Math.random()}`,
      type: event.type,
      message: formatEvent(event),
      timestamp: new Date(),
    };

    setNotifications(prev => [notification, ...prev].slice(0, 50));
  }, []);

  const { connected } = useWebSocket(facilityId, handleEvent);
  const unreadCount = notifications.length;

  return (
    <div className="relative">
      {/* Bell button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="relative p-2 text-gray-500 hover:text-gray-700 transition"
      >
        <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
        </svg>
        {unreadCount > 0 && (
          <span className="absolute -top-0.5 -right-0.5 w-4 h-4 bg-red-500 text-white text-[10px] font-bold rounded-full flex items-center justify-center">
            {unreadCount > 9 ? '9+' : unreadCount}
          </span>
        )}
      </button>

      {/* Connection indicator */}
      <div className={`absolute -bottom-0.5 right-1 w-2 h-2 rounded-full ${connected ? 'bg-green-400' : 'bg-gray-300'}`} />

      {/* Dropdown panel */}
      {isOpen && (
        <div className="absolute right-0 mt-2 w-80 bg-white border border-gray-200 rounded-xl shadow-lg z-50">
          <div className="px-4 py-3 border-b border-gray-100 flex items-center justify-between">
            <h3 className="font-semibold text-sm text-gray-800">Notifications</h3>
            {notifications.length > 0 && (
              <button
                onClick={() => setNotifications([])}
                className="text-xs text-gray-500 hover:text-gray-700"
              >
                Clear all
              </button>
            )}
          </div>
          <div className="max-h-80 overflow-y-auto">
            {notifications.length === 0 ? (
              <div className="px-4 py-8 text-center text-sm text-gray-400">
                No notifications yet
              </div>
            ) : (
              notifications.map((n) => (
                <div key={n.id} className="px-4 py-3 border-b border-gray-50 hover:bg-gray-50 transition">
                  <div className="text-sm text-gray-800">{n.message}</div>
                  <div className="text-xs text-gray-400 mt-1">
                    {n.timestamp.toLocaleTimeString()}
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      )}
    </div>
  );
}

function formatEvent(event: WsEvent): string {
  switch (event.type) {
    case 'new_task_available':
      return `New task available: ${event.pick_count || 0} picks for transaction ${String(event.transaction_id || '').slice(0, 8)}...`;
    case 'task_completed':
      return `Task completed by ${event.user || 'a worker'}`;
    default:
      return `${event.type}: ${JSON.stringify(event).slice(0, 100)}`;
  }
}
