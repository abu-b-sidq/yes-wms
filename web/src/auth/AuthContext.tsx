import React, { createContext, useCallback, useContext, useEffect, useRef, useState } from 'react';
import {
  GoogleAuthProvider,
  onAuthStateChanged,
  signInWithEmailAndPassword,
  signInWithPopup,
  signOut as firebaseSignOut,
  type User,
} from 'firebase/auth';
import { auth } from '../api/firebase';
import { selectFacility, sessionLogin } from '../api/auth';
import { clearSession, saveSession } from '../api/client';
import type { Facility, SelectFacilityResponse } from '../types/wms';
import { getErrorCode, getErrorMessage, getFirebaseAuthErrorMessage } from './errorMessages';

export type AuthStatus =
  | 'unauthenticated'
  | 'choosing_facility'
  | 'ready'
  | 'access_limited'
  | 'session_error';

interface AccessState {
  kind: 'access_limited' | 'session_error';
  title: string;
  description: string;
}

interface AuthState {
  user: User | null;
  loading: boolean;
  authStatus: AuthStatus;
  facilities: Facility[];
  selectedFacility: Facility | null;
  loginError: string | null;
  facilityLoading: boolean;
  accessState: AccessState | null;
}

interface AuthContextValue extends AuthState {
  signIn: (email: string, password: string) => Promise<void>;
  signInWithGoogle: () => Promise<void>;
  signOut: () => Promise<void>;
  chooseFacility: (facility: Facility) => Promise<void>;
  retrySessionBootstrap: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | null>(null);

function createAuthState(overrides: Partial<AuthState> = {}): AuthState {
  return {
    user: null,
    loading: false,
    authStatus: 'unauthenticated',
    facilities: [],
    selectedFacility: null,
    loginError: null,
    facilityLoading: false,
    accessState: null,
    ...overrides,
  };
}

function resolvePreferredFacility(
  facilities: Facility[],
  lastUsedFacility: Facility | null
): Facility | null {
  if (facilities.length === 1) {
    return facilities[0];
  }

  if (!lastUsedFacility) {
    return null;
  }

  return facilities.find((facility) => facility.id === lastUsedFacility.id) ?? null;
}

function buildAccessState(error: unknown): Pick<AuthState, 'authStatus' | 'accessState'> {
  const code = getErrorCode(error);

  if (code === 'AUTHZ_PENDING_USER') {
    return {
      authStatus: 'access_limited',
      accessState: {
        kind: 'access_limited',
        title: 'Access pending approval',
        description:
          'Your account is signed in, but a YES WMS administrator still needs to approve access before you can continue.',
      },
    };
  }

  if (code === 'AUTHZ_SUSPENDED_USER') {
    return {
      authStatus: 'access_limited',
      accessState: {
        kind: 'access_limited',
        title: 'Access suspended',
        description:
          'This YES WMS account has been suspended. Contact your administrator if this looks unexpected.',
      },
    };
  }

  return {
    authStatus: 'session_error',
    accessState: {
      kind: 'session_error',
      title: 'We could not start your warehouse session',
      description: getErrorMessage(
        error,
        'Please try again. If the problem keeps happening, check your Firebase auth setup and network connection.'
      ),
    },
  };
}

function buildNoFacilityAccessState(): AccessState {
  return {
    kind: 'access_limited',
    title: 'No facility access yet',
    description:
      'Your account is authenticated, but no warehouse facilities are assigned to it yet. Ask a YES WMS administrator to grant facility access.',
  };
}

function buildFacilitySelectionError(error: unknown): AccessState {
  return {
    kind: 'session_error',
    title: 'We could not activate that facility',
    description: getErrorMessage(
      error,
      'Please try again. If this keeps failing, your facility access may have changed on the server.'
    ),
  };
}

function saveFacilitySession(response: SelectFacilityResponse): void {
  saveSession({
    warehouseKey: response.warehouse_key,
    orgId: response.org_id,
    facilityId: response.facility.code,
    facilityName: response.facility.name,
  });
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
}

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [state, setState] = useState<AuthState>(() => createAuthState({ loading: true }));
  const requestIdRef = useRef(0);

  const isActiveRequest = useCallback((requestId: number) => {
    return requestIdRef.current === requestId;
  }, []);

  const resetToUnauthenticated = useCallback(() => {
    requestIdRef.current += 1;
    clearSession();
    setState(createAuthState());
  }, []);

