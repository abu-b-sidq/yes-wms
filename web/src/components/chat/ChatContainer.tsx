import React, { useEffect, useRef } from 'react';
import ChatMessage from './ChatMessage';
import ChatInput from './ChatInput';
import ComponentRenderer from '../renderers/ComponentRenderer';
import type { Message, UIComponent } from '../../types/chat';
import { looksLikeStructuredAssistantContent, resolveAssistantRenderState } from '../../utils/assistantContent';

interface ChatContainerProps {
  messages: Message[];
  streaming: boolean;
  streamingText: string;
  streamingComponents: UIComponent[];
  activeToolCall: string | null;
  error: string | null;
  onSend: (message: string) => void;
  onConfirmAction: (action: string, parameters: Record<string, unknown>) => void;
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
}: ChatContainerProps) {
  const scrollRef = useRef<HTMLDivElement>(null);
  const streamingRenderState = resolveAssistantRenderState(streamingText, streamingComponents);
  const showStreamingBubble = Boolean(streamingRenderState.text);
  const showStructuredPlaceholder =
    streaming &&
    !showStreamingBubble &&
    streamingRenderState.components.length === 0 &&
    looksLikeStructuredAssistantContent(streamingText);

  // Auto-scroll on new content
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, streamingText, streamingComponents]);

  return (
    <div className="flex flex-col h-full">
      {/* Messages area */}
      <div
        ref={scrollRef}
        className="flex-1 overflow-y-auto chat-scroll px-4 py-6"
      >
        <div className="max-w-4xl mx-auto space-y-6">
          {/* Welcome message when empty */}
          {messages.length === 0 && !streaming && (
            <div className="text-center py-20">
              <h2 className="text-2xl font-bold text-gray-800 mb-3">
                Welcome to YES WMS
              </h2>
              <p className="text-gray-500 mb-8 max-w-lg mx-auto">
                Ask questions about your warehouse in plain English. Try queries like:
              </p>
              <div className="flex flex-wrap justify-center gap-2">
                {[
                  'How many GRNs done today?',
                  'Show inventory levels',
                  'List pending transactions',
                  'What SKUs are in Zone A?',
                ].map((suggestion) => (
                  <button
                    key={suggestion}
                    onClick={() => onSend(suggestion)}
                    className="px-4 py-2 bg-white border border-gray-200 rounded-full text-sm text-gray-600 hover:border-primary-400 hover:text-primary-600 transition"
                  >
                    {suggestion}
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Chat messages */}
          {messages.map((msg) => (
            <ChatMessage
              key={msg.id}
              message={msg}
              onConfirmAction={onConfirmAction}
            />
          ))}

          {/* Streaming indicator */}
          {streaming && (
            <div className="flex justify-start">
              <div className="max-w-3xl mr-12">
                <div className="text-xs font-medium text-primary-600 mb-1">
                  AI Assistant
                </div>

                {activeToolCall && (
                  <div className="flex items-center gap-2 px-4 py-2 bg-primary-50 border border-primary-100 rounded-xl text-sm text-primary-700 mb-2">
                    <div className="animate-spin h-3 w-3 border-2 border-primary-500 border-t-transparent rounded-full" />
                    {activeToolCall}
                  </div>
                )}

                {showStreamingBubble && (
                  <div className="bg-white border border-gray-200 rounded-2xl px-4 py-3">
                    <div className="whitespace-pre-wrap text-sm leading-relaxed cursor-blink">
                      {streamingRenderState.text}
                    </div>
                  </div>
                )}

                {!showStreamingBubble && !activeToolCall && !showStructuredPlaceholder && (
                  <div className="flex items-center gap-2 px-4 py-3 bg-white border border-gray-200 rounded-2xl">
                    <div className="flex gap-1">
                      <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                      <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                      <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                    </div>
                    <span className="text-sm text-gray-500">Thinking...</span>
                  </div>
                )}

                {showStructuredPlaceholder && (
                  <div className="flex items-center gap-2 px-4 py-3 bg-white border border-gray-200 rounded-2xl text-sm text-gray-500">
                    <div className="flex gap-1">
                      <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                      <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                      <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
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
          )}

          {/* Error */}
          {error && (
            <div className="bg-red-50 border border-red-200 rounded-xl px-4 py-3 text-sm text-red-700">
              {error}
            </div>
          )}
        </div>
      </div>

      {/* Input */}
      <ChatInput onSend={onSend} disabled={streaming} />
    </div>
  );
}
