import React from 'react';
import type { Conversation } from '../../types/chat';

interface ConversationListProps {
  conversations: Conversation[];
  activeId: string | null;
  onSelect: (id: string) => void;
  onDelete: (id: string) => void;
  onNew: () => void;
}

export default function ConversationList({
  conversations,
  activeId,
  onSelect,
  onDelete,
  onNew,
}: ConversationListProps) {
  return (
    <div className="flex h-full flex-col">
      <div className="px-2 pb-3">
        <button
          onClick={onNew}
          className="ops-button-primary flex w-full items-center justify-center gap-2 rounded-[22px] px-4 py-3 text-sm font-medium transition"
        >
          <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M12 4v16m8-8H4" />
          </svg>
          New Chat
        </button>
      </div>

      <div className="chat-scroll flex-1 space-y-2 overflow-y-auto px-2 pb-2">
        {conversations.map((conversation) => {
          const isActive = conversation.id === activeId;

          return (
            <div
              key={conversation.id}
              onClick={() => onSelect(conversation.id)}
              className={`group cursor-pointer rounded-[24px] px-4 py-4 transition ${
                isActive
                  ? 'ops-note-card'
                  : 'ops-card-soft hover:-translate-y-0.5 hover:border-[var(--ops-border-strong)] hover:bg-[var(--ops-subtle-fill-strong)]'
              }`}
            >
              <div className="flex items-start gap-3">
                <div className={`mt-1 h-2.5 w-2.5 rounded-full ${isActive ? 'bg-[var(--ops-highlight)]' : 'bg-[var(--ops-text-soft)]'}`} />

                <div className="min-w-0 flex-1">
                  <div className={`truncate text-sm font-semibold ${isActive ? 'text-[var(--ops-highlight)]' : 'text-[var(--ops-text)]'}`}>
                    {conversation.title}
                  </div>
                  <div className="mt-1 truncate text-xs text-[var(--ops-text-muted)]">
                    {conversation.model_provider}/{conversation.model_name}
                  </div>
                </div>

                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    onDelete(conversation.id);
                  }}
                  className="rounded-full p-1.5 text-[var(--ops-text-soft)] opacity-0 transition hover:bg-[rgba(239,124,116,0.12)] hover:text-[var(--ops-danger)] group-hover:opacity-100"
                >
                  <svg className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                  </svg>
                </button>
              </div>
            </div>
          );
        })}

        {conversations.length === 0 && (
          <div className="rounded-[24px] border border-dashed border-[var(--ops-border)] bg-[var(--ops-subtle-fill)] px-4 py-8 text-center text-sm text-[var(--ops-text-soft)]">
            No matching conversations yet
          </div>
        )}
      </div>
    </div>
  );
}