  const bootstrapSession = useCallback(
    async (firebaseUser: User) => {
      const requestId = ++requestIdRef.current;
      clearSession();
      setState(createAuthState({ user: firebaseUser, loading: true }));

      try {
        const response = await sessionLogin();
        if (!isActiveRequest(requestId)) {
          return;
        }

        const facilities = response.available_facilities ?? [];
        const preferredFacility = resolvePreferredFacility(facilities, response.last_used_facility);

        if (preferredFacility) {
          try {
            const facilityResponse = await selectFacility(preferredFacility.id);
            if (!isActiveRequest(requestId)) {
              return;
            }

            saveFacilitySession(facilityResponse);
            setState(
              createAuthState({
                user: firebaseUser,
                authStatus: 'ready',
                facilities,
                selectedFacility: facilityResponse.facility,
              })
            );
            return;
          } catch (error) {
            if (!isActiveRequest(requestId)) {
              return;
            }

            setState(
              createAuthState({
                user: firebaseUser,
                authStatus: 'session_error',
                facilities,
                accessState: buildFacilitySelectionError(error),
              })
            );
            return;
          }
        }

        if (facilities.length > 1) {
          setState(
            createAuthState({
              user: firebaseUser,
              authStatus: 'choosing_facility',
              facilities,
            })
          );
          return;
        }

        setState(
          createAuthState({
            user: firebaseUser,
            authStatus: 'access_limited',
            accessState: buildNoFacilityAccessState(),
          })
        );
      } catch (error) {
        if (!isActiveRequest(requestId)) {
          return;
        }

        const nextState = buildAccessState(error);
        setState(
          createAuthState({
            user: firebaseUser,
            authStatus: nextState.authStatus,
            accessState: nextState.accessState,
          })
        );
      }
    },
    [isActiveRequest]
  );

  useEffect(() => {
    const unsubscribe = onAuthStateChanged(auth, (firebaseUser) => {
      if (firebaseUser) {
        void bootstrapSession(firebaseUser);
        return;
      }

      resetToUnauthenticated();
    });

    return unsubscribe;
  }, [bootstrapSession, resetToUnauthenticated]);

  const signIn = useCallback(async (email: string, password: string) => {
    clearSession();
    setState((current) =>
      createAuthState({
        user: current.user,
        loading: true,
      })
    );

    try {
      await signInWithEmailAndPassword(auth, email, password);
    } catch (error) {
      setState(
        createAuthState({
          loginError: getFirebaseAuthErrorMessage(error),
        })
      );
    }
  }, []);

  const signInWithGoogle = useCallback(async () => {
    clearSession();
    setState((current) =>
      createAuthState({
        user: current.user,
        loading: true,
      })
    );

    const provider = new GoogleAuthProvider();
    provider.setCustomParameters({ prompt: 'select_account' });

    try {
      await signInWithPopup(auth, provider);
    } catch (error) {
      setState(
        createAuthState({
          loginError: getFirebaseAuthErrorMessage(error),
        })
      );
    }
  }, []);

  const signOut = useCallback(async () => {
    requestIdRef.current += 1;
    clearSession();
    setState((current) => ({
      ...current,
      loading: true,
      facilityLoading: false,
      loginError: null,
      accessState: null,
    }));

    await firebaseSignOut(auth);
  }, []);

  const chooseFacility = useCallback(
    async (facility: Facility) => {
      const firebaseUser = auth.currentUser;
      if (!firebaseUser) {
        resetToUnauthenticated();
        return;
      }

      const requestId = ++requestIdRef.current;
      setState((current) => ({
        ...current,
        facilityLoading: true,
        loginError: null,
        accessState: null,
      }));

      try {
        const response = await selectFacility(facility.id);
        if (!isActiveRequest(requestId)) {
          return;
        }

        saveFacilitySession(response);
        setState((current) =>
          createAuthState({
            user: firebaseUser,
            authStatus: 'ready',
            facilities: current.facilities,
            selectedFacility: response.facility,
          })
        );
      } catch (error) {
        if (!isActiveRequest(requestId)) {
          return;
        }

        setState((current) =>
          createAuthState({
            user: firebaseUser,
            authStatus: 'session_error',
            facilities: current.facilities,
            accessState: buildFacilitySelectionError(error),
          })
        );
      }
    },
    [isActiveRequest, resetToUnauthenticated]
  );

  const retrySessionBootstrap = useCallback(async () => {
    const firebaseUser = auth.currentUser;
    if (!firebaseUser) {
      resetToUnauthenticated();
      return;
    }

    await bootstrapSession(firebaseUser);
  }, [bootstrapSession, resetToUnauthenticated]);

  return (
    <AuthContext.Provider
      value={{
        ...state,
        signIn,
        signInWithGoogle,
        signOut,
        chooseFacility,
        retrySessionBootstrap,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}
