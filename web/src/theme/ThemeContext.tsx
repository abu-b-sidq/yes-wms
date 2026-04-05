import React, { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react';

export type ThemePreference = 'dark' | 'light' | 'system';
export type ResolvedTheme = 'dark' | 'light';

interface ThemeContextValue {
  preference: ThemePreference;
  resolved: ResolvedTheme;
  setPreference: (preference: ThemePreference) => void;
  toggleTheme: () => void;
}

const STORAGE_KEY = 'ops-theme';
const LIGHT_THEME_COLOR = '#eef2e7';
const DARK_THEME_COLOR = '#0b1512';

const ThemeContext = createContext<ThemeContextValue | null>(null);

function isThemePreference(value: string | null): value is ThemePreference {
  return value === 'dark' || value === 'light' || value === 'system';
}

function applyTheme(resolved: ResolvedTheme) {
  const root = document.documentElement;
  const themeColorMeta = document.querySelector('meta[name="theme-color"]');

  root.classList.toggle('light-theme', resolved === 'light');
  root.dataset.theme = resolved;
  root.style.colorScheme = resolved;
  themeColorMeta?.setAttribute('content', resolved === 'light' ? LIGHT_THEME_COLOR : DARK_THEME_COLOR);
}

function resolveInitialPreference(): ThemePreference {
  if (typeof window === 'undefined') {
    return 'system';
  }

  const saved = window.localStorage.getItem(STORAGE_KEY);
  return isThemePreference(saved) ? saved : 'system';
}

function resolveTheme(preference: ThemePreference, systemPrefersLight: boolean): ResolvedTheme {
  if (preference === 'system') {
    return systemPrefersLight ? 'light' : 'dark';
  }

  return preference;
}

export function ThemeProvider({ children }: { children: React.ReactNode }) {
  const [preference, setPreferenceState] = useState<ThemePreference>(resolveInitialPreference);
  const [resolved, setResolved] = useState<ResolvedTheme>('dark');

  useEffect(() => {
    const mediaQuery = window.matchMedia('(prefers-color-scheme: light)');

    const syncTheme = () => {
      const nextResolved = resolveTheme(preference, mediaQuery.matches);
      setResolved(nextResolved);
      applyTheme(nextResolved);
    };

    syncTheme();
    mediaQuery.addEventListener('change', syncTheme);

    return () => {
      mediaQuery.removeEventListener('change', syncTheme);
    };
  }, [preference]);

  const setPreference = useCallback((nextPreference: ThemePreference) => {
    setPreferenceState(nextPreference);
    window.localStorage.setItem(STORAGE_KEY, nextPreference);
  }, []);

  const toggleTheme = useCallback(() => {
    setPreference(resolved === 'light' ? 'dark' : 'light');
  }, [resolved, setPreference]);

  const value = useMemo<ThemeContextValue>(
    () => ({
      preference,
      resolved,
      setPreference,
      toggleTheme,
    }),
    [preference, resolved, setPreference, toggleTheme]
  );

  return <ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>;
}

export function useTheme() {
  const context = useContext(ThemeContext);

  if (!context) {
    throw new Error('useTheme must be used within a ThemeProvider');
  }

  return context;
}
