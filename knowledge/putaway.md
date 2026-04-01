# Putaway Procedures

## Overview
Putaway moves items from the PRE_PUTAWAY staging zone to their designated storage locations. This step must be completed promptly to keep the staging area clear.

## Standard Putaway Process
1. Pick items from the PRE_PUTAWAY zone
2. Identify the destination storage location (bin/shelf)
3. Create a PUTAWAY transaction in the WMS
4. Specify the SKU code, quantity, and destination location code
5. Execute the putaway — stock moves from PRE_PUTAWAY to the destination

## Location Assignment Rules
- Fast-moving SKUs go to Zone A (ground-level, near dispatch)
- Slow-moving SKUs go to Zone B or Zone C (upper shelves)
- Bulk/heavy items go to Zone D (floor storage)
- Temperature-sensitive items go to the COLD zone
- Hazardous items go to the HAZ zone (requires special authorization)

## Batch Management
- Always record the batch number during putaway for traceability
- Items with different batch numbers must be stored separately (no mixed batches in one bin)
- FEFO (First Expired, First Out) applies — older batches must be placed closer to the pick face

## Capacity Rules
- Never overfill a bin location beyond its rated capacity
- If a bin is full, use an overflow location in the same zone
- Report full zones to the warehouse manager for re-slotting

## Common Issues
- "Insufficient stock in PRE_PUTAWAY" error: The GRN may not have been executed yet
- "Location not found" error: Verify the location code with the masters list
- Items in wrong zone: Create a MOVE transaction to correct location
