# StockOne Neo API endpoint paths and defaults.

# Authentication
AUTH_TOKEN_PATH = "/o/token/"

# Core / Master data
PRODUCTS_PATH = "/api/v1/core/products/"
TAX_PATH = "/api/v1/core/tax/"

# Inbound
PURCHASE_ORDER_PATH = "/api/v1/inbound/purchase_order/"
SUPPLIER_PATH = "/api/v1/inbound/supplier/"
SUPPLIER_CREATE_PATH = "/api/v1/inbound/update_supplier/"
ASN_PATH = "/api/v1/inbound/asn/"
GRN_PATH = "/api/v1/inbound/grn/"

# Outbound
ORDERS_V1_PATH = "/api/v1/outbound/orders/"
ORDERS_V2_PATH = "/api/v2/outbound/orders/"
CUSTOMER_PATH = "/api/v1/outbound/customer/"
SALES_RETURN_PATH = "/api/v1/outbound/sales_return/"
INVOICE_PATH = "/api/v1/outbound/invoice/"
PICKLIST_PATH = "/api/v1/outbound/picklist_view/"

# Inventory
INVENTORY_PATH = "/api/v1/inventory/inventory/"
MOVE_INVENTORY_PATH = "/api/v1/inventory/move_inventory/"
STOCK_STATUS_UPDATE_PATH = "/api/v1/inventory/update_stock_status/"
SKU_PACK_PATH = "/api/v1/inventory/pack/"

# Production
JOB_ORDER_PATH = "/api/v1/production/jo/"

# Default pagination
DEFAULT_PAGE_SIZE = 10
