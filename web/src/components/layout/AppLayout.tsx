import React, { useCallback, useEffect, useState } from 'react';
import { useAuth } from '../../auth/AuthContext';
import { getSession } from '../../api/client';
import { useChat } from '../../hooks/useChat';
import ChatContainer from '../chat/ChatContainer';
import ConversationList from '../chat/ConversationList';
import ModelSelector from '../chat/ModelSelector';
import AssistantAvatar from '../chat/AssistantAvatar';
import NotificationPanel from './NotificationPanel';
import { ASSISTANT_NAME } from '../../constants/branding';

function resolveDisplayName(displayName?: string | null, email?: string | null): string {
  if (displayName?.trim()) {
    return displayName.trim().split(/\s+/)[0];
  }

  if (email) {
    return email.split('@')[0].replace(/[._-]+/g, ' ');
  }

  return 'there';
}

interface RailButtonProps {
  active?: boolean;
  label: string;
  onClick: () => void;
  icon: React.ReactNode;
}

function RailButton({ active = false, label, onClick, icon }: RailButtonProps) {
  return (
    <button
      type="button"
      aria-label={label}
      onClick={onClick}
      className={`flex h-12 w-12 items-center justify-center rounded-[18px] border transition ${
        active
          ? 'border-[rgba(212,234,114,0.18)] bg-[rgba(121,191,100,0.16)] text-[var(--ops-highlight)] shadow-[0_12px_28px_rgba(91,159,78,0.24)]'
          : 'border-[var(--ops-border)] bg-[var(--ops-glass-soft)] text-[var(--ops-text-muted)] hover:border-[var(--ops-border-strong)] hover:bg-[var(--ops-glass-hover)] hover:text-[var(--ops-text)]'
      }`}
    >
      {icon}
    </button>
  );
}

