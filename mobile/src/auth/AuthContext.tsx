import React, { createContext, useContext, useEffect, useState } from 'react';
import auth, { FirebaseAuthTypes } from '@react-native-firebase/auth';
import { sessionLogin, selectFacility, Facility } from '../api/auth';
import { saveSessionHeaders, clearSession } from '../utils/storage';
import { getFcmToken } from '../utils/storage';

interface AuthState {
  user: FirebaseAuthTypes.User | null;
  loading: boolean;
  facilities: Facility[];
  selectedFacility: Facility | null;
  loginError: string | null;
}

interface AuthContextValue extends AuthState {
  signIn: (email: string, password: string) => Promise<void>;
  signOut: () => Promise<void>;
  chooseFacility: (facility: Facility) => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [state, setState] = useState<AuthState>({
    user: null,
    loading: true,
    facilities: [],
    selectedFacility: null,
    loginError: null,
  });

  useEffect(() => {
    const unsubscribe = auth().onAuthStateChanged(async (firebaseUser) => {
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
            });
          } else {
            // Need to pick a facility
            setState({
              user: firebaseUser,
              loading: false,
              facilities: available_facilities,
              selectedFacility: null,
              loginError: null,
            });
          }
        } catch (err: any) {
          setState({
            user: firebaseUser,
            loading: false,
            facilities: [],
            selectedFacility: null,
            loginError: err.message,
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
        });
      }
    });

    return unsubscribe;
  }, []);

  const signIn = async (email: string, password: string) => {
    setState((s) => ({ ...s, loading: true, loginError: null }));
    try {
      await auth().signInWithEmailAndPassword(email, password);
    } catch (err: any) {
      setState((s) => ({
        ...s,
        loading: false,
        loginError: err.message || 'Login failed',
      }));
    }
  };

  const signOut = async () => {
    await auth().signOut();
    await clearSession();
    setState({
      user: null,
      loading: false,
      facilities: [],
      selectedFacility: null,
      loginError: null,
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
    } catch (err: any) {
      setState((s) => ({
        ...s,
        loading: false,
        loginError: err.message,
      }));
    }
  };

  return (
    <AuthContext.Provider
      value={{ ...state, signIn, signOut, chooseFacility }}
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
