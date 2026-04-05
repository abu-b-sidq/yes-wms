import React from 'react';
import type { Message } from '../../types/chat';
import { resolveAssistantRenderState } from '../../utils/assistantContent';
import ComponentRenderer from '../renderers/ComponentRenderer';
import AssistantAvatar from './AssistantAvatar';
import { ASSISTANT_NAME } from '../../constants/branding';

interface ChatMessageProps {
  message: Message;
  onConfirmAction?: (action: string, parameters: Record<string, unknown>) => void;
}

function resolveRoleLabel(message: Message): string {
  switch (message.role) {
    case 'assistant':
      return ASSISTANT_NAME;
    case 'tool':
      return 'Tool update';
    case 'system':
      return 'System';
    default:
      return 'You';
  }
}

export default function ChatMessage({ message, onConfirmAction }: ChatMessageProps) {
  const isUser = message.role === 'user';
  const isAssistant = message.role === 'assistant';
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
      <div className={`flex w-full max-w-4xl gap-3 ${isUser ? 'justify-end' : 'items-start'}`}>
        {!isUser && isAssistant && <AssistantAvatar size="sm" className="hidden sm:block" />}

        <div className={`max-w-3xl ${isUser ? 'ml-12' : 'mr-12'}`}>
          <div
            className={`mb-1 text-xs font-medium ${
              isUser ? 'text-right text-[var(--ops-text-soft)]' : 'text-[var(--ops-text-muted)]'
            }`}
          >
            {resolveRoleLabel(message)}
          </div>

          {showBubble && (
            <div
              className={`rounded-[26px] px-4 py-3.5 shadow-[0_16px_36px_rgba(3,13,10,0.18)] ${
                isUser
                  ? 'border border-[rgba(212,234,114,0.14)] bg-[linear-gradient(180deg,rgba(121,191,100,0.96)_0%,rgba(95,159,78,0.96)_100%)] text-[var(--ops-primary-contrast)]'
                  : 'border border-[var(--ops-border)] bg-[linear-gradient(180deg,rgba(20,40,34,0.96)_0%,rgba(13,28,23,0.96)_100%)] text-[var(--ops-text)]'
              }`}
            >
              <div className="whitespace-pre-wrap text-sm leading-7">{contentToRender}</div>
            </div>
          )}

          {showRenderFallback && (
            <div className="rounded-[26px] border border-[var(--ops-border)] bg-[rgba(255,255,255,0.03)] px-4 py-3 text-sm text-[var(--ops-text-muted)]">
              Structured response received, but it could not be rendered.
            </div>
          )}

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
    </div>
  );
}
