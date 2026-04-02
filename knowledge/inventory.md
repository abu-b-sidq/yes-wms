# Inventory Management Procedures

## Inventory Concepts
- **on_hand**: Total physical quantity in the location
- **reserved**: Quantity allocated to pending orders (not available for new picks)
- **available**: on_hand minus reserved — what can be picked for new orders

## Cycle Counting
Cycle counting is the process of counting a subset of inventory on a rotating basis rather than shutting down for a full stocktake.

### Cycle Count Process
1. Select the zone or locations to count
2. Create a CYCLE_COUNT transaction in WMS
3. Count physical items in each location
4. Enter actual counts into the system
5. Review discrepancies before executing
6. Execute the cycle count to update balances

### Count Frequency
- Zone A (fast-moving): Count weekly
- Zone B (medium-moving): Count monthly
- Zone C/D (slow-moving): Count quarterly

## Inventory Adjustments
Use ADJUSTMENT transactions for:
- Damaged goods write-off
- Quantity corrections after cycle count discrepancies
- Stock received outside normal GRN process (found stock)

All adjustments require supervisor approval and must include a reason in the notes field.

## Inventory Discrepancy Investigation
When a discrepancy is found:
1. Check the inventory ledger for recent movements (use `wms_get_inventory_ledger`)
2. Look for pending transactions that may not be executed
3. Check if stock was recently moved to a different location
4. If unexplained, create an ADJUSTMENT with a full description in notes

## Stock Reservation
When an order is placed, stock is automatically reserved (reducing available quantity).
- Reserved stock cannot be picked for other orders
- Reservations are released when an order is cancelled
- Check available (not on_hand) before committing to orders

## Querying Available Inventory for a SKU

When a user asks "what is the available inventory for SKU X", "how much stock do we have of SKU X", "what is the on-hand quantity for SKU X", or any similar inventory availability question, **always filter by `entity_type = LOCATION`**.

The `InventoryBalance` table tracks stock across multiple entity types: LOCATION, ZONE, INVOICE, VIRTUAL_BUCKET, SUPPLIER, and CUSTOMER. Only the LOCATION entity type represents physical stock sitting on warehouse shelves. The other entity types represent stock that is in transit, staged, or allocated:

- **LOCATION** — Physical bin or shelf. This is the real, available warehouse inventory.
- **ZONE** (e.g., PRE_PUTAWAY) — Staging area. Stock here has been received but not yet put away. It is not yet in a storage location.
- **INVOICE** — Stock picked for a customer order. It has left its storage location and is awaiting dispatch.
- **VIRTUAL_BUCKET, SUPPLIER, CUSTOMER** — Logical/accounting entries, not physical stock.

Summing across all entity types would double-count units — the same physical goods can appear in both a ZONE (while staged) and later a LOCATION (after putaway). Always use `entity_type = "LOCATION"` when calling `wms_get_inventory_balances` to answer inventory availability questions.

Example: to answer "how much SKU-001 is available?", call `wms_get_inventory_balances` with `sku_code="SKU-001"` and `entity_type="LOCATION"`.
