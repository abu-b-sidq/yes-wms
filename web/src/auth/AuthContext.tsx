import React, { createContext, useContext, useEffect, useState, useCallback } from 'react';
import {
  onAuthStateChanged,
  signInWithEmailAndPassword,
  signOut as firebaseSignOut,
  type User,
} from 'firebase/auth';
import { auth } from '../api/firebase';
import { sessionLogin, selectFacility } from '../api/auth';
import { saveSession, clearSession } from '../api/client';
import type { Facility } from '../types/wms';

interface AuthState {
  user: User | null;
  loading: boolean;
  facilities: Facility[];
  selectedFacility: Facility | null;
  loginError: string | null;
  facilityLoading: boolean;
}

interface AuthContextValue extends AuthState {
  signIn: (email: string, password: string) => Promise<void>;
  signOut: () => Promise<void>;
  chooseFacility: (facility: Facility) => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
}

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [state, setState] = useState<AuthState>({
    user: null,
    loading: true,
    facilities: [],
    selectedFacility: null,
    loginError: null,
    facilityLoading: false,
  });

  // Listen to Firebase auth state
  useEffect(() => {
    const unsubscribe = onAuthStateChanged(auth, async (firebaseUser) => {
      if (firebaseUser) {
        try {
          const resp = await sessionLogin();
          const facilities = resp.available_facilities || [];
          let selected: Facility | null = null;

          // Auto-select if only one facility or restore last used
          if (facilities.length === 1) {
            selected = facilities[0];
          } else if (resp.last_used_facility) {
            selected = facilities.find(f => f.code === resp.last_used_facility?.code) || null;
          }

          if (selected) {
            const result = await selectFacility(selected.code);
            saveSession({
              warehouseKey: result.warehouse_key,
              orgId: result.org_id,
              facilityId: selected.code,
              facilityName: selected.name,
            });
          }

          setState({
            user: firebaseUser,
            loading: false,
            facilities,
            selectedFacility: selected,
            loginError: null,
            facilityLoading: false,
          });
        } catch (err) {
          setState({
            user: firebaseUser,
            loading: false,
            facilities: [],
            selectedFacility: null,
            loginError: err instanceof Error ? err.message : 'Session login failed',
            facilityLoading: false,
          });
        }
      } else {
        clearSession();
        setState({
          user: null,
          loading: false,
          facilities: [],
          selectedFacility: null,
          loginError: null,
          facilityLoading: false,
        });
      }
    });
    return unsubscribe;
  }, []);

  const signIn = useCallback(async (email: string, password: string) => {
    setState(s => ({ ...s, loginError: null, loading: true }));
    try {
      await signInWithEmailAndPassword(auth, email, password);
    } catch (err) {
      setState(s => ({
        ...s,
        loading: false,
        loginError: err instanceof Error ? err.message : 'Login failed',
      }));
    }
  }, []);

  const signOut = useCallback(async () => {
    clearSession();
    await firebaseSignOut(auth);
  }, []);

  const chooseFacility = useCallback(async (facility: Facility) => {
    setState(s => ({ ...s, facilityLoading: true }));
    try {
      const result = await selectFacility(facility.code);
      saveSession({
        warehouseKey: result.warehouse_key,
        orgId: result.org_id,
        facilityId: facility.code,
        facilityName: facility.name,
      });
      setState(s => ({
        ...s,
        selectedFacility: facility,
        facilityLoading: false,
      }));
    } catch (err) {
      setState(s => ({
        ...s,
        facilityLoading: false,
        loginError: err instanceof Error ? err.message : 'Facility selection failed',
      }));
    }
  }, []);

  return (
    <AuthContext.Provider value={{ ...state, signIn, signOut, chooseFacility }}>
      {children}
    </AuthContext.Provider>
  );
}
