import React, { useEffect, useRef } from 'react';
import type { Message, UIComponent } from '../../types/chat';
import { looksLikeStructuredAssistantContent, resolveAssistantRenderState } from '../../utils/assistantContent';
import ComponentRenderer from '../renderers/ComponentRenderer';
import AssistantAvatar from './AssistantAvatar';
import ChatInput from './ChatInput';
import ChatMessage from './ChatMessage';
import { ASSISTANT_NAME } from '../../constants/branding';

interface ChatContainerProps {
  messages: Message[];
  streaming: boolean;
  streamingText: string;
  streamingComponents: UIComponent[];
  activeToolCall: string | null;
  error: string | null;
  onSend: (message: string) => void;
  onConfirmAction: (action: string, parameters: Record<string, unknown>) => void;
  viewerName: string;
  facilityName: string;
}

interface PromptCard {
  title: string;
  description: string;
  prompt: string;
}

const promptCards: PromptCard[] = [
  {
    title: 'Inventory snapshot',
    description: 'Zone health and low-stock risk.',
    prompt: 'Summarize inventory health by zone and call out low-stock risk.',
  },
  {
    title: 'Inbound check',
    description: 'GRN progress and receiving blockers.',
    prompt: "Show today's GRN progress and any receiving bottlenecks.",
  },
  {
    title: 'Pending work',
    description: 'Highest-priority warehouse tasks.',
    prompt: 'List the highest-priority open warehouse tasks right now.',
  },
];

function resolveTimeGreeting(): string {
  const hour = new Date().getHours();

  if (hour < 12) {
    return 'morning';
  }

  if (hour < 18) {
    return 'afternoon';
  }

  return 'evening';
}

