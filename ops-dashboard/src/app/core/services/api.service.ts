import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { map } from 'rxjs/operators';
import { environment } from '../../../environments/environment';

interface ApiEnvelope<T> { success: boolean; data: T; error: string | null; }

@Injectable({ providedIn: 'root' })
export class ApiService {
  protected http = inject(HttpClient);
  protected baseUrl = environment.apiUrl;

  private unwrap<T>(source: Observable<ApiEnvelope<T>>): Observable<T> {
    return source.pipe(map(res => res.data));
  }

  get<T>(path: string, params?: Record<string, string | number | boolean>): Observable<T> {
    let httpParams = new HttpParams();
    if (params) {
      Object.entries(params).forEach(([key, val]) => {
        if (val !== undefined && val !== null) {
          httpParams = httpParams.set(key, String(val));
        }
      });
    }
    return this.unwrap(this.http.get<ApiEnvelope<T>>(`${this.baseUrl}${path}`, { params: httpParams }));
  }

  post<T>(path: string, body: unknown): Observable<T> {
    return this.unwrap(this.http.post<ApiEnvelope<T>>(`${this.baseUrl}${path}`, body));
  }

  patch<T>(path: string, body: unknown): Observable<T> {
    return this.unwrap(this.http.patch<ApiEnvelope<T>>(`${this.baseUrl}${path}`, body));
  }

  put<T>(path: string, body: unknown): Observable<T> {
    return this.unwrap(this.http.put<ApiEnvelope<T>>(`${this.baseUrl}${path}`, body));
  }

  delete<T>(path: string): Observable<T> {
    return this.unwrap(this.http.delete<ApiEnvelope<T>>(`${this.baseUrl}${path}`));
  }
}
