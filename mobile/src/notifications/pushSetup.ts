import messaging from '@react-native-firebase/messaging';
import { Platform } from 'react-native';
import { saveFcmToken } from '../utils/storage';
import apiClient from '../api/client';

export async function requestNotificationPermission(): Promise<boolean> {
  const authStatus = await messaging().requestPermission();
  return (
    authStatus === messaging.AuthorizationStatus.AUTHORIZED ||
    authStatus === messaging.AuthorizationStatus.PROVISIONAL
  );
}

export async function registerForPushNotifications(): Promise<string | null> {
  try {
    const hasPermission = await requestNotificationPermission();
    if (!hasPermission) return null;

    const token = await messaging().getToken();
    await saveFcmToken(token);

    // Register with backend
    await apiClient.post('/mobile/notifications/register-device', {
      fcm_token: token,
      device_type: Platform.OS === 'ios' ? 'IOS' : 'ANDROID',
    });

    return token;
  } catch {
    return null;
  }
}

export function setupForegroundHandler(
  onNotification: (title: string, body: string, data: Record<string, string>) => void
) {
  return messaging().onMessage(async (remoteMessage) => {
    const title = remoteMessage.notification?.title || 'WMS';
    const body = remoteMessage.notification?.body || '';
    const data = (remoteMessage.data || {}) as Record<string, string>;
    onNotification(title, body, data);
  });
}

export function setupBackgroundHandler() {
  messaging().setBackgroundMessageHandler(async (_remoteMessage) => {
    // Background message handling — app will open when notification is tapped
  });
}

export async function getInitialNotification(): Promise<Record<string, string> | null> {
  const remoteMessage = await messaging().getInitialNotification();
  if (remoteMessage?.data) {
    return remoteMessage.data as Record<string, string>;
  }
  return null;
}

export function onNotificationOpened(
  handler: (data: Record<string, string>) => void
) {
  return messaging().onNotificationOpenedApp((remoteMessage) => {
    if (remoteMessage.data) {
      handler(remoteMessage.data as Record<string, string>);
    }
  });
}
