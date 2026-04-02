import React from 'react';
import { AuthProvider, useAuth } from './auth/AuthContext';
import AccessStatePage from './auth/AccessStatePage';
import LoginPage from './auth/LoginPage';
import FacilityPicker from './auth/FacilityPicker';
import AppLayout from './components/layout/AppLayout';

function AppContent() {
  const { authStatus, loading } = useAuth();

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-100">
        <div className="flex flex-col items-center gap-3">
          <div className="w-8 h-8 border-3 border-primary-600 border-t-transparent rounded-full animate-spin" />
          <p className="text-slate-500 text-sm">Preparing your warehouse session...</p>
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
