import { useState, useCallback, useRef } from 'react';
import { streamChat, createConversation, listConversations, getConversation, deleteConversation } from '../api/ai';
import type { Conversation, Message, UIComponent } from '../types/chat';

interface ChatState {
  conversations: Conversation[];
  activeConversation: Conversation | null;
  messages: Message[];
  streaming: boolean;
  streamingText: string;
  streamingComponents: UIComponent[];
  activeToolCall: string | null;
  error: string | null;
}

export function useChat() {
  const [state, setState] = useState<ChatState>({
    conversations: [],
    activeConversation: null,
    messages: [],
    streaming: false,
    streamingText: '',
    streamingComponents: [],
    activeToolCall: null,
    error: null,
  });
  const abortRef = useRef(false);

  const loadConversations = useCallback(async () => {
    try {
      const convs = await listConversations();
      setState(s => ({ ...s, conversations: convs }));
    } catch (err) {
      setState(s => ({ ...s, error: err instanceof Error ? err.message : 'Failed to load conversations' }));
    }
  }, []);

  const loadConversation = useCallback(async (id: string) => {
    try {
      const conv = await getConversation(id);
      setState(s => ({
        ...s,
        activeConversation: conv,
        messages: conv.messages || [],
        error: null,
      }));
    } catch (err) {
      setState(s => ({ ...s, error: err instanceof Error ? err.message : 'Failed to load conversation' }));
    }
  }, []);

  const startNewConversation = useCallback(async (provider: string, model: string) => {
    try {
      const conv = await createConversation(provider, model);
      setState(s => ({
        ...s,
        activeConversation: conv,
        messages: [],
        conversations: [conv, ...s.conversations],
        error: null,
      }));
      return conv;
    } catch (err) {
      setState(s => ({ ...s, error: err instanceof Error ? err.message : 'Failed to create conversation' }));
      return null;
    }
  }, []);

  const removeConversation = useCallback(async (id: string) => {
    try {
      await deleteConversation(id);
      setState(s => ({
        ...s,
        conversations: s.conversations.filter(c => c.id !== id),
        activeConversation: s.activeConversation?.id === id ? null : s.activeConversation,
        messages: s.activeConversation?.id === id ? [] : s.messages,
      }));
    } catch (err) {
      setState(s => ({ ...s, error: err instanceof Error ? err.message : 'Failed to delete conversation' }));
    }
  }, []);

  const sendMessage = useCallback(async (
    text: string,
    conversationId?: string,
    confirmAction?: { action: string; parameters: Record<string, unknown> }
  ) => {
    const convId = conversationId || state.activeConversation?.id;
    if (!convId) return;

    abortRef.current = false;

    // Add user message to state immediately (unless it's a confirm action)
    if (!confirmAction && text) {
      const userMsg: Message = {
        id: `temp-${Date.now()}`,
        role: 'user',
        content: text,
        components: null,
        tool_calls: null,
        created_at: new Date().toISOString(),
      };
      setState(s => ({
        ...s,
        messages: [...s.messages, userMsg],
        streaming: true,
        streamingText: '',
        streamingComponents: [],
        activeToolCall: null,
        error: null,
      }));
    } else {
      setState(s => ({
        ...s,
        streaming: true,
        streamingText: '',
        streamingComponents: [],
        activeToolCall: null,
        error: null,
      }));
    }

    try {
      let fullText = '';
      const components: UIComponent[] = [];

      for await (const event of streamChat(convId, text, confirmAction)) {
        if (abortRef.current) break;

        switch (event.event) {
          case 'token':
            fullText += (event.data as { text: string }).text;
            setState(s => ({ ...s, streamingText: fullText }));
            break;

          case 'tool_call':
            setState(s => ({
              ...s,
              activeToolCall: `${(event.data as { name: string }).name}: ${(event.data as { status: string }).status}`,
            }));
            break;

          case 'tool_result':
            setState(s => ({ ...s, activeToolCall: null }));
            break;

          case 'components':
            components.push(...(event.data as unknown as UIComponent[]));
            setState(s => ({ ...s, streamingComponents: [...components] }));
            break;

          case 'error':
            setState(s => ({
              ...s,
              error: (event.data as { message: string }).message,
            }));
            break;

          case 'done': {
            const doneData = event.data as { message_id: string; text: string };
            const assistantMsg: Message = {
              id: doneData.message_id || `done-${Date.now()}`,
              role: 'assistant',
              content: doneData.text || fullText,
              components: components.length > 0 ? components : null,
              tool_calls: null,
              created_at: new Date().toISOString(),
            };
            setState(s => ({
              ...s,
              messages: [...s.messages, assistantMsg],
              streaming: false,
              streamingText: '',
              streamingComponents: [],
              activeToolCall: null,
            }));

            // Update conversation title in sidebar for first message
            setState(prev => {
              if (prev.messages.length <= 2) {
                return {
                  ...prev,
                  conversations: prev.conversations.map(c =>
                    c.id === convId ? { ...c, title: text.slice(0, 100) || c.title } : c
                  ),
                  activeConversation: prev.activeConversation
                    ? { ...prev.activeConversation, title: text.slice(0, 100) || prev.activeConversation.title }
                    : prev.activeConversation,
                };
              }
              return prev;
            });
            return;
          }
        }
      }
    } catch (err) {
      setState(s => ({
        ...s,
        streaming: false,
        error: err instanceof Error ? err.message : 'Stream failed',
      }));
    }
  }, [state.activeConversation?.id, state.messages.length]);

  const stopStreaming = useCallback(() => {
    abortRef.current = true;
    setState(s => ({ ...s, streaming: false }));
  }, []);

  return {
    ...state,
    loadConversations,
    loadConversation,
    startNewConversation,
    removeConversation,
    sendMessage,
    stopStreaming,
  };
}
