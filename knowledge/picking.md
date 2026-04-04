# Order Picking Procedures

## Objective
Order picking converts available inventory into customer-ready demand fulfillment. The goal is to pick the right SKU, lot, quantity, and pack configuration at the lowest safe travel cost.

## Picking Principles
- Accuracy is more important than raw speed on customer-critical or regulated orders.
- Pick from the system-directed location unless an approved exception process is followed.
- Confirm SKU, lot, unit of measure, and quantity before removing stock.
- Short picks and substitutions should be visible immediately to planning and customer service teams.

## Picking Methods

### Discrete Picking
- One picker completes one order at a time.
- Best for simple operations, high-value orders, or training environments.
- Easy to control but can increase travel.

### Batch Picking
- Pick multiple orders in one pass when lines share similar SKUs or zones.
- Improves travel efficiency for small-order profiles.
- Requires strong order segregation during sortation.

### Cluster Picking
- Pick multiple orders simultaneously into separate totes or compartments.
- Works well for e-commerce and piece-pick profiles.
- Use only when container labeling and confirmation are reliable.

### Zone Picking
- Each picker owns a physical zone.
- Orders move through zones by tote, cart, or conveyor.
- Reduces long travel but requires good handoff discipline.

### Wave Picking
- Release orders in time-based or carrier-based waves.
- Useful when dispatch cutoffs and vehicle schedules matter.
- Avoid oversized waves that flood staging and create congestion.

## Standard Pick Process
1. Review the pick task, order priority, service commitment, and any special handling notes.
2. Confirm the assigned source location, SKU, unit of measure, lot or batch, and quantity.
3. Travel to location using the most efficient approved route.
4. Verify the location label before touching stock.
5. Scan or visually confirm the SKU and lot.
6. Pick the required quantity using correct pack-breaking rules.
7. Inspect picked units for damage, leakage, contamination, or expiry concerns.
8. Place stock into the correct order tote, pallet, or dispatch container.
9. Create or complete the ORDER_PICK transaction in WMS.
10. Execute the transaction so stock moves from location inventory to invoice or order allocation state.
11. Label the picked container and move it to dispatch staging or the next zone handoff.
12. Escalate exceptions immediately rather than silently editing customer intent.

## Stock Rotation Rules
- FEFO applies to perishable or expiry-sensitive SKUs.
- FIFO applies where lot age matters but explicit expiry is not the main driver.
- Always record the actual lot or batch picked if the system requires it.
- Never pick expired product without documented management approval for non-sale use cases.

## Pack and Unit-of-Measure Rules
- Respect pick units: pallet, case, inner, and each.
- If the task requires full-case picking, do not break cases without approval.
- For broken-case picks, ensure residual quantity remains labeled and location-ready.
- Use conversion rules carefully; many pick errors come from confusing eaches and cases.

## Short Pick Procedure
1. Recount the source location.
2. Check for mixed product, hidden cartons, or pallet shadow stock.
3. Review nearby approved alternate locations in the same zone.
4. Use inventory visibility to confirm whether stock exists elsewhere.
5. Complete a partial pick only for the physically confirmed quantity.
6. Record the shortfall reason and notify the supervisor or planner.

## Pick Quality Checks
- Confirm barcode or product description if the SKU label is damaged.
- Check lot, expiry, and packaging condition before putting stock into the order container.
- For customer-specific compliance orders, verify carton markings and any required documents.
- For high-value items, perform a second-person or scan verification at packout.

## Exception Handling

### Empty Location
- Treat as a possible inventory-accuracy issue, not just a picking problem.
- Search approved alternate locations before raising the exception.
- Trigger a count or replenishment review if the empty location should have contained stock.

### Wrong Item at Location
- Stop and segregate the misplaced stock.
- Do not pick around a location integrity problem.
- Report the mismatch so a correction move or inventory investigation can be performed.

### Damaged Pick Face Stock
- Do not ship damaged goods.
- Segregate damaged units and record the affected quantity.
- Pick replacement stock from another approved location if available.

### Barcode or Label Failure
- Use secondary SKU verification such as description, lot, or supervisor check.
- Relabel the container or location after verification to prevent repeat failure.

### Substitution Request
- Do not substitute a different SKU unless the business process explicitly allows it.
- If substitution is allowed, capture the approval and replacement SKU traceability.

## Handoff to Dispatch
- Consolidate all lines belonging to the same shipment before final staging.
- Use staging lanes by route, carrier, order priority, or cutoff time.
- Ensure picked stock is not left in unmarked carts or floor positions.
- Update order status promptly so dispatch and customer service see the same reality.

## Picking KPIs
- Pick accuracy
- Lines picked per labor hour
- Units picked per labor hour
- Travel time percentage
- Short pick rate
- Re-pick or correction rate
- Order cycle time from release to stage complete

## Consultant Improvement Techniques
- Use ABC velocity analysis to decide which SKUs deserve forward pick faces.
- Review pick path design to remove backtracking and aisle crossing.
- Apply slotting affinity so common order combinations are physically closer.
- Track mispicks by root cause: wrong slot, wrong label, wrong UOM, poor training, or master data error.
- Do not use productivity targets that encourage skipping scan confirmation on risky SKUs.
