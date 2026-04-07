# YES WMS Domain Knowledge

## Transaction Types

A **GRN** (Goods Received Note) is used to receive items into the warehouse. When a GRN is completed, stock lands in the PRE_PUTAWAY staging zone and waits to be moved to a storage location.

A **PUTAWAY** transaction moves items from the PRE_PUTAWAY staging zone to their designated storage locations. It is always done after a GRN.

A **MOVE** transaction transfers stock between any two locations within the warehouse — for example, relocating items between zones or consolidating inventory.

An **ORDER_PICK** transaction records the picking of items from storage locations to fulfil a customer order or invoice. Picked items are allocated against the invoice.

A **RETURN** transaction processes goods coming back from customers. Returned items are inspected and re-entered into stock or flagged for disposal.

A **CYCLE_COUNT** transaction is used for periodic inventory verification. Operators count physical stock in a location and the system reconciles the count against the recorded balance.

An **ADJUSTMENT** transaction applies a manual correction to inventory — for example, to account for damage, loss, or data entry errors. Adjustments require a reason code.

## Transaction Statuses

Transactions move through the following statuses:

- **PENDING** — created but not yet started
- **IN_PROGRESS** — currently being worked on
- **COMPLETED** — finished successfully
- **PARTIALLY_COMPLETED** — some items were processed but not all
- **FAILED** — encountered an error and did not complete
- **CANCELLED** — manually cancelled before completion

## Entity Types

- **LOCATION** — a physical bin or shelf where stock is stored
- **ZONE** — a logical grouping of locations (e.g. PRE_PUTAWAY, BULK, PICK_FACE)
- **INVOICE** — a customer order that drives ORDER_PICK transactions
- **VIRTUAL_BUCKET** — a non-physical holding area used for in-transit or reserved stock
- **SUPPLIER** — the vendor supplying goods in a GRN
- **CUSTOMER** — the recipient of goods in an ORDER_PICK or RETURN

## Inventory Records

**InventoryBalance** holds the current stock level for each SKU at each location. The key fields are:
- `on_hand` — total units physically present
- `reserved` — units allocated to pending orders
- `available` — on_hand minus reserved (can be picked or moved)

**InventoryLedger** is an immutable audit trail. Every stock movement (GRN, putaway, move, pick, adjustment) writes a ledger entry. It records the SKU, location, quantity delta, transaction reference, and timestamp. Use the ledger for historical analysis; use InventoryBalance for current state.
