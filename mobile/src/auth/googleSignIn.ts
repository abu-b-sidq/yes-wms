import { getApp as getFirebaseWebApp, getApps as getFirebaseWebApps, initializeApp as initializeFirebaseWebApp } from 'firebase/app';
import {
  getAuth as getFirebaseWebAuth,
  GoogleAuthProvider as FirebaseWebGoogleAuthProvider,
  signInWithPopup as signInWithFirebaseWebPopup,
  signOut as signOutFirebaseWebAuth,
} from 'firebase/auth';
import { Platform } from 'react-native';
import { getErrorCode, getErrorMessage } from './errorMessages';
import {
  ensureFirebaseAppConfigured,
  firebaseWebOptions,
  googleAndroidPackageName,
  googleWebClientId,
  hasGoogleAndroidClientConfig,
  hasFirebaseWebConfig,
  hasGoogleWebClientId,
} from './firebaseApp';

type GoogleSignInModule = typeof import('@react-native-google-signin/google-signin');

let googleSignInModule: GoogleSignInModule | null = null;

if (Platform.OS !== 'web') {
  try {
    googleSignInModule = require('@react-native-google-signin/google-signin') as GoogleSignInModule;
  } catch (_err) {
    googleSignInModule = null;
  }
}

const GoogleSignin = googleSignInModule?.GoogleSignin ?? null;
const isCancelledResponse = googleSignInModule?.isCancelledResponse ?? null;
const isErrorWithCode = googleSignInModule?.isErrorWithCode ?? null;
const isSuccessResponse = googleSignInModule?.isSuccessResponse ?? null;
const statusCodes = googleSignInModule?.statusCodes ?? null;

let googleSignInConfigured = false;

function getAndroidGoogleConfigErrorMessage(): string {
  const packageName = googleAndroidPackageName || 'this Android app';

  return `Google sign-in is not fully configured for ${packageName}. Add this app's SHA-1 and SHA-256 fingerprints in Firebase, download a fresh google-services.json, and rebuild the Android app.`;
}

export function getGoogleSignInAvailabilityMessage(): string | null {
  if (Platform.OS === 'web') {
    if (!hasFirebaseWebConfig()) {
      return 'Firebase web auth config is missing for this build.';
    }

    return null;
  }

  if (!GoogleSignin) {
    return 'Google Sign-In native module is missing from this Android build. Reinstall node modules and rebuild the app.';
  }

  if (!hasGoogleWebClientId()) {
    return 'Google web client ID is missing from google-services.json.';
  }

  if (!hasGoogleAndroidClientConfig()) {
    return getAndroidGoogleConfigErrorMessage();
  }

  return null;
}

export function isGoogleSignInAvailable(): boolean {
  return getGoogleSignInAvailabilityMessage() === null;
}

export function configureGoogleSignIn(): boolean {
  if (!isGoogleSignInAvailable() || !GoogleSignin) {
    return false;
  }

  if (!googleSignInConfigured) {
    GoogleSignin.configure({
      webClientId: googleWebClientId,
    });
    googleSignInConfigured = true;
  }

  return true;
}

export async function signInWithGoogleIdToken(): Promise<string | null> {
  if (Platform.OS === 'web') {
    await ensureFirebaseAppConfigured();

    const firebaseWebApp =
      getFirebaseWebApps()[0] ?? initializeFirebaseWebApp(firebaseWebOptions);
    const firebaseWebAuth = getFirebaseWebAuth(firebaseWebApp);
    const provider = new FirebaseWebGoogleAuthProvider();

    provider.setCustomParameters({
      prompt: 'select_account',
    });

    const result = await signInWithFirebaseWebPopup(firebaseWebAuth, provider);
    const credential =
      FirebaseWebGoogleAuthProvider.credentialFromResult(result);

    return credential?.idToken ?? result.user.getIdToken();
  }

  if (!configureGoogleSignIn() || !GoogleSignin || !isSuccessResponse || !isCancelledResponse) {
    throw new Error('Google sign-in is unavailable in this build.');
  }

  await GoogleSignin.hasPlayServices({
    showPlayServicesUpdateDialog: true,
  });

  const response = await GoogleSignin.signIn();

  if (isCancelledResponse(response)) {
    return null;
  }

  if (!isSuccessResponse(response) || !response.data.idToken) {
    throw new Error(
      'Google sign-in did not return an ID token. Check the Firebase web client configuration.'
    );
  }

  return response.data.idToken;
}

export async function signOutGoogleSession(): Promise<void> {
  if (Platform.OS === 'web') {
    if (getFirebaseWebApps().length === 0) {
      return;
    }

    const firebaseWebAuth = getFirebaseWebAuth(getFirebaseWebApp());
    if (!firebaseWebAuth.currentUser) {
      return;
    }

    await signOutFirebaseWebAuth(firebaseWebAuth);
    return;
  }

  if (!GoogleSignin || !GoogleSignin.getCurrentUser()) {
    return;
  }

  await GoogleSignin.signOut();
}

export function getGoogleSignInErrorMessage(error: unknown): string {
  if (isErrorWithCode && statusCodes && isErrorWithCode(error)) {
    switch (error.code) {
      case statusCodes.IN_PROGRESS:
        return 'Google sign-in is already in progress.';
      case statusCodes.PLAY_SERVICES_NOT_AVAILABLE:
        return 'Google Play Services are unavailable or need an update on this device.';
      default:
        break;
    }
  }

  const code = getErrorCode(error);
  const message = getErrorMessage(error, 'Google sign-in failed. Please try again.');

  if (code === '10' || code === 'DEVELOPER_ERROR' || message.includes('DEVELOPER_ERROR')) {
    return getAndroidGoogleConfigErrorMessage();
  }

  if (code === 'auth/operation-not-allowed') {
    return 'Google sign-in is not enabled for this Firebase project.';
  }

  return message;
}
