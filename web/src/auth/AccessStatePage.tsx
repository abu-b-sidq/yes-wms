import React from 'react';
import { useAuth } from './AuthContext';

export default function AccessStatePage() {
  const { user, accessState, retrySessionBootstrap, signOut, loading } = useAuth();

  if (!accessState) {
    return null;
  }

  const accentClass =
    accessState.kind === 'access_limited'
      ? 'bg-amber-100 text-amber-700'
      : 'bg-red-100 text-red-700';

  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-100 px-4">
      <div className="w-full max-w-lg rounded-3xl border border-slate-200 bg-white p-8 shadow-xl">
        <div className={`w-12 h-12 rounded-2xl flex items-center justify-center ${accentClass}`}>
          <svg className="w-6 h-6" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.8}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v4m0 4h.01M10.29 3.86l-7.5 13A1 1 0 003.65 18h16.7a1 1 0 00.86-1.14l-7.5-13a1 1 0 00-1.72 0z" />
          </svg>
        </div>

        <h1 className="mt-6 text-2xl font-bold text-slate-900">{accessState.title}</h1>
        <p className="mt-3 text-sm leading-6 text-slate-600">{accessState.description}</p>

        {user?.email && (
          <div className="mt-6 rounded-2xl bg-slate-50 px-4 py-3 text-sm text-slate-600">
            Signed in as <span className="font-medium text-slate-900">{user.email}</span>
          </div>
        )}

        <div className="mt-8 flex flex-col gap-3 sm:flex-row">
          <button
            type="button"
            onClick={() => void retrySessionBootstrap()}
            disabled={loading}
            className="flex-1 rounded-xl bg-primary-600 px-4 py-3 font-medium text-white transition hover:bg-primary-700 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {loading ? 'Retrying...' : 'Retry'}
          </button>
          <button
            type="button"
            onClick={() => void signOut()}
            className="flex-1 rounded-xl border border-slate-300 px-4 py-3 font-medium text-slate-700 transition hover:bg-slate-50"
          >
            Sign out
          </button>
        </div>
      </div>
    </div>
  );
}
