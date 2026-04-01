export interface AppUser {
  id: string;
  email: string;
  display_name: string;
  photo_url?: string;
  status: 'PENDING' | 'ACTIVE' | 'SUSPENDED';
}

export interface Facility {
  id: string;
  code: string;
  warehouse_key: string;
  org_id: string;
  name: string;
  is_active?: boolean;
  address?: string;
}

export interface Organization {
  id: string;
  code: string;
  name: string;
  is_active: boolean;
}

/** Shape of the `data` field returned by POST /mobile/session/login */
export interface SessionLoginData {
  user_id: string;
  email: string;
  display_name: string;
  photo_url?: string;
  available_facilities: Facility[];
  last_used_facility: Facility | null;
}

/** Standard API envelope */
export interface ApiEnvelope<T> {
  success: boolean;
  data: T;
  error: string | null;
  meta: Record<string, unknown>;
}

export type SessionLoginResponse = ApiEnvelope<SessionLoginData>;

export interface WmsSession {
  user: AppUser;
  facility: Facility;
  orgId: string;
  warehouseKey: string;
  permissions: string[];
}

export interface UserPermissions {
  permissions: string[];
  roles: string[];
}
