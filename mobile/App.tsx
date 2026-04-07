import React, { useEffect } from 'react';
import { StatusBar } from 'react-native';
import { AuthProvider } from './src/auth/AuthContext';
import { AppNavigator } from './src/navigation/AppNavigator';
import { colors } from './src/theme';
import {
  registerForPushNotifications,
  setupBackgroundHandler,
} from './src/notifications/pushSetup';

// Set up background message handler (must be called outside component)
setupBackgroundHandler();

export default function App() {
  useEffect(() => {
    registerForPushNotifications();
  }, []);

  return (
    <AuthProvider>
      <StatusBar barStyle="light-content" backgroundColor={colors.bg} />
      <AppNavigator />
    </AuthProvider>
  );
}
