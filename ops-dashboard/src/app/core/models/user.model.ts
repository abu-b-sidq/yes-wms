export interface AppUser {
  id: string;
  email: string;
  display_name: string;
  status: 'PENDING' | 'ACTIVE' | 'SUSPENDED';
}

export interface Facility {
  id: string;
  code: string;
  warehouse_key: string;
  name: string;
  is_active: boolean;
  address?: string;
}

export interface Organization {
  id: string;
  code: string;
  name: string;
  is_active: boolean;
}

export interface SessionLoginResponse {
  user: AppUser;
  available_facilities: Facility[];
  last_used_facility: Facility | null;
}

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
