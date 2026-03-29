import React, { useEffect, useState, useCallback } from 'react';
import { useAuth } from '../../auth/AuthContext';
import { useChat } from '../../hooks/useChat';
import ChatContainer from '../chat/ChatContainer';
import ConversationList from '../chat/ConversationList';
import ModelSelector from '../chat/ModelSelector';
import NotificationPanel from './NotificationPanel';
import { getSession } from '../../api/client';

export default function AppLayout() {
  const { user, selectedFacility, signOut } = useAuth();
  const chat = useChat();
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [provider, setProvider] = useState('ollama');
  const [model, setModel] = useState('llama3.1');

  const session = getSession();

  // Load conversations on mount
  useEffect(() => {
    chat.loadConversations();
  }, [chat.loadConversations]);

  const handleNewChat = useCallback(async () => {
    await chat.startNewConversation(provider, model);
  }, [chat, provider, model]);

  const handleSelectConversation = useCallback(async (id: string) => {
    await chat.loadConversation(id);
  }, [chat]);

  const handleSend = useCallback(async (message: string) => {
    // If no active conversation, create one first
    if (!chat.activeConversation) {
      const conv = await chat.startNewConversation(provider, model);
      if (conv) {
        await chat.sendMessage(message, conv.id);
      }
    } else {
      await chat.sendMessage(message);
    }
  }, [chat, provider, model]);

  const handleConfirmAction = useCallback(async (action: string, parameters: Record<string, unknown>) => {
    if (chat.activeConversation) {
      await chat.sendMessage('', chat.activeConversation.id, { action, parameters });
    }
  }, [chat]);

  return (
    <div className="flex h-screen bg-gray-50">
      {/* Sidebar */}
      {sidebarOpen && (
        <div className="w-72 bg-white border-r border-gray-200 flex flex-col flex-shrink-0">
          {/* Logo */}
          <div className="px-4 py-4 border-b border-gray-100">
            <h1 className="text-xl font-bold text-gray-900">YES WMS</h1>
            <p className="text-xs text-gray-500 mt-0.5">AI Dashboard</p>
          </div>

          {/* Conversations */}
          <div className="flex-1 overflow-hidden">
            <ConversationList
              conversations={chat.conversations}
              activeId={chat.activeConversation?.id || null}
              onSelect={handleSelectConversation}
              onDelete={chat.removeConversation}
              onNew={handleNewChat}
            />
          </div>

          {/* User info */}
          <div className="p-3 border-t border-gray-100">
            <div className="text-sm text-gray-700 truncate">{user?.email}</div>
            <div className="text-xs text-gray-400 mt-0.5">{selectedFacility?.name}</div>
            <button
              onClick={signOut}
              className="mt-2 text-xs text-gray-500 hover:text-red-500 transition"
            >
              Sign out
            </button>
          </div>
        </div>
      )}

      {/* Main area */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Top bar */}
        <div className="h-14 bg-white border-b border-gray-200 flex items-center justify-between px-4 flex-shrink-0">
          <div className="flex items-center gap-3">
            <button
              onClick={() => setSidebarOpen(!sidebarOpen)}
              className="p-1.5 text-gray-500 hover:text-gray-700 transition"
            >
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M4 6h16M4 12h16M4 18h16" />
              </svg>
            </button>
            <div className="text-sm font-medium text-gray-700 truncate">
              {chat.activeConversation?.title || 'New Chat'}
            </div>
          </div>

          <div className="flex items-center gap-3">
            <ModelSelector
              provider={provider}
              model={model}
              onSelect={(p, m) => { setProvider(p); setModel(m); }}
            />
            <NotificationPanel facilityId={session?.facilityId || null} />
          </div>
        </div>

        {/* Chat */}
        <div className="flex-1 overflow-hidden">
          <ChatContainer
            messages={chat.messages}
            streaming={chat.streaming}
            streamingText={chat.streamingText}
            streamingComponents={chat.streamingComponents}
            activeToolCall={chat.activeToolCall}
            error={chat.error}
            onSend={handleSend}
            onConfirmAction={handleConfirmAction}
          />
        </div>
      </div>
    </div>
  );
}
