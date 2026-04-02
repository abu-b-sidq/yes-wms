import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';
import { ApiService } from './api.service';
import {
  ConnectorConfig,
  ConnectorCreatePayload,
  ConnectorUpdatePayload,
  SyncLog,
  TestConnectionResult
} from '../models/connector.model';

@Injectable({ providedIn: 'root' })
export class ConnectorsService extends ApiService {

  list(): Observable<ConnectorConfig[]> {
    return this.get<ConnectorConfig[]>('/connectors/');
  }

  getById(id: string): Observable<ConnectorConfig> {
    return this.get<ConnectorConfig>(`/connectors/${id}`);
  }

  create(payload: ConnectorCreatePayload): Observable<ConnectorConfig> {
    return this.post<ConnectorConfig>('/connectors/', payload);
  }

  update(id: string, payload: ConnectorUpdatePayload): Observable<ConnectorConfig> {
    return this.put<ConnectorConfig>(`/connectors/${id}`, payload);
  }

  deactivate(id: string): Observable<ConnectorConfig> {
    return this.delete<ConnectorConfig>(`/connectors/${id}`);
  }

  testConnection(id: string): Observable<TestConnectionResult> {
    return this.post<TestConnectionResult>(`/connectors/${id}/test`, {});
  }

  triggerSync(id: string, entityTypes?: string[]): Observable<SyncLog[]> {
    return this.post<SyncLog[]>(`/connectors/${id}/sync`, { entity_types: entityTypes ?? null });
  }

  getLogs(id: string): Observable<SyncLog[]> {
    return this.get<SyncLog[]>(`/connectors/${id}/logs`);
  }

  getLog(connectorId: string, logId: string): Observable<SyncLog> {
    return this.get<SyncLog>(`/connectors/${connectorId}/logs/${logId}`);
  }
}
