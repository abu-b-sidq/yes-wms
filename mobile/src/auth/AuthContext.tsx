import React, { createContext, useContext, useEffect, useState } from 'react';
import auth, { FirebaseAuthTypes } from '@react-native-firebase/auth';
import { sessionLogin, selectFacility, Facility } from '../api/auth';
import { saveSessionHeaders, clearSession } from '../utils/storage';
import { getFcmToken } from '../utils/storage';
import { getFirebaseAuthErrorMessage, getErrorMessage } from './errorMessages';
import { ensureFirebaseAppConfigured } from './firebaseApp';
import {
  configureGoogleSignIn,
  getGoogleSignInAvailabilityMessage,
  getGoogleSignInErrorMessage,
  isGoogleSignInAvailable,
  signInWithGoogleIdToken,
  signOutGoogleSession,
} from './googleSignIn';

interface AuthState {
  user: FirebaseAuthTypes.User | null;
  loading: boolean;
  facilities: Facility[];
  selectedFacility: Facility | null;
  loginError: string | null;
  googleSignInAvailable: boolean;
  googleSignInMessage: string | null;
}

interface AuthContextValue extends AuthState {
  signIn: (email: string, password: string) => Promise<void>;
  signInWithGoogle: () => Promise<void>;
  signOut: () => Promise<void>;
  chooseFacility: (facility: Facility) => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | null>(null);
const INITIAL_GOOGLE_SIGN_IN_MESSAGE = getGoogleSignInAvailabilityMessage();
const INITIAL_GOOGLE_SIGN_IN_AVAILABLE =
  INITIAL_GOOGLE_SIGN_IN_MESSAGE === null &&
  (configureGoogleSignIn() || isGoogleSignInAvailable());

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [state, setState] = useState<AuthState>({
    user: null,
    loading: true,
    facilities: [],
    selectedFacility: null,
    loginError: null,
    googleSignInAvailable: INITIAL_GOOGLE_SIGN_IN_AVAILABLE,
    googleSignInMessage: INITIAL_GOOGLE_SIGN_IN_MESSAGE,
  });

  useEffect(() => {
    let unsubscribe: () => void = () => {};
    let mounted = true;

    void ensureFirebaseAppConfigured()
      .then(() => {
        if (!mounted) {
          return;
        }

        unsubscribe = auth().onAuthStateChanged(async (firebaseUser) => {
          if (firebaseUser) {
            try {
              const fcmToken = await getFcmToken();
              const response = await sessionLogin(fcmToken || undefined);
              const { last_used_facility, available_facilities } = response.data;

              if (available_facilities.length === 1) {
                // Auto-select single facility
                await _selectAndSave(available_facilities[0]);
                setState({
                  user: firebaseUser,
                  loading: false,
                  facilities: available_facilities,
                  selectedFacility: available_facilities[0],
                  loginError: null,
                  googleSignInAvailable: INITIAL_GOOGLE_SIGN_IN_AVAILABLE,
                  googleSignInMessage: INITIAL_GOOGLE_SIGN_IN_MESSAGE,
                });
              } else if (last_used_facility) {
                // Restore last facility
                await _selectAndSave(last_used_facility);
                setState({
                  user: firebaseUser,
                  loading: false,
                  facilities: available_facilities,
                  selectedFacility: last_used_facility,
                  loginError: null,
                  googleSignInAvailable: INITIAL_GOOGLE_SIGN_IN_AVAILABLE,
                  googleSignInMessage: INITIAL_GOOGLE_SIGN_IN_MESSAGE,
                });
              } else {
                // Need to pick a facility
                setState({
                  user: firebaseUser,
                  loading: false,
                  facilities: available_facilities,
                  selectedFacility: null,
                  loginError: null,
                  googleSignInAvailable: INITIAL_GOOGLE_SIGN_IN_AVAILABLE,
                  googleSignInMessage: INITIAL_GOOGLE_SIGN_IN_MESSAGE,
                });
              }
            } catch (error: unknown) {
              const loginError = getErrorMessage(
                error,
                'We could not start your warehouse session. Please try again.'
              );

              setState({
                user: firebaseUser,
                loading: false,
                facilities: [],
                selectedFacility: null,
                loginError,
                googleSignInAvailable: INITIAL_GOOGLE_SIGN_IN_AVAILABLE,
                googleSignInMessage: INITIAL_GOOGLE_SIGN_IN_MESSAGE,
              });
            }
          } else {
            await clearSession();
            setState({
              user: null,
              loading: false,
              facilities: [],
              selectedFacility: null,
              loginError: null,
              googleSignInAvailable: INITIAL_GOOGLE_SIGN_IN_AVAILABLE,
              googleSignInMessage: INITIAL_GOOGLE_SIGN_IN_MESSAGE,
            });
          }
        });
      })
      .catch((error: unknown) => {
        if (!mounted) {
          return;
        }

        const loginError = getErrorMessage(
          error,
          'We could not configure Firebase for this build.'
        );

        setState({
          user: null,
          loading: false,
          facilities: [],
          selectedFacility: null,
          loginError,
          googleSignInAvailable: false,
          googleSignInMessage: getGoogleSignInAvailabilityMessage(),
        });
      });

    return () => {
      mounted = false;
      unsubscribe();
    };
  }, []);

