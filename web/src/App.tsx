import React from 'react';
import { AuthProvider, useAuth } from './auth/AuthContext';
import AccessStatePage from './auth/AccessStatePage';
import LoginPage from './auth/LoginPage';
import FacilityPicker from './auth/FacilityPicker';
import AppLayout from './components/layout/AppLayout';
import AssistantAvatar from './components/chat/AssistantAvatar';
import { ASSISTANT_NAME } from './constants/branding';

function AppContent() {
  const { authStatus, loading } = useAuth();

  if (loading) {
    return (
      <div className="min-h-screen px-4 py-8">
        <div className="mx-auto flex min-h-[calc(100vh-4rem)] max-w-5xl items-center justify-center">
          <div className="soft-panel flex w-full max-w-3xl flex-col items-center gap-6 px-8 py-12 text-center">
            <div className="relative">
              <div className="pulse-soft absolute inset-6 rounded-full bg-[rgba(121,191,100,0.22)] blur-3xl" />
              <AssistantAvatar size="lg" className="float-gentle relative" />
            </div>
            <div className="space-y-3">
              <p className="ops-label text-xs">
                YES WMS
              </p>
              <h1 className="text-3xl font-semibold text-[var(--ops-text)]">
                Preparing {ASSISTANT_NAME} for your warehouse
              </h1>
              <p className="mx-auto max-w-xl text-sm leading-7 text-[var(--ops-text-muted)]">
                We are restoring your facility, conversations, and live activity so the workspace
                is ready when you land.
              </p>
            </div>
            <div className="ops-chip flex items-center gap-3 rounded-full px-5 py-3 text-sm">
              <div className="h-4 w-4 animate-spin rounded-full border-2 border-[var(--ops-primary)] border-t-transparent" />
              Preparing your warehouse session...
            </div>
          </div>
        </div>
      </div>
    );
  }

  switch (authStatus) {
    case 'unauthenticated':
      return <LoginPage />;
    case 'choosing_facility':
      return <FacilityPicker />;
    case 'access_limited':
    case 'session_error':
      return <AccessStatePage />;
    case 'ready':
      return <AppLayout />;
    default:
      return <LoginPage />;
  }
}

export default function App() {
  return (
    <AuthProvider>
      <AppContent />
    </AuthProvider>
  );
}
