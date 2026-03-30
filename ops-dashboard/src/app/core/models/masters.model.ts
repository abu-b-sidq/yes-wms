export interface Sku {
  id: string;
  code: string;
  name: string;
  description?: string;
  uom: string;
  is_active: boolean;
  org: string;
  created_at: string;
  updated_at: string;
  metadata?: Record<string, unknown>;
}

export interface Zone {
  id: string;
  code: string;
  name: string;
  zone_type?: string;
  is_active: boolean;
  org: string;
  created_at: string;
  updated_at: string;
}

export interface Location {
  id: string;
  code: string;
  name: string;
  zone: string;
  zone_code?: string;
  zone_name?: string;
  capacity?: number;
  is_active: boolean;
  org: string;
  created_at: string;
  updated_at: string;
}

export interface FacilitySku {
  id: string;
  sku: string;
  sku_code?: string;
  sku_name?: string;
  facility: string;
  is_active: boolean;
}

export interface FacilityZone {
  id: string;
  zone: string;
  zone_code?: string;
  zone_name?: string;
  facility: string;
  is_active: boolean;
}

export interface FacilityLocation {
  id: string;
  location: string;
  location_code?: string;
  location_name?: string;
  facility: string;
  is_active: boolean;
}

export interface SkuCreatePayload {
  code: string;
  name: string;
  description?: string;
  uom: string;
  metadata?: Record<string, unknown>;
}

export interface ZoneCreatePayload {
  code: string;
  name: string;
  zone_type?: string;
}

export interface LocationCreatePayload {
  code: string;
  name: string;
  zone: string;
  capacity?: number;
}
