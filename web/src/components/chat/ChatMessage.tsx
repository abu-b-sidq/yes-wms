import React from 'react';
import type { Message } from '../../types/chat';
import ComponentRenderer from '../renderers/ComponentRenderer';

interface ChatMessageProps {
  message: Message;
  onConfirmAction?: (action: string, parameters: Record<string, unknown>) => void;
}

export default function ChatMessage({ message, onConfirmAction }: ChatMessageProps) {
  const isUser = message.role === 'user';

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}>
      <div className={`max-w-3xl ${isUser ? 'ml-12' : 'mr-12'}`}>
        {/* Role label */}
        <div className={`text-xs font-medium mb-1 ${isUser ? 'text-right text-gray-500' : 'text-primary-600'}`}>
          {isUser ? 'You' : 'AI Assistant'}
        </div>

        {/* Message bubble */}
        <div
          className={`rounded-2xl px-4 py-3 ${
            isUser
              ? 'bg-primary-600 text-white'
              : 'bg-white border border-gray-200 text-gray-800'
          }`}
        >
          {message.content && (
            <div className="whitespace-pre-wrap text-sm leading-relaxed">
              {message.content}
            </div>
          )}
        </div>

        {/* Dynamic components */}
        {message.components && message.components.length > 0 && (
          <div className="mt-3 space-y-3">
            {message.components.map((component, idx) => (
              <ComponentRenderer
                key={idx}
                component={component}
                onConfirmAction={onConfirmAction}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
