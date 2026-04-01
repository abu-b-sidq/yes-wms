# Goods Receiving (GRN) Procedures

## Overview
A Goods Received Note (GRN) records the receipt of items into the warehouse. Items land in the PRE_PUTAWAY staging zone until they are putaway into storage locations.

## Standard GRN Process
1. Verify the delivery against the purchase order or supplier reference
2. Count and inspect all items for damage or discrepancies
3. Create a GRN using the WMS with the supplier reference number
4. Specify each SKU code and quantity received
5. Note any damaged, short-delivered, or rejected items in the GRN notes field
6. Execute the GRN — stock will credit to the PRE_PUTAWAY zone
7. Hand items over to the putaway team for storage

## Handling Damaged or Short Deliveries
- Record damaged quantities in the GRN notes: "Qty 5 SKU-X damaged, not received"
- For partial deliveries, create the GRN for the quantity actually received only
- Create an ADJUSTMENT transaction if items are later rejected after initial receipt

## Quality Checks
- Temperature-sensitive goods must be checked with a thermometer before GRN
- Expiry dates must be verified and recorded in the batch_number field
- Heavy items: ensure weight matches delivery note before GRN

## Common Issues
- "SKU not found" error: Check the SKU code with the masters team
- "Facility not active" error: Ensure the correct facility is selected
- Duplicate GRN: Search by reference number before creating to avoid duplicates
