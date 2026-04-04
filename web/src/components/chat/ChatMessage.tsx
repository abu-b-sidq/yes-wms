import React from 'react';
import type { Message } from '../../types/chat';
import ComponentRenderer from '../renderers/ComponentRenderer';
import { resolveAssistantRenderState } from '../../utils/assistantContent';

interface ChatMessageProps {
  message: Message;
  onConfirmAction?: (action: string, parameters: Record<string, unknown>) => void;
}

export default function ChatMessage({ message, onConfirmAction }: ChatMessageProps) {
  const isUser = message.role === 'user';
  const assistantRenderState = !isUser
    ? resolveAssistantRenderState(message.content, message.components)
    : null;
  const contentToRender = isUser ? message.content : assistantRenderState?.text ?? message.content;
  const componentsToRender = isUser ? [] : assistantRenderState?.components ?? [];
  const showBubble = Boolean(contentToRender);
  const showRenderFallback =
    !isUser &&
    Boolean(assistantRenderState?.hideRawContent) &&
    !contentToRender &&
    componentsToRender.length === 0;

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}>
      <div className={`max-w-3xl ${isUser ? 'ml-12' : 'mr-12'}`}>
        {/* Role label */}
        <div className={`text-xs font-medium mb-1 ${isUser ? 'text-right text-gray-500' : 'text-primary-600'}`}>
          {isUser ? 'You' : 'AI Assistant'}
        </div>

        {/* Message bubble */}
        {showBubble && (
          <div
            className={`rounded-2xl px-4 py-3 ${
              isUser
                ? 'bg-primary-600 text-white'
                : 'bg-white border border-gray-200 text-gray-800'
            }`}
          >
            <div className="whitespace-pre-wrap text-sm leading-relaxed">
              {contentToRender}
            </div>
          </div>
        )}

        {showRenderFallback && (
          <div className="rounded-2xl px-4 py-3 bg-gray-50 border border-gray-200 text-sm text-gray-500">
            Structured response received, but it could not be rendered.
          </div>
        )}

        {/* Dynamic components */}
        {componentsToRender.length > 0 && (
          <div className="mt-3 space-y-3">
            {componentsToRender.map((component, idx) => (
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
