import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';
import { ApiService } from './api.service';
import {
  Transaction, TransactionListItem,
  GrnPayload, MovePayload, PutawayPayload, OrderPickPayload,
  TransactionCreatePayload,
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

  createTransaction(payload: TransactionCreatePayload): Observable<Transaction> {
    return this.post<Transaction>('/operations/transactions', {
      transaction_type: payload.transaction_type,
      reference_number: payload.reference_number ?? '',
      notes: payload.notes ?? '',
      picks: payload.picks ?? [],
      drops: payload.drops ?? []
    });
  }

  executeTransaction(id: string): Observable<Transaction> {
    return this.post<Transaction>(`/operations/transactions/${id}/execute`, {});
  }

  cancelTransaction(id: string): Observable<Transaction> {
    return this.post<Transaction>(`/operations/transactions/${id}/cancel`, {});
  }

  // --- Dashboard shortcuts via the shared create endpoint ---
  createGrn(payload: GrnPayload): Observable<Transaction> {
    return this.createTransaction({
      transaction_type: 'GRN',
      reference_number: payload.reference,
      notes: payload.notes,
      drops: payload.items.map((item) => ({
        sku_code: item.sku_code,
        dest_entity_type: 'ZONE',
        dest_entity_code: item.destination_zone || 'PRE_PUTAWAY',
        quantity: item.quantity,
        batch_number: item.batch
      }))
    });
  }

  createMove(payload: MovePayload): Observable<Transaction> {
    return this.createTransaction({
      transaction_type: 'MOVE',
      reference_number: payload.reference,
      notes: payload.notes,
      picks: payload.items.map((item) => ({
        sku_code: item.sku_code,
        source_entity_type: 'LOCATION',
        source_entity_code: item.source_location,
        quantity: item.quantity,
        batch_number: item.batch
      })),
      drops: payload.items.map((item) => ({
        sku_code: item.sku_code,
        dest_entity_type: 'LOCATION',
        dest_entity_code: item.destination_location,
        quantity: item.quantity,
        batch_number: item.batch
      }))
    });
  }

  createPutaway(payload: PutawayPayload): Observable<Transaction> {
    return this.createTransaction({
      transaction_type: 'PUTAWAY',
      reference_number: payload.reference,
      notes: payload.notes,
      picks: payload.items.map((item) => ({
        sku_code: item.sku_code,
        source_entity_type: 'ZONE',
        source_entity_code: item.source_zone || 'PRE_PUTAWAY',
        quantity: item.quantity,
        batch_number: item.batch
      })),
      drops: payload.items.map((item) => ({
        sku_code: item.sku_code,
        dest_entity_type: 'LOCATION',
        dest_entity_code: item.destination_location,
        quantity: item.quantity,
        batch_number: item.batch
      }))
    });
  }

  createOrderPick(payload: OrderPickPayload): Observable<Transaction> {
    return this.createTransaction({
      transaction_type: 'ORDER_PICK',
      reference_number: payload.reference,
      notes: payload.notes,
      picks: payload.items.map((item) => ({
        sku_code: item.sku_code,
        source_entity_type: 'LOCATION',
        source_entity_code: item.source_location,
        quantity: item.quantity,
        batch_number: item.batch
      })),
      drops: payload.items.map((item) => ({
        sku_code: item.sku_code,
        dest_entity_type: 'INVOICE',
        dest_entity_code: item.invoice_code,
        quantity: item.quantity,
        batch_number: item.batch
      }))
    });
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
