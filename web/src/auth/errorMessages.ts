type ErrorWithCode = {
  code?: unknown;
  message?: unknown;
};

export function getErrorCode(error: unknown): string | null {
  if (!error || typeof error !== 'object' || !('code' in error)) {
    return null;
  }

  const code = (error as ErrorWithCode).code;
  return typeof code === 'string' && code.trim() ? code : null;
}

export function getErrorMessage(error: unknown, fallback: string): string {
  if (error instanceof Error && error.message.trim()) {
    return error.message;
  }

  if (error && typeof error === 'object' && 'message' in error) {
    const message = (error as ErrorWithCode).message;
    if (typeof message === 'string' && message.trim()) {
      return message;
    }
  }

  return fallback;
}

export function getFirebaseAuthErrorMessage(error: unknown): string {
  const code = getErrorCode(error);

  const messages: Record<string, string> = {
    'auth/user-not-found': 'No account found with this email.',
    'auth/wrong-password': 'Incorrect password.',
    'auth/invalid-credential': 'Invalid email or password.',
    'auth/too-many-requests': 'Too many attempts. Please try again later.',
    'auth/network-request-failed': 'Network error. Check your connection.',
    'auth/popup-closed-by-user': 'Google sign-in was cancelled before completion.',
    'auth/cancelled-popup-request': 'Another sign-in window is already open.',
    'auth/popup-blocked': 'Allow popups for this site to continue with Google sign-in.',
    'auth/unauthorized-domain': 'This site is not authorized for Google sign-in in Firebase Auth.',
    'auth/operation-not-allowed': 'Google sign-in is not enabled for this Firebase project.',
  };

  if (code && messages[code]) {
    return messages[code];
  }

  return getErrorMessage(error, 'Sign in failed. Please try again.');
}
