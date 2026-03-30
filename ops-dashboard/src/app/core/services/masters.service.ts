import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';
import { ApiService } from './api.service';
import {
  Sku, Zone, Location,
  SkuCreatePayload, ZoneCreatePayload, LocationCreatePayload
} from '../models/masters.model';

interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  size: number;
}

@Injectable({ providedIn: 'root' })
export class MastersService extends ApiService {

  // --- SKU ---
  getSkus(params?: Record<string, string | number | boolean>): Observable<PaginatedResponse<Sku> | Sku[]> {
    return this.get<PaginatedResponse<Sku> | Sku[]>('/masters/skus', params);
  }

  getSku(code: string): Observable<Sku> {
    return this.get<Sku>(`/masters/skus/${code}`);
  }

  createSku(payload: SkuCreatePayload): Observable<Sku> {
    return this.post<Sku>('/masters/skus', payload);
  }

  updateSku(code: string, payload: Partial<SkuCreatePayload>): Observable<Sku> {
    return this.patch<Sku>(`/masters/skus/${code}`, payload);
  }

  // --- Zone ---
  getZones(params?: Record<string, string | number | boolean>): Observable<PaginatedResponse<Zone> | Zone[]> {
    return this.get<PaginatedResponse<Zone> | Zone[]>('/masters/zones', params);
  }

  getZone(code: string): Observable<Zone> {
    return this.get<Zone>(`/masters/zones/${code}`);
  }

  createZone(payload: ZoneCreatePayload): Observable<Zone> {
    return this.post<Zone>('/masters/zones', payload);
  }

  updateZone(code: string, payload: Partial<ZoneCreatePayload>): Observable<Zone> {
    return this.patch<Zone>(`/masters/zones/${code}`, payload);
  }

  // --- Location ---
  getLocations(params?: Record<string, string | number | boolean>): Observable<PaginatedResponse<Location> | Location[]> {
    return this.get<PaginatedResponse<Location> | Location[]>('/masters/locations', params);
  }

  getLocation(code: string): Observable<Location> {
    return this.get<Location>(`/masters/locations/${code}`);
  }

  createLocation(payload: LocationCreatePayload): Observable<Location> {
    return this.post<Location>('/masters/locations', payload);
  }

  updateLocation(code: string, payload: Partial<LocationCreatePayload>): Observable<Location> {
    return this.patch<Location>(`/masters/locations/${code}`, payload);
  }

  // --- Facilities ---
  getFacilities(): Observable<unknown[]> {
    return this.get<unknown[]>('/masters/facilities');
  }
}
