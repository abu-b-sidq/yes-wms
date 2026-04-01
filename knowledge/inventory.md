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
