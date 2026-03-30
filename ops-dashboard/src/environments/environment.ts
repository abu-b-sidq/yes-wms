// Development environment — values are injected at runtime via window.__env or angular proxy
// For production builds, see environment.prod.ts

declare global {
  interface Window {
    __env?: {
      FIREBASE_API_KEY?: string;
      FIREBASE_AUTH_DOMAIN?: string;
      FIREBASE_PROJECT_ID?: string;
      API_URL?: string;
    };
  }
}

export const environment = {
  production: false,
  get apiUrl() {
    return window.__env?.API_URL || 'http://localhost:8010/api/v1';
  },
  get firebase() {
    return {
      apiKey: window.__env?.FIREBASE_API_KEY || '',
      authDomain: window.__env?.FIREBASE_AUTH_DOMAIN || '',
      projectId: window.__env?.FIREBASE_PROJECT_ID || '',
    };
  }
};