  const signIn = async (email: string, password: string) => {
    setState((s) => ({ ...s, loading: true, loginError: null }));
    try {
      await ensureFirebaseAppConfigured();
      await auth().signInWithEmailAndPassword(email, password);
    } catch (error: unknown) {
      const loginError = getFirebaseAuthErrorMessage(error);

      setState((s) => ({
        ...s,
        loading: false,
        loginError,
      }));
    }
  };

  const signInWithGoogle = async () => {
    setState((s) => ({ ...s, loading: true, loginError: null }));

    try {
      await ensureFirebaseAppConfigured();
      const idToken = await signInWithGoogleIdToken();

      if (!idToken) {
        setState((s) => ({
          ...s,
          loading: false,
          loginError: null,
        }));
        return;
      }

      const credential = auth.GoogleAuthProvider.credential(idToken);
      await auth().signInWithCredential(credential);
    } catch (error: unknown) {
      const loginError = getGoogleSignInErrorMessage(error);

      setState((s) => ({
        ...s,
        loading: false,
        loginError,
      }));
    }
  };

  const signOut = async () => {
    try {
      await signOutGoogleSession();
    } catch (_err) {
      // Firebase sign-out is the important step; stale Google session should not block logout.
    }

    await auth().signOut();
    await clearSession();
    setState({
      user: null,
      loading: false,
      facilities: [],
      selectedFacility: null,
      loginError: null,
      googleSignInAvailable: INITIAL_GOOGLE_SIGN_IN_AVAILABLE,
      googleSignInMessage: INITIAL_GOOGLE_SIGN_IN_MESSAGE,
    });
  };

  const chooseFacility = async (facility: Facility) => {
    setState((s) => ({ ...s, loading: true }));
    try {
      await _selectAndSave(facility);
      setState((s) => ({
        ...s,
        loading: false,
        selectedFacility: facility,
      }));
    } catch (error: unknown) {
      const loginError = getErrorMessage(
        error,
        'We could not activate that facility. Please try again.'
      );

      setState((s) => ({
        ...s,
        loading: false,
        loginError,
      }));
    }
  };

  return (
    <AuthContext.Provider
      value={{ ...state, signIn, signInWithGoogle, signOut, chooseFacility }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
}

async function _selectAndSave(facility: Facility) {
  const response = await selectFacility(facility.id);
  await saveSessionHeaders({
    warehouseKey: response.data.warehouse_key,
    orgId: response.data.org_id,
    facilityId: facility.code,
    facilityCode: facility.code,
  });
}
