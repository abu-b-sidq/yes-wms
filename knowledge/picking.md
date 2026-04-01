# Order Picking Procedures

## Overview
Order Pick (ORDER_PICK) transactions record the movement of stock from storage locations to fulfill customer orders or invoices.

## Standard Pick Process
1. Receive a pick task from the supervisor or WMS
2. Navigate to the specified source location
3. Verify the SKU code and quantity to be picked
4. Create an ORDER_PICK transaction in WMS with source location and invoice/order reference
5. Execute the pick — stock is debited from the location and assigned to the invoice entity

## FEFO / FIFO Rules
- Always pick the oldest batch first (First Expired, First Out for perishables)
- If multiple batches are available, pick the batch with the earliest expiry date
- Record the correct batch number in the pick transaction

## Short Picks
- If insufficient stock is at the specified location, check adjacent locations in the same zone
- Use `wms_get_inventory_balances` to find alternative locations with available stock
- Report the short pick to the supervisor — do not substitute a different SKU
- Create a partial pick for the available quantity and note the shortfall

## Quality Checks During Pick
- Inspect items for damage before picking — do not pick damaged goods
- Check expiry dates — do not pick expired or nearly-expired items without authorization
- Verify pack quantities (case picks vs unit picks)

## Common Issues
- "Insufficient available quantity" error: Check if stock is reserved for another order
- "Location empty" error: Run inventory balance check and notify supervisor
- Wrong item picked: Reverse the pick with a MOVE transaction back to the location
