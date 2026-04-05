import React, { useCallback, useState } from 'react';
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
    if (event.type === 'pong' || event.type === 'connected' || event.type === 'subscribed') {
      return;
    }

    const notification: Notification = {
      id: `${Date.now()}-${Math.random()}`,
      type: event.type,
      message: formatEvent(event),
      timestamp: new Date(),
    };

    setNotifications((current) => [notification, ...current].slice(0, 50));
  }, []);

  const { connected } = useWebSocket(facilityId, handleEvent);
  const unreadCount = notifications.length;

  return (
    <div className="relative">
      <button
        onClick={() => setIsOpen((current) => !current)}
        className="ops-button-secondary relative rounded-[18px] p-3 transition"
      >
        <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
        </svg>
        {unreadCount > 0 && (
          <span className="absolute -right-1.5 -top-1.5 flex h-5 min-w-5 items-center justify-center rounded-full bg-[var(--ops-primary)] px-1 text-[10px] font-semibold text-[var(--ops-primary-contrast)]">
            {unreadCount > 9 ? '9+' : unreadCount}
          </span>
        )}
        <span className={`absolute -bottom-0.5 right-1.5 h-2.5 w-2.5 rounded-full ${connected ? 'bg-[var(--ops-success)]' : 'bg-[var(--ops-text-soft)]'}`} />
      </button>

      {isOpen && (
        <div className="soft-panel absolute right-0 z-50 mt-3 w-80 p-3">
          <div className="flex items-center justify-between px-2 pb-3">
            <div>
              <h3 className="text-sm font-semibold text-[var(--ops-text)]">Live notifications</h3>
              <p className="text-xs text-[var(--ops-text-soft)]">
                {connected ? 'Connected to facility events' : 'Waiting for live facility events'}
              </p>
            </div>
            {notifications.length > 0 && (
              <button
                onClick={() => setNotifications([])}
                className="text-xs font-medium text-[var(--ops-text-muted)] transition hover:text-[var(--ops-text)]"
              >
                Clear
              </button>
            )}
          </div>

          <div className="chat-scroll max-h-80 space-y-2 overflow-y-auto px-1">
            {notifications.length === 0 ? (
              <div className="rounded-[22px] border border-dashed border-[var(--ops-border)] bg-[var(--ops-subtle-fill)] px-4 py-8 text-center text-sm text-[var(--ops-text-soft)]">
                No notifications yet
              </div>
            ) : (
              notifications.map((notification) => (
                <div
                  key={notification.id}
                  className="ops-card-soft rounded-[22px] px-4 py-3"
                >
                  <div className="text-sm leading-6 text-[var(--ops-text)]">{notification.message}</div>
                  <div className="mt-1 text-xs text-[var(--ops-text-soft)]">
                    {notification.timestamp.toLocaleTimeString()}
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
