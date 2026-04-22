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
  transaction_type?: TransactionType;
  status: TransactionStatus;
  reference?: string;
  reference_number?: string;
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

export interface TransactionCreatePickPayload {
  sku_code: string;
  source_entity_type: EntityType;
  source_entity_code: string;
  quantity: number;
  batch_number?: string;
}

export interface TransactionCreateDropPayload {
  sku_code: string;
  dest_entity_type: EntityType;
  dest_entity_code: string;
  quantity: number;
  batch_number?: string;
}

export interface TransactionCreatePayload {
  transaction_type: TransactionType;
  reference_number?: string;
  notes?: string;
  picks?: TransactionCreatePickPayload[];
  drops?: TransactionCreateDropPayload[];
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

export interface VirtualWarehouseArea {
  key: string;
  label: string;
  kind: string;
  x: number;
  y: number;
  w: number;
  h: number;
}

export interface VirtualWarehouseScene {
  width: number;
  height: number;
  areas: VirtualWarehouseArea[];
}

export interface VirtualWarehouseFacility {
  code: string;
  name: string;
  warehouse_key: string;
}

export interface VirtualWarehouseZone {
  code: string;
  name: string;
  kind: string;
  label: string;
  x: number;
  y: number;
  w: number;
  h: number;
}

export interface VirtualWarehouseStockItem {
  sku_code: string;
  sku_name: string;
  batch_number: string;
  quantity_on_hand: string;
  quantity_available: string;
  quantity_reserved: string;
}

export interface VirtualWarehouseTaskSummary {
  id: string;
  task_type: string;
  task_status: TaskStatus | string;
  transaction_id: string;
  transaction_type: TransactionType | string;
  reference_number: string;
  sku_code: string;
  sku_name: string;
  quantity: string;
  counterpart_entity_code?: string | null;
  assigned_to_name?: string | null;
  picked_by_name?: string | null;
  task_started_at?: string | null;
  task_completed_at?: string | null;
}

export interface VirtualWarehouseLocation {
  code: string;
  name: string;
  zone_code: string;
  kind: string;
  x: number;
  y: number;
  w: number;
  h: number;
  rotation: number;
  quantity_on_hand: string;
  quantity_available: string;
  quantity_reserved: string;
  stock_items: VirtualWarehouseStockItem[];
  active_tasks: VirtualWarehouseTaskSummary[];
  worker_ids: string[];
}

export interface VirtualWarehouseWorker {
  id: string;
  user_id: string;
  display_name: string;
  state: 'picking' | 'carrying' | 'dropping' | string;
  x: number;
  y: number;
  task_id: string;
  task_type: string;
  task_status: TaskStatus | string;
  sku_code: string;
  sku_name: string;
  quantity: string;
  source_entity_type?: EntityType | string | null;
  source_entity_code?: string | null;
  dest_entity_type?: EntityType | string | null;
  dest_entity_code?: string | null;
  assigned_at?: string | null;
  task_started_at?: string | null;
  task_completed_at?: string | null;
}

export interface VirtualWarehouseTaskLink {
  id: string;
  state: 'carrying' | 'dropping' | string;
  worker_id: string;
  worker_name: string;
  sku_code: string;
  quantity: string;
  source_entity_type: EntityType | string;
  source_entity_code: string;
  dest_entity_type: EntityType | string;
  dest_entity_code: string;
  source_x: number;
  source_y: number;
  dest_x: number;
  dest_y: number;
}

export interface VirtualWarehouseSummary {
  location_quantity: string;
  user_quantity: string;
  workers_active: number;
  workers_carrying: number;
  locations_with_stock: number;
  unplaced_location_count: number;
}

export interface VirtualWarehouseUnplacedLocation {
  code: string;
  name: string;
  zone_code: string;
}

export interface VirtualWarehouseResponse {
  facility: VirtualWarehouseFacility;
  scene: VirtualWarehouseScene;
  zones: VirtualWarehouseZone[];
  locations: VirtualWarehouseLocation[];
  workers: VirtualWarehouseWorker[];
  task_links: VirtualWarehouseTaskLink[];
  summary: VirtualWarehouseSummary;
  unplaced_locations: VirtualWarehouseUnplacedLocation[];
}
