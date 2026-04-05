import React, { useState } from 'react';
import { useAuth } from './AuthContext';
import AssistantAvatar from '../components/chat/AssistantAvatar';
import { ASSISTANT_NAME } from '../constants/branding';
import ThemeToggle from '../components/layout/ThemeToggle';

export default function LoginPage() {
  const { signIn, signInWithGoogle, loginError, loading } = useAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    await signIn(email, password);
  };

  const handleGoogleSignIn = async () => {
    await signInWithGoogle();
  };

  return (
    <div className="h-[100dvh] overflow-hidden px-3 py-3 md:px-4">
      <div className="mx-auto grid h-full max-w-7xl gap-4 lg:grid-cols-[1fr_0.92fr]">
        <section className="soft-panel relative overflow-hidden px-6 py-7 md:px-8 md:py-8">
          <div className="absolute right-6 top-6 z-10">
            <ThemeToggle />
          </div>
          <div className="absolute inset-x-16 top-0 h-32 rounded-full bg-[rgba(121,191,100,0.2)] blur-3xl" />
          <div className="relative flex h-full flex-col justify-between gap-6">
            <div className="space-y-4">
              <p className="ops-label text-xs">
                YES WMS / {ASSISTANT_NAME}
              </p>
              <div className="max-w-2xl space-y-3">
                <h1 className="text-3xl font-semibold leading-tight text-[var(--ops-text)] md:text-5xl">
                  The warehouse workspace that feels like the operations console talking back.
                </h1>
                <p className="max-w-xl text-sm leading-7 text-[var(--ops-text-muted)] md:text-base">
                  Track inbound activity, review inventory questions, and act faster with a
                  darker ops-first interface built around your floor operations.
                </p>
              </div>
            </div>

            <div className="grid gap-4 xl:grid-cols-[220px_1fr] xl:items-end">
              <div className="mx-auto xl:mx-0">
                <AssistantAvatar size="lg" className="float-gentle" />
              </div>

              <div className="grid gap-3">
                <div className="ops-note-card rounded-[26px] p-4">
                  <p className="ops-label text-xs text-[var(--ops-highlight)]">
                    {ASSISTANT_NAME}
                  </p>
                  <h2 className="mt-2 text-xl font-semibold text-[var(--ops-text)]">
                    I can narrate what is happening in your warehouse.
                  </h2>
                  <p className="mt-2 text-sm leading-6 text-[var(--ops-text-muted)]">
                    Ask me about open GRNs, zone congestion, slow-moving stock, or what needs
                    attention before the next shift handoff.
                  </p>
                </div>

                <div className="grid gap-3 sm:grid-cols-3">
                  <div className="ops-card-soft rounded-[22px] p-3.5">
                    <p className="ops-label text-xs">Style</p>
                    <p className="mt-1.5 text-sm font-medium text-[var(--ops-text)]">Dark, focused, operational</p>
                  </div>
                  <div className="ops-card-soft rounded-[22px] p-3.5">
                    <p className="ops-label text-xs">Feel</p>
                    <p className="mt-1.5 text-sm font-medium text-[var(--ops-text)]">Ops dashboard continuity</p>
                  </div>
                  <div className="ops-card-soft rounded-[22px] p-3.5">
                    <p className="ops-label text-xs">Focus</p>
                    <p className="mt-1.5 text-sm font-medium text-[var(--ops-text)]">Warehouse operations</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>

        <section className="soft-panel flex items-center overflow-hidden px-5 py-6 md:px-8">
          <div className="mx-auto w-full max-w-md">
            <div className="mb-6 space-y-2">
              <p className="ops-label text-xs">
                Welcome back
              </p>
              <h2 className="text-2xl font-semibold text-[var(--ops-text)] md:text-3xl">Sign in to YES WMS</h2>
              <p className="text-sm leading-6 text-[var(--ops-text-muted)]">
                Pick up your warehouse conversations, live alerts, and facility context right
                where you left them.
              </p>
            </div>

            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label htmlFor="email" className="mb-2 block text-sm font-medium text-[var(--ops-text-muted)]">
                  Email
                </label>
                <input
                  id="email"
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                  className="ops-input w-full rounded-2xl px-4 py-3 text-sm outline-none transition"
                  placeholder="you@company.com"
                  autoComplete="username"
                />
              </div>

              <div>
                <label htmlFor="password" className="mb-2 block text-sm font-medium text-[var(--ops-text-muted)]">
                  Password
                </label>
                <input
                  id="password"
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  className="ops-input w-full rounded-2xl px-4 py-3 text-sm outline-none transition"
                  placeholder="Enter your password"
                  autoComplete="current-password"
                />
              </div>

              {loginError && (
                <p className="rounded-2xl border border-[rgba(239,124,116,0.24)] bg-[rgba(239,124,116,0.12)] px-4 py-3 text-sm text-[var(--ops-danger)]">
                  {loginError}
                </p>
              )}

              <button
                type="submit"
                disabled={loading}
                className="ops-button-primary w-full rounded-2xl px-4 py-3 font-medium transition disabled:cursor-not-allowed disabled:opacity-50"
              >
                {loading ? 'Signing in...' : 'Sign In'}
              </button>
            </form>

            <div className="my-5 flex items-center gap-3">
              <div className="ops-divider h-px flex-1" />
              <span className="ops-label text-[11px]">Or</span>
              <div className="ops-divider h-px flex-1" />
            </div>

            <button
              type="button"
              onClick={handleGoogleSignIn}
              disabled={loading}
              className="ops-button-secondary flex w-full items-center justify-center gap-3 rounded-2xl py-3 font-medium transition disabled:cursor-not-allowed disabled:opacity-50"
            >
              <img
                src="https://www.gstatic.com/firebasejs/ui/2.0.0/images/auth/google.svg"
                alt="Google"
                className="h-5 w-5"
              />
              Continue with Google
            </button>
          </div>
        </section>
      </div>
    </div>
  );
}
