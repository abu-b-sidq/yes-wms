import React from 'react';
import ReactMarkdown from 'react-markdown';
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
              className={`rounded-[26px] px-4 py-3.5 ${
                isUser
                  ? 'border border-[rgba(212,234,114,0.14)] bg-[linear-gradient(180deg,rgba(121,191,100,0.96)_0%,rgba(95,159,78,0.96)_100%)] text-[var(--ops-primary-contrast)]'
                  : 'ops-chat-bubble text-[var(--ops-text)]'
              }`}
            >
              {isUser ? (
                <div className="whitespace-pre-wrap text-sm leading-7">{contentToRender}</div>
              ) : (
                <div className="text-sm leading-7">
                <ReactMarkdown
                  components={{
                    h1: ({ children }) => <h1 className="text-lg font-bold mb-2 mt-3 first:mt-0">{children}</h1>,
                    h2: ({ children }) => <h2 className="text-base font-bold mb-2 mt-3 first:mt-0">{children}</h2>,
                    h3: ({ children }) => <h3 className="text-sm font-bold mb-1 mt-2 first:mt-0">{children}</h3>,
                    p: ({ children }) => <p className="mb-2 last:mb-0">{children}</p>,
                    ul: ({ children }) => <ul className="list-disc list-inside mb-2 space-y-0.5">{children}</ul>,
                    ol: ({ children }) => <ol className="list-decimal list-inside mb-2 space-y-0.5">{children}</ol>,
                    li: ({ children }) => <li className="text-sm">{children}</li>,
                    strong: ({ children }) => <strong className="font-semibold">{children}</strong>,
                    hr: () => <hr className="my-3 border-[var(--ops-border)]" />,
                    code: ({ children }) => <code className="bg-[var(--ops-subtle-fill)] rounded px-1 text-xs font-mono">{children}</code>,
                  }}
                >
                  {contentToRender}
                </ReactMarkdown>
                </div>
              )}
            </div>
          )}

          {showRenderFallback && (
            <div className="rounded-[26px] border border-[var(--ops-border)] bg-[var(--ops-subtle-fill)] px-4 py-3 text-sm text-[var(--ops-text-muted)]">
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
