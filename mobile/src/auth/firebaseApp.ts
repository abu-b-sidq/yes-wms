import AsyncStorage from '@react-native-async-storage/async-storage';
import firebaseApp, { ReactNativeFirebase } from '@react-native-firebase/app';
import { Platform } from 'react-native';

type GoogleServicesProjectInfo = {
  project_number?: string;
  project_id?: string;
  storage_bucket?: string;
};

type GoogleServicesApiKey = {
  current_key?: string;
};

type GoogleServicesOAuthClient = {
  client_id?: string;
  client_type?: number;
};

type GoogleServicesAndroidClientInfo = {
  package_name?: string;
};

type GoogleServicesClientInfo = {
  mobilesdk_app_id?: string;
  android_client_info?: GoogleServicesAndroidClientInfo;
};

type GoogleServicesClient = {
  api_key?: GoogleServicesApiKey[];
  client_info?: GoogleServicesClientInfo;
  oauth_client?: GoogleServicesOAuthClient[];
};

type GoogleServicesConfig = {
  project_info?: GoogleServicesProjectInfo;
  client?: GoogleServicesClient[];
};

let googleServicesConfig: GoogleServicesConfig = {};

try {
  googleServicesConfig = require('../../android/app/google-services.json') as GoogleServicesConfig;
} catch (_err) {
  try {
    googleServicesConfig = require('../../google-services.json') as GoogleServicesConfig;
  } catch (_fallbackErr) {
    googleServicesConfig = {};
  }
}

const GOOGLE_ANDROID_CLIENT_TYPE = 1;
const GOOGLE_WEB_CLIENT_TYPE = 3;
const googleServices = googleServicesConfig;
const projectInfo = googleServices.project_info ?? {};
const defaultClient = googleServices.client?.[0];
const oauthClients = defaultClient?.oauth_client ?? [];

export const googleWebClientId =
  oauthClients.find(
    (oauthClient) => oauthClient.client_type === GOOGLE_WEB_CLIENT_TYPE
  )?.client_id ?? '';

export const googleAndroidPackageName =
  defaultClient?.client_info?.android_client_info?.package_name ?? '';

export const firebaseWebOptions: ReactNativeFirebase.FirebaseAppOptions & {
  authDomain?: string;
} = {
  appId: defaultClient?.client_info?.mobilesdk_app_id ?? '',
  apiKey: defaultClient?.api_key?.[0]?.current_key ?? '',
  authDomain: projectInfo.project_id ? `${projectInfo.project_id}.firebaseapp.com` : '',
  messagingSenderId: projectInfo.project_number ?? '',
  projectId: projectInfo.project_id ?? '',
  storageBucket: projectInfo.storage_bucket ?? '',
};

let firebaseWebAppReadyPromise: Promise<void> | null = null;

export function hasFirebaseWebConfig(): boolean {
  return Boolean(
    firebaseWebOptions.appId &&
      firebaseWebOptions.apiKey &&
      firebaseWebOptions.projectId &&
      firebaseWebOptions.authDomain
  );
}

export function hasGoogleWebClientId(): boolean {
  return Boolean(googleWebClientId);
}

export function hasGoogleAndroidClientConfig(): boolean {
  return oauthClients.some(
    (oauthClient) => oauthClient.client_type === GOOGLE_ANDROID_CLIENT_TYPE
  );
}

export function ensureFirebaseAppConfigured(): Promise<void> {
  if (Platform.OS !== 'web') {
    return Promise.resolve();
  }

  if (!hasFirebaseWebConfig()) {
    return Promise.reject(
      new Error('Firebase web configuration is missing for this build.')
    );
  }

  if (firebaseApp.apps.length > 0) {
    return Promise.resolve();
  }

  if (!firebaseWebAppReadyPromise) {
    firebaseApp.setReactNativeAsyncStorage(AsyncStorage);
    firebaseWebAppReadyPromise = firebaseApp
      .initializeApp(firebaseWebOptions)
      .then(() => undefined);
  }

  return firebaseWebAppReadyPromise;
}