export default function AppLayout() {
  const { user, selectedFacility, signOut } = useAuth();
  const chat = useChat();
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [provider, setProvider] = useState('ollama');
  const [model, setModel] = useState('llama3.1');
  const [searchTerm, setSearchTerm] = useState('');

  const session = getSession();
  const displayName = resolveDisplayName(user?.displayName, user?.email);
  const activeTitle = chat.activeConversation?.title || 'New thread';
  const facilityName = selectedFacility?.name || session?.facilityName || 'your warehouse';
  const filteredConversations = chat.conversations.filter((conversation) => {
    const query = searchTerm.trim().toLowerCase();

    if (!query) {
      return true;
    }

    return (
      conversation.title.toLowerCase().includes(query) ||
      conversation.model_provider.toLowerCase().includes(query) ||
      conversation.model_name.toLowerCase().includes(query)
    );
  });

  useEffect(() => {
    void chat.loadConversations();
  }, [chat.loadConversations]);

  useEffect(() => {
    if (!chat.activeConversation) {
      return;
    }

    setProvider(chat.activeConversation.model_provider);
    setModel(chat.activeConversation.model_name);
  }, [
    chat.activeConversation?.id,
    chat.activeConversation?.model_name,
    chat.activeConversation?.model_provider,
  ]);

  const handleNewChat = useCallback(async () => {
    await chat.startNewConversation(provider, model);
  }, [chat, model, provider]);

  const handleSelectConversation = useCallback(
    async (id: string) => {
      await chat.loadConversation(id);

      if (window.innerWidth < 768) {
        setSidebarOpen(false);
      }
    },
    [chat]
  );

  const handleSend = useCallback(
    async (message: string) => {
      if (!chat.activeConversation) {
        const conversation = await chat.startNewConversation(provider, model);

        if (conversation) {
          await chat.sendMessage(message, conversation.id, undefined, { provider, model });
        }

        return;
      }

      await chat.sendMessage(message, undefined, undefined, { provider, model });
    },
    [chat, model, provider]
  );

  const handleConfirmAction = useCallback(
    async (action: string, parameters: Record<string, unknown>) => {
      if (chat.activeConversation) {
        await chat.sendMessage('', chat.activeConversation.id, { action, parameters });
      }
    },
    [chat]
  );

  const handleModelSelect = useCallback(
    async (nextProvider: string, nextModel: string) => {
      const activeConversation = chat.activeConversation;
      const previousProvider = activeConversation?.model_provider ?? provider;
      const previousModel = activeConversation?.model_name ?? model;

      setProvider(nextProvider);
      setModel(nextModel);

      if (
        activeConversation &&
        (activeConversation.model_provider !== nextProvider ||
          activeConversation.model_name !== nextModel)
      ) {
        const updated = await chat.updateConversationModel(
          activeConversation.id,
          nextProvider,
          nextModel
        );

        if (!updated) {
          setProvider(previousProvider);
          setModel(previousModel);
        }
      }
    },
    [chat, model, provider]
  );

  return (
    <div className="h-[100dvh] overflow-hidden p-2.5 md:p-3">
      {sidebarOpen && (
        <button
          type="button"
          aria-label="Close conversations"
          onClick={() => setSidebarOpen(false)}
          className="fixed inset-0 z-30 bg-[var(--ops-overlay)] backdrop-blur-[2px] md:hidden"
        />
      )}

      <div className="flex h-full gap-2.5">
        <aside className="soft-panel hidden w-[80px] flex-col items-center justify-between px-2.5 py-3 md:flex">
          <div className="flex flex-col items-center gap-3">
            <div className="flex h-12 w-12 items-center justify-center rounded-[20px] border border-[rgba(212,234,114,0.18)] bg-[linear-gradient(180deg,rgba(121,191,100,0.98)_0%,rgba(95,159,78,0.98)_100%)] text-[var(--ops-primary-contrast)] shadow-[0_16px_32px_rgba(91,159,78,0.22)]">
              <svg className="h-6 w-6" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.8}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M5 12h14M12 5l7 7-7 7" />
              </svg>
            </div>

            <RailButton
              active={sidebarOpen}
              label="Toggle conversations"
              onClick={() => setSidebarOpen((current) => !current)}
              icon={
                <svg className="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.8}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M4 6h16M4 12h10M4 18h16" />
                </svg>
              }
            />

            <RailButton
              label="Start new conversation"
              onClick={() => void handleNewChat()}
              icon={
                <svg className="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.8}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M12 5v14M5 12h14" />
                </svg>
              }
            />

            <div className="my-1 h-px w-8 bg-[var(--ops-line-soft)]" />

            <div className="ops-card-soft rounded-[20px] px-3 py-2 text-center">
              <div className="ops-label text-[10px]">
                Live
              </div>
              <div className="mx-auto mt-2 h-2.5 w-2.5 rounded-full bg-[var(--ops-success)]" />
            </div>
          </div>

          <div className="flex flex-col items-center gap-3">
            <div className="ops-chip rounded-[18px] px-3 py-2 text-[10px] font-semibold uppercase tracking-[0.24em]">
              {ASSISTANT_NAME}
            </div>
            <AssistantAvatar size="sm" />
          </div>
        </aside>

        <aside
          className={`soft-panel fixed inset-y-3 left-3 z-40 w-[min(88vw,300px)] flex-col overflow-hidden md:static md:z-auto md:w-[300px] ${
            sidebarOpen ? 'flex' : 'hidden'
          }`}
        >
          <div className="border-b border-[var(--ops-line-soft)] px-5 pb-3 pt-5">
            <div className="flex items-start justify-between gap-4">
              <div>
                <p className="ops-label text-xs">
                  Conversations
                </p>
                <h2 className="mt-2 text-xl font-semibold text-[var(--ops-text)]">Warehouse Threads</h2>
                <p className="mt-1 text-sm leading-5 text-[var(--ops-text-muted)]">
                  Browse active questions, summaries, and follow-ups for {facilityName}.
                </p>
              </div>
              <button
                type="button"
                onClick={() => setSidebarOpen(false)}
                className="rounded-full border border-[var(--ops-border)] p-2 text-[var(--ops-text-soft)] transition hover:text-[var(--ops-text)] md:hidden"
              >
                <svg className="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.8}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
          </div>

          <div className="min-h-0 flex-1 px-3 py-2.5">
            <ConversationList
              conversations={filteredConversations}
              activeId={chat.activeConversation?.id || null}
              onSelect={handleSelectConversation}
              onDelete={chat.removeConversation}
              onNew={handleNewChat}
            />
          </div>

          <div className="border-t border-[var(--ops-line-soft)] p-4">
            <div className="flex items-center gap-3">
              <AssistantAvatar size="sm" />
              <div className="min-w-0">
                <div className="truncate text-sm font-medium text-[var(--ops-text)]">{user?.email}</div>
                <div className="truncate text-xs text-[var(--ops-text-muted)]">{facilityName}</div>
              </div>
            </div>
            <button
              type="button"
              onClick={signOut}
              className="mt-3 text-sm text-[var(--ops-text-muted)] transition hover:text-[var(--ops-text)]"
            >
              Sign out
            </button>
          </div>
        </aside>

        <main className="soft-panel flex min-w-0 flex-1 flex-col overflow-hidden">
          <header className="border-b border-[var(--ops-line-soft)] px-4 py-3 md:px-5">
            <div className="flex flex-col gap-3 xl:flex-row xl:items-center xl:justify-between">
              <div className="min-w-0">
                <div className="flex items-center gap-3">
                  <button
                    type="button"
                    onClick={() => setSidebarOpen(true)}
                    className="ops-button-secondary flex h-11 w-11 items-center justify-center rounded-[18px] transition md:hidden"
                  >
                    <svg className="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.8}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M4 6h16M4 12h10M4 18h16" />
                    </svg>
                  </button>

                  <div>
                    <p className="ops-label text-xs">
                      YES WMS
                    </p>
                    <div className="mt-1 flex items-center gap-2 text-sm text-[var(--ops-text-muted)]">
                      <span className="inline-flex h-2 w-2 rounded-full bg-[var(--ops-success)]" />
                      <span className="truncate">
                        {chat.activeConversation ? activeTitle : facilityName}
                      </span>
                    </div>
                  </div>
                </div>
              </div>

              <div className="flex w-full flex-col gap-2.5 xl:w-auto xl:items-end">
                <label className="ops-input-shell flex w-full items-center gap-3 rounded-[20px] px-4 py-2.5 text-sm xl:min-w-[320px]">
                  <svg className="h-4 w-4 text-[var(--ops-text-soft)]" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.8}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="m21 21-4.35-4.35m1.85-5.65a7.5 7.5 0 11-15 0 7.5 7.5 0 0115 0z" />
                  </svg>
                  <input
                    type="text"
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    placeholder="Search thread"
                    className="w-full bg-transparent text-sm text-[var(--ops-text)] outline-none placeholder:text-[var(--ops-text-soft)]"
                  />
                </label>

                <div className="flex flex-wrap items-center gap-2">
                  <ModelSelector
                    provider={provider}
                    model={model}
                    onSelect={handleModelSelect}
                  />
                  <NotificationPanel facilityId={session?.facilityId || null} />
                  <button
                    type="button"
                    onClick={() => void handleNewChat()}
                    className="ops-button-primary rounded-[18px] px-4 py-2.5 text-sm font-medium transition"
                  >
                    New Thread
                  </button>
                </div>
              </div>
            </div>
          </header>

          <div className="min-h-0 flex-1">
            <ChatContainer
              messages={chat.messages}
              streaming={chat.streaming}
              streamingText={chat.streamingText}
              streamingComponents={chat.streamingComponents}
              activeToolCall={chat.activeToolCall}
              error={chat.error}
              onSend={handleSend}
              onConfirmAction={handleConfirmAction}
              viewerName={displayName}
              facilityName={facilityName}
            />
          </div>
        </main>
      </div>
    </div>
  );
}
