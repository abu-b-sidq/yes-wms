import { auth } from './firebase';
import { getSession } from './client';
import type { SSEEvent } from '../types/chat';

/**
 * Stream chat messages via SSE (Server-Sent Events).
 * Uses fetch + ReadableStream because we need POST with custom headers.
 */
export async function* streamChat(
  conversationId: string,
  message: string,
  confirmAction?: { action: string; parameters: Record<string, unknown> },
  modelSelection?: { provider: string; model: string }
): AsyncGenerator<SSEEvent> {
  const user = auth.currentUser;
  if (!user) throw new Error('Not authenticated');

  const token = await user.getIdToken();
  const session = getSession();

  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    Authorization: `Bearer ${token}`,
  };
  if (session) {
    headers['warehouse'] = session.warehouseKey;
    headers['X-Org-Id'] = session.orgId;
    headers['X-Facility-Id'] = session.facilityId;
  }

  const body: Record<string, unknown> = {
    conversation_id: conversationId,
    message,
  };
  if (confirmAction) {
    body.confirm_action = confirmAction;
  }
  if (modelSelection) {
    body.model_provider = modelSelection.provider;
    body.model_name = modelSelection.model;
  }

  const apiBase = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8010';
  const response = await fetch(`${apiBase}/api/v1/ai/chat`, {
    method: 'POST',
    headers,
    body: JSON.stringify(body),
  });

  if (!response.ok) {
    throw new Error(`Chat request failed: ${response.status}`);
  }

  const reader = response.body?.getReader();
  if (!reader) throw new Error('No response body');

  const decoder = new TextDecoder();
  let buffer = '';

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });

    // Parse SSE events from buffer
    const lines = buffer.split('\n');
    buffer = lines.pop() || ''; // Keep incomplete line in buffer

    let currentEvent = '';
    let currentData = '';

    for (const line of lines) {
      if (line.startsWith('event: ')) {
        currentEvent = line.slice(7).trim();
      } else if (line.startsWith('data: ')) {
        currentData = line.slice(6).trim();
      } else if (line === '' && currentEvent && currentData) {
        try {
          yield {
            event: currentEvent,
            data: JSON.parse(currentData),
          };
        } catch {
          // Skip malformed JSON
        }
        currentEvent = '';
        currentData = '';
      }
    }
  }
}

/**
 * Non-streaming API calls for conversation management.
 */
import apiClient from './client';
import type { Conversation, ModelInfo } from '../types/chat';

export async function createConversation(
  modelProvider: string,
  modelName: string
): Promise<Conversation> {
  const resp = await apiClient.post('/ai/conversations', {
    model_provider: modelProvider,
    model_name: modelName,
  });
  return resp.data;
}

export async function listConversations(): Promise<Conversation[]> {
  const resp = await apiClient.get('/ai/conversations');
  return resp.data;
}

export async function getConversation(id: string): Promise<Conversation> {
  const resp = await apiClient.get(`/ai/conversations/${id}`);
  return resp.data;
}

export async function deleteConversation(id: string): Promise<void> {
  await apiClient.delete(`/ai/conversations/${id}`);
}

export async function updateConversationModel(
  id: string,
  modelProvider: string,
  modelName: string
): Promise<Conversation> {
  const resp = await apiClient.patch(`/ai/conversations/${id}`, {
    model_provider: modelProvider,
    model_name: modelName,
  });
  return resp.data;
}

export async function listModels(): Promise<ModelInfo[]> {
  const resp = await apiClient.get('/ai/models');
  return resp.data;
}