export default function ChatContainer({
  messages,
  streaming,
  streamingText,
  streamingComponents,
  activeToolCall,
  error,
  onSend,
  onConfirmAction,
  viewerName,
  facilityName,
}: ChatContainerProps) {
  const scrollRef = useRef<HTMLDivElement>(null);
  const streamingRenderState = resolveAssistantRenderState(streamingText, streamingComponents);
  const showStreamingBubble = Boolean(streamingRenderState.text);
  const showStructuredPlaceholder =
    streaming &&
    !showStreamingBubble &&
    streamingRenderState.components.length === 0 &&
    looksLikeStructuredAssistantContent(streamingText);
  const isEmptyState = messages.length === 0 && !streaming;
  const greeting = resolveTimeGreeting();

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, streamingText, streamingComponents]);

  if (isEmptyState) {
    return (
      <div ref={scrollRef} className="h-full overflow-hidden px-4 py-4 md:px-5">
        <div className="mx-auto flex h-full max-w-4xl flex-col justify-center">
          <div className="flex flex-col items-center text-center">
            <div className="pulse-soft rounded-full bg-[radial-gradient(circle_at_35%_35%,rgba(212,234,114,0.88)_0%,rgba(121,191,100,0.9)_44%,rgba(47,106,79,0.96)_100%)] p-[2px] shadow-[0_20px_60px_rgba(91,159,78,0.22)]">
              <div className="rounded-full bg-[rgba(8,19,17,0.86)] p-2">
                <AssistantAvatar size="md" />
              </div>
            </div>
            <h2 className="mt-5 text-3xl font-semibold leading-tight text-[var(--ops-text)] md:text-5xl">
              Good {greeting}, {viewerName}
            </h2>
            <p className="mt-2 text-lg font-medium text-[var(--ops-highlight)] md:text-xl">
              What's moving in {facilityName}?
            </p>
            <p className="mt-3 max-w-2xl text-sm leading-6 text-[var(--ops-text-muted)] md:text-base">
              Ask about inventory, inbound flow, or transaction delays and I'll answer in plain
              language with warehouse context.
            </p>
          </div>

          <div className="mt-6 flex min-h-0 flex-col gap-3">
            <div className="ops-note-card rounded-[26px] px-5 py-4 text-left">
              <div className="flex items-center gap-3">
                <AssistantAvatar size="sm" />
                <div>
                  <p className="ops-label text-xs text-[var(--ops-highlight)]">
                    {ASSISTANT_NAME}
                  </p>
                  <p className="mt-1 text-sm leading-6 text-[var(--ops-text-muted)]">
                    Ask a question, and I'll keep the answer grounded in {facilityName}.
                  </p>
                </div>
              </div>
            </div>

            <div className="flex min-h-0 flex-col gap-3">
              <ChatInput
                onSend={onSend}
                disabled={streaming}
                variant="hero"
                placeholder={`Ask anything about ${facilityName}...`}
              />

              <div className="grid gap-2.5 sm:grid-cols-3">
                {promptCards.map((card) => (
                  <button
                    key={card.title}
                    onClick={() => onSend(card.prompt)}
                    className="ops-card-soft rounded-[22px] px-4 py-3.5 text-left transition hover:-translate-y-0.5 hover:border-[var(--ops-border-strong)] hover:bg-[rgba(255,255,255,0.06)]"
                  >
                    <p className="text-sm font-semibold text-[var(--ops-text)]">{card.title}</p>
                    <p className="mt-1.5 text-sm leading-5 text-[var(--ops-text-muted)]">{card.description}</p>
                  </button>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex h-full flex-col">
      <div ref={scrollRef} className="chat-scroll flex-1 overflow-y-auto px-4 py-4 md:px-5">
        <div className="mx-auto max-w-4xl space-y-6">
          {messages.map((message) => (
            <ChatMessage
              key={message.id}
              message={message}
              onConfirmAction={onConfirmAction}
            />
          ))}

          {streaming && (
            <div className="flex justify-start">
              <div className="flex w-full max-w-4xl gap-3">
                <AssistantAvatar size="sm" className="hidden sm:block" />

                <div className="max-w-3xl">
                  <div className="mb-1 text-xs font-medium text-[var(--ops-text-muted)]">{ASSISTANT_NAME}</div>

                  {activeToolCall && (
                    <div className="ops-note-card mb-2 flex items-center gap-2 rounded-[22px] px-4 py-2.5 text-sm text-[var(--ops-highlight)]">
                      <div className="h-3 w-3 animate-spin rounded-full border-2 border-[var(--ops-primary)] border-t-transparent" />
                      {activeToolCall}
                    </div>
                  )}

                  {showStreamingBubble && (
                    <div className="rounded-[26px] border border-[var(--ops-border)] bg-[linear-gradient(180deg,rgba(20,40,34,0.96)_0%,rgba(13,28,23,0.96)_100%)] px-4 py-3.5 shadow-[0_16px_36px_rgba(3,13,10,0.18)]">
                      <div className="cursor-blink whitespace-pre-wrap text-sm leading-7 text-[var(--ops-text)]">
                        {streamingRenderState.text}
                      </div>
                    </div>
                  )}

                  {!showStreamingBubble && !activeToolCall && !showStructuredPlaceholder && (
                    <div className="flex items-center gap-2 rounded-[26px] border border-[var(--ops-border)] bg-[linear-gradient(180deg,rgba(20,40,34,0.96)_0%,rgba(13,28,23,0.96)_100%)] px-4 py-3.5 shadow-[0_16px_36px_rgba(3,13,10,0.18)]">
                      <div className="flex gap-1">
                        <div className="h-2 w-2 animate-bounce rounded-full bg-[var(--ops-text-soft)]" style={{ animationDelay: '0ms' }} />
                        <div className="h-2 w-2 animate-bounce rounded-full bg-[var(--ops-text-soft)]" style={{ animationDelay: '150ms' }} />
                        <div className="h-2 w-2 animate-bounce rounded-full bg-[var(--ops-text-soft)]" style={{ animationDelay: '300ms' }} />
                      </div>
                      <span className="text-sm text-[var(--ops-text-muted)]">Thinking...</span>
                    </div>
                  )}

                  {showStructuredPlaceholder && (
                    <div className="flex items-center gap-2 rounded-[26px] border border-[var(--ops-border)] bg-[linear-gradient(180deg,rgba(20,40,34,0.96)_0%,rgba(13,28,23,0.96)_100%)] px-4 py-3.5 text-sm text-[var(--ops-text-muted)] shadow-[0_16px_36px_rgba(3,13,10,0.18)]">
                      <div className="flex gap-1">
                        <div className="h-2 w-2 animate-bounce rounded-full bg-[var(--ops-text-soft)]" style={{ animationDelay: '0ms' }} />
                        <div className="h-2 w-2 animate-bounce rounded-full bg-[var(--ops-text-soft)]" style={{ animationDelay: '150ms' }} />
                        <div className="h-2 w-2 animate-bounce rounded-full bg-[var(--ops-text-soft)]" style={{ animationDelay: '300ms' }} />
                      </div>
                      Formatting response...
                    </div>
                  )}

                  {streamingRenderState.components.length > 0 && (
                    <div className="mt-3 space-y-3">
                      {streamingRenderState.components.map((component, idx) => (
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
          )}

          {error && (
            <div className="rounded-[24px] border border-[rgba(239,124,116,0.24)] bg-[rgba(239,124,116,0.12)] px-4 py-3 text-sm text-[var(--ops-danger)]">
              {error}
            </div>
          )}
        </div>
      </div>

      <ChatInput
        onSend={onSend}
        disabled={streaming}
        placeholder={`Ask a follow-up about ${facilityName}...`}
      />
    </div>
  );
}
