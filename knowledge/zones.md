# Warehouse Zones and Locations

## Zone Types

### PRE_PUTAWAY (Staging Zone)
- Temporary holding zone for items received via GRN
- Items must be putaway within 24 hours
- Do not count PRE_PUTAWAY stock in available inventory for orders
- If items remain in PRE_PUTAWAY for more than 48 hours, escalate to warehouse manager

### Storage Zones (A, B, C, D)
- Zone A: High-velocity, ground floor, nearest to dispatch
- Zone B: Medium-velocity, mid-shelf storage
- Zone C: Low-velocity, high shelf, bulk items
- Zone D: Floor storage for oversized or pallet quantities

### Dispatch Zone
- Temporary holding for picked orders awaiting dispatch
- Stock in Dispatch zone is assigned to INVOICE entities
- Orders must leave Dispatch within the same business day

### COLD Zone
- Refrigerated storage for temperature-sensitive items
- Temperature must be maintained between 2°C and 8°C
- Access logged — requires authorization for entry

### HAZ Zone
- Hazardous materials storage
- Restricted access — requires HAZMAT certification
- Requires separate documentation for all movements

## Location Code Format
Location codes follow the format: `ZONE-AISLE-BAY-LEVEL`
- Example: `A-01-03-02` = Zone A, Aisle 1, Bay 3, Level 2
- Example: `B-02-05-01` = Zone B, Aisle 2, Bay 5, Ground level (01)

## Finding Available Locations
Use `wms_get_inventory_balances` filtered by entity_type=LOCATION to see current stock levels per bin.
Empty locations have no balance record or a zero on_hand quantity.
