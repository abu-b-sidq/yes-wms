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
    <div className="flex flex-col h-full">
      {/* New conversation button */}
      <div className="p-3">
        <button
          onClick={onNew}
          className="w-full flex items-center gap-2 px-4 py-2.5 bg-primary-600 text-white rounded-xl text-sm font-medium hover:bg-primary-700 transition"
        >
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M12 4v16m8-8H4" />
          </svg>
          New Chat
        </button>
      </div>

      {/* Conversation list */}
      <div className="flex-1 overflow-y-auto px-3 space-y-1">
        {conversations.map((conv) => (
          <div
            key={conv.id}
            className={`group flex items-center gap-2 px-3 py-2.5 rounded-lg cursor-pointer transition ${
              conv.id === activeId
                ? 'bg-primary-50 text-primary-700'
                : 'text-gray-700 hover:bg-gray-100'
            }`}
            onClick={() => onSelect(conv.id)}
          >
            <div className="flex-1 min-w-0">
              <div className="text-sm font-medium truncate">{conv.title}</div>
              <div className="text-xs text-gray-400 mt-0.5">
                {conv.model_provider}/{conv.model_name}
              </div>
            </div>
            <button
              onClick={(e) => {
                e.stopPropagation();
                onDelete(conv.id);
              }}
              className="opacity-0 group-hover:opacity-100 p-1 text-gray-400 hover:text-red-500 transition"
            >
              <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
              </svg>
            </button>
          </div>
        ))}

        {conversations.length === 0 && (
          <div className="text-center text-sm text-gray-400 py-8">
            No conversations yet
          </div>
        )}
      </div>
    </div>
  );
}
