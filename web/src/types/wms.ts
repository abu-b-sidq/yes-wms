export interface Facility {
  id: string;
  code: string;
  warehouse_key: string;
  name: string;
  is_active: boolean;
}

export interface SessionLoginResponse {
  user: {
    id: string;
    email: string;
    display_name: string;
    status: string;
  };
  available_facilities: Facility[];
  last_used_facility: Facility | null;
}

export interface WMSSession {
  warehouseKey: string;
  orgId: string;
  facilityId: string;
  facilityName: string;
}
