import React from 'react';
import { useAuth } from './AuthContext';
import AssistantAvatar from '../components/chat/AssistantAvatar';
import { ASSISTANT_NAME } from '../constants/branding';

export default function AccessStatePage() {
  const { user, accessState, retrySessionBootstrap, signOut, loading } = useAuth();

  if (!accessState) {
    return null;
  }

  const accentClass =
    accessState.kind === 'access_limited'
      ? 'border border-[rgba(228,180,82,0.24)] bg-[rgba(228,180,82,0.12)] text-[var(--ops-warning)]'
      : 'border border-[rgba(239,124,116,0.24)] bg-[rgba(239,124,116,0.12)] text-[var(--ops-danger)]';

  return (
    <div className="h-[100dvh] overflow-hidden px-3 py-3 md:px-4">
      <div className="mx-auto grid h-full max-w-6xl gap-4 lg:grid-cols-[0.92fr_1.08fr]">
        <section className="soft-panel flex flex-col justify-between gap-6 overflow-hidden px-6 py-7 md:px-7 md:py-8">
          <div className="space-y-4">
            <p className="ops-label text-xs">
              Session Check
            </p>
            <h1 className="max-w-xl text-3xl font-semibold leading-tight text-[var(--ops-text)] md:text-4xl">
              {ASSISTANT_NAME} is ready, but your warehouse access needs attention.
            </h1>
            <p className="max-w-lg text-sm leading-6 text-[var(--ops-text-muted)]">
              We kept the workspace aligned with the operations console, but we still need a valid
              facility session before the live assistant can respond with warehouse data.
            </p>
          </div>

          <div className="grid gap-4 md:grid-cols-[180px_1fr] md:items-end">
            <AssistantAvatar size="md" className="mx-auto md:mx-0" />
            <div className="ops-note-card rounded-[24px] p-4">
              <p className="ops-label text-xs text-[var(--ops-highlight)]">
                {ASSISTANT_NAME}
              </p>
              <p className="mt-2 text-sm leading-6 text-[var(--ops-text-muted)]">
                Once access is restored, I'll jump back into inventory summaries, transaction
                status, and facility-specific guidance right away.
              </p>
            </div>
          </div>
        </section>

        <section className="soft-panel flex items-center overflow-hidden px-5 py-6 md:px-8">
          <div className="w-full">
            <div className={`flex h-14 w-14 items-center justify-center rounded-[20px] ${accentClass}`}>
              <svg className="h-6 w-6" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.8}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v4m0 4h.01M10.29 3.86l-7.5 13A1 1 0 003.65 18h16.7a1 1 0 00.86-1.14l-7.5-13a1 1 0 00-1.72 0z" />
              </svg>
            </div>

            <h2 className="mt-5 text-2xl font-semibold text-[var(--ops-text)] md:text-3xl">{accessState.title}</h2>
            <p className="mt-3 max-w-xl text-sm leading-6 text-[var(--ops-text-muted)]">{accessState.description}</p>

            {user?.email && (
              <div className="ops-card-soft mt-5 rounded-[22px] px-4 py-3.5 text-sm text-[var(--ops-text-muted)]">
                Signed in as <span className="font-medium text-[var(--ops-text)]">{user.email}</span>
              </div>
            )}

            <div className="mt-6 flex flex-col gap-3 sm:flex-row">
              <button
                type="button"
                onClick={() => void retrySessionBootstrap()}
                disabled={loading}
                className="ops-button-primary flex-1 rounded-2xl px-4 py-3 font-medium transition disabled:cursor-not-allowed disabled:opacity-50"
              >
                {loading ? 'Retrying...' : 'Retry'}
              </button>
              <button
                type="button"
                onClick={() => void signOut()}
                className="ops-button-secondary flex-1 rounded-2xl px-4 py-3 font-medium transition"
              >
                Sign out
              </button>
            </div>
          </div>
        </section>
      </div>
    </div>
  );
}
