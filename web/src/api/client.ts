import axios from 'axios';
import { auth } from './firebase';
import type { WMSSession } from '../types/wms';

const apiClient = axios.create({
  baseURL: `${import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8010'}/api/v1`,
  timeout: 15000,
});

export function getSession(): WMSSession | null {
  const raw = sessionStorage.getItem('wms_session');
  if (!raw) return null;
  return JSON.parse(raw);
}

export function saveSession(session: WMSSession): void {
  sessionStorage.setItem('wms_session', JSON.stringify(session));
}

export function clearSession(): void {
  sessionStorage.removeItem('wms_session');
}

// Request interceptor: inject Firebase token + session headers
apiClient.interceptors.request.use(async (config) => {
  const user = auth.currentUser;
  if (user) {
    const token = await user.getIdToken();
    config.headers.Authorization = `Bearer ${token}`;
  }

  const session = getSession();
  if (session) {
    config.headers['warehouse'] = session.warehouseKey;
    config.headers['X-Org-Id'] = session.orgId;
    config.headers['X-Facility-Id'] = session.facilityId;
  }

  return config;
});

// Response interceptor: unwrap the standard envelope
apiClient.interceptors.response.use(
  (response) => {
    const body = response.data;
    if (body && typeof body === 'object' && 'success' in body) {
      if (body.success) {
        response.data = body.data;
      } else {
        const msg = body.error?.message || 'Request failed';
        return Promise.reject(new Error(msg));
      }
    }
    return response;
  },
  (error) => {
    const msg =
      error.response?.data?.error?.message ||
      error.message ||
      'Network error';
    return Promise.reject(new Error(msg));
  }
);

export default apiClient;
