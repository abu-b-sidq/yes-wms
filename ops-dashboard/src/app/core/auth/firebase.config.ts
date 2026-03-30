import { initializeApp, getApps, FirebaseApp } from 'firebase/app';
import { getAuth, Auth } from 'firebase/auth';

let app: FirebaseApp;
let auth: Auth;

export function initFirebase(config: { apiKey: string; authDomain: string; projectId: string }): void {
  if (!getApps().length) {
    app = initializeApp(config);
  } else {
    app = getApps()[0];
  }
  auth = getAuth(app);
}

export function getFirebaseAuth(): Auth {
  return auth;
}
