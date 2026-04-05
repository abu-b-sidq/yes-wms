import { Injectable, signal } from '@angular/core';

export type ThemePreference = 'dark' | 'light' | 'system';

@Injectable({ providedIn: 'root' })
export class ThemeService {
  private readonly STORAGE_KEY = 'ops-theme';
  private readonly systemQuery = window.matchMedia('(prefers-color-scheme: light)');
  private readonly themeColorMeta = document.querySelector('meta[name="theme-color"]');

  preference = signal<ThemePreference>('system');
  resolved = signal<'light' | 'dark'>('dark');

  constructor() {
    const saved = localStorage.getItem(this.STORAGE_KEY) as ThemePreference | null;
    if (saved === 'dark' || saved === 'light' || saved === 'system') {
      this.preference.set(saved);
    }
    this.apply();
    this.systemQuery.addEventListener('change', () => this.apply());
  }

  init(): void {
    this.apply();
  }

  set(pref: ThemePreference): void {
    this.preference.set(pref);
    localStorage.setItem(this.STORAGE_KEY, pref);
    this.apply();
  }

  toggle(): void {
    this.set(this.resolved() === 'light' ? 'dark' : 'light');
  }

  private apply(): void {
    const isLight =
      this.preference() === 'light' ||
      (this.preference() === 'system' && this.systemQuery.matches);
    const root = document.documentElement;

    root.classList.toggle('light-theme', isLight);
    root.dataset['theme'] = isLight ? 'light' : 'dark';
    root.style.colorScheme = isLight ? 'light' : 'dark';
    this.resolved.set(isLight ? 'light' : 'dark');
    this.themeColorMeta?.setAttribute('content', isLight ? '#eef2e7' : '#0b1512');
  }
}
