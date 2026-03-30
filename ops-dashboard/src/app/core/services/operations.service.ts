import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';
import { ApiService } from './api.service';
import {
  Transaction, TransactionListItem,
  GrnPayload, MovePayload, PutawayPayload, OrderPickPayload,
  InventoryBalance, TransactionType, TransactionStatus
} from '../models/operations.model';

interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  size: number;
}

@Injectable({ providedIn: 'root' })
export class OperationsService extends ApiService {

  // --- Transactions ---
  getTransactions(params?: {
    type?: TransactionType;
    status?: TransactionStatus;
    page?: number;
    size?: number;
    search?: string;
  }): Observable<PaginatedResponse<TransactionListItem> | TransactionListItem[]> {
    return this.get<PaginatedResponse<TransactionListItem> | TransactionListItem[]>(
      '/operations/transactions',
      params as Record<string, string | number | boolean>
    );
  }

  getTransaction(id: string): Observable<Transaction> {
    return this.get<Transaction>(`/operations/transactions/${id}`);
  }

  executeTransaction(id: string): Observable<Transaction> {
    return this.post<Transaction>(`/operations/transactions/${id}/execute`, {});
  }

  cancelTransaction(id: string): Observable<Transaction> {
    return this.post<Transaction>(`/operations/transactions/${id}/cancel`, {});
  }

  // --- Convenience endpoints (create + execute) ---
  createGrn(payload: GrnPayload): Observable<Transaction> {
    return this.post<Transaction>('/operations/grn', payload);
  }

  createMove(payload: MovePayload): Observable<Transaction> {
    return this.post<Transaction>('/operations/move', payload);
  }

  createPutaway(payload: PutawayPayload): Observable<Transaction> {
    return this.post<Transaction>('/operations/putaway', payload);
  }

  createOrderPick(payload: OrderPickPayload): Observable<Transaction> {
    return this.post<Transaction>('/operations/order-pick', payload);
  }

  // --- Inventory ---
  getBalances(params?: {
    sku_code?: string;
    entity_type?: string;
    entity_code?: string;
    page?: number;
    size?: number;
  }): Observable<PaginatedResponse<InventoryBalance> | InventoryBalance[]> {
    return this.get<PaginatedResponse<InventoryBalance> | InventoryBalance[]>(
      '/inventory/balances',
      params as Record<string, string | number | boolean>
    );
  }

  getBalancesByLocation(locationCode: string): Observable<InventoryBalance[]> {
    return this.get<InventoryBalance[]>(`/inventory/balances/by-location/${locationCode}`);
  }

  getBalancesBySku(skuCode: string): Observable<InventoryBalance[]> {
    return this.get<InventoryBalance[]>(`/inventory/balances/by-sku/${skuCode}`);
  }
}
