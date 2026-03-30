export const environment = {
  production: true,
  apiUrl: '/api/v1',
  firebase: {
    apiKey: (window as Window & { __env?: { FIREBASE_API_KEY?: string } }).__env?.FIREBASE_API_KEY || '',
    authDomain: (window as Window & { __env?: { FIREBASE_AUTH_DOMAIN?: string } }).__env?.FIREBASE_AUTH_DOMAIN || '',
    projectId: (window as Window & { __env?: { FIREBASE_PROJECT_ID?: string } }).__env?.FIREBASE_PROJECT_ID || '',
  }
};
