export interface Facility {
  id: string;
  code: string;
  warehouse_key: string;
  org_id: string;
  name: string;
}

export interface SessionLoginResponse {
  user_id: string;
  email: string;
  display_name: string;
  photo_url: string;
  available_facilities: Facility[];
  last_used_facility: Facility | null;
}

export interface SelectFacilityResponse {
  facility: Facility;
  warehouse_key: string;
  org_id: string;
}

export interface WMSSession {
  warehouseKey: string;
  orgId: string;
  facilityId: string;
  facilityName: string;
}
