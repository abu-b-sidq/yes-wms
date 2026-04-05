export type ConnectorType = 'STOCKONE' | 'SAP' | 'ORACLE';
export type SyncEntityType = 'SKU' | 'INVENTORY' | 'ORDER' | 'PURCHASE_ORDER' | 'SUPPLIER' | 'CUSTOMER';
export type SyncStatus = 'PENDING' | 'RUNNING' | 'COMPLETED' | 'FAILED';

export interface ConnectorConfig {
  id: string;
  name: string;
  connector_type: ConnectorType;
  is_active: boolean;
  facility_id: string | null;
  config: Record<string, string | number | boolean>;
  sync_interval_minutes: number;
  enabled_entities: SyncEntityType[];
  last_synced_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface ConnectorCreatePayload {
  name: string;
  connector_type: ConnectorType;
  config: Record<string, string | number | boolean>;
  facility_id?: string | null;
  sync_interval_minutes?: number;
  enabled_entities?: SyncEntityType[];
}

export interface ConnectorUpdatePayload {
  name?: string;
  is_active?: boolean;
  config?: Record<string, string | number | boolean>;
  facility_id?: string | null;
  sync_interval_minutes?: number;
  enabled_entities?: SyncEntityType[];
}

export interface SyncLog {
  id: string;
  connector_id: string;
  entity_type: SyncEntityType;
  status: SyncStatus;
  started_at: string | null;
  completed_at: string | null;
  records_fetched: number;
  records_created: number;
  records_updated: number;
  records_skipped: number;
  records_failed: number;
  error_details: Array<{ external_id?: string; error: string; type?: string }> | null;
  created_at: string;
}

export interface TestConnectionResult {
  status: string;
  token_type: string | null;
  expires_in: number | null;
  scope: string | null;
}

// Default config templates per connector type
export const CONNECTOR_CONFIG_TEMPLATES: Record<ConnectorType, Record<string, string>> = {
  STOCKONE: {
    base_url: 'https://alpha-backend.stockone.com',
    client_id: '',
    client_secret: '',
    warehouse_key: ''
  },
  SAP: {
    base_url: '',
    username: '',
    password: '',
    client: ''
  },
  ORACLE: {
    base_url: '',
    username: '',
    password: '',
    warehouse_key: ''
  }
};

export const ENTITY_TYPE_LABELS: Record<SyncEntityType, string> = {
  SKU: 'Products / SKUs',
  INVENTORY: 'Inventory Balances',
  ORDER: 'Orders',
  PURCHASE_ORDER: 'Purchase Orders',
  SUPPLIER: 'Suppliers',
  CUSTOMER: 'Customers'
};

export const SYNC_STATUS_CONFIG: Record<SyncStatus, { color: string; bg: string }> = {
  PENDING:   { color: 'var(--ops-warning-strong)', bg: 'var(--ops-warning-soft)' },
  RUNNING:   { color: 'var(--ops-accent-blue)', bg: 'var(--ops-accent-blue-soft)' },
  COMPLETED: { color: 'var(--ops-success-strong)', bg: 'var(--ops-success-soft)' },
  FAILED:    { color: 'var(--ops-danger-strong)', bg: 'var(--ops-danger-soft)' }
};
