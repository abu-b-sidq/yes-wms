export type TransactionType = 'GRN' | 'MOVE' | 'PUTAWAY' | 'ORDER_PICK' | 'RETURN' | 'CYCLE_COUNT' | 'ADJUSTMENT';
export type TransactionStatus = 'PENDING' | 'IN_PROGRESS' | 'COMPLETED' | 'FAILED' | 'CANCELLED';
export type TaskStatus = 'PENDING' | 'ASSIGNED' | 'IN_PROGRESS' | 'COMPLETED' | 'CANCELLED';
export type EntityType = 'LOCATION' | 'ZONE' | 'INVOICE' | 'VIRTUAL_BUCKET' | 'SUPPLIER' | 'CUSTOMER';

export interface Pick {
  id: string;
  sku_code: string;
  sku_name?: string;
  quantity: number;
  source_type: EntityType;
  source_code: string;
  source_name?: string;
  status: TaskStatus;
  assigned_to?: string;
  batch?: string;
}

export interface Drop {
  id: string;
  sku_code: string;
  sku_name?: string;
  quantity: number;
  destination_type: EntityType;
  destination_code: string;
  destination_name?: string;
  status: TaskStatus;
  assigned_to?: string;
  batch?: string;
  pick?: string;
}

export interface Transaction {
  id: string;
  type: TransactionType;
  status: TransactionStatus;
  reference?: string;
  notes?: string;
  facility: string;
  facility_name?: string;
  org: string;
  picks: Pick[];
  drops: Drop[];
  created_at: string;
  updated_at: string;
  executed_at?: string;
  document_url?: string;
}

export interface TransactionListItem {
  id: string;
  type: TransactionType;
  status: TransactionStatus;
  reference?: string;
  facility: string;
  created_at: string;
  updated_at: string;
  pick_count?: number;
  drop_count?: number;
}

export interface GrnPayload {
  reference?: string;
  notes?: string;
  items: Array<{
    sku_code: string;
    quantity: number;
    destination_zone?: string;
    batch?: string;
  }>;
}

export interface MovePayload {
  reference?: string;
  notes?: string;
  items: Array<{
    sku_code: string;
    quantity: number;
    source_location: string;
    destination_location: string;
    batch?: string;
  }>;
}

export interface PutawayPayload {
  reference?: string;
  notes?: string;
  items: Array<{
    sku_code: string;
    quantity: number;
    source_zone?: string;
    destination_location: string;
    batch?: string;
  }>;
}

export interface OrderPickPayload {
  reference: string;
  notes?: string;
  items: Array<{
    sku_code: string;
    quantity: number;
    source_location: string;
    invoice_code: string;
    batch?: string;
  }>;
}

export interface InventoryBalance {
  id: string;
  facility_code: string;
  sku_code: string;
  entity_type: EntityType;
  entity_code: string;
  batch_number: string;
  quantity_on_hand: string;
  quantity_reserved: string;
  quantity_available: string;
  updated_at: string;
}
