# Putaway Procedures

## Objective
Putaway transfers inbound stock from staging into the correct storage location while preserving traceability, storage discipline, and future pick efficiency.

## Putaway Design Principles
- Put away quickly enough to keep inbound staging clear and inventory visible to planning teams.
- Put away accurately enough that pickers trust the location record without searching.
- Use slotting rules that reflect velocity, cube, weight, compatibility, and handling constraints.
- Avoid double handling. A poor first putaway creates later moves, congestion, and mispicks.

## Standard Putaway Process
1. Review the GRN or inbound staging list and confirm stock is released for putaway.
2. Verify SKU, quantity, batch or lot, serial range, and any temperature or hazmat requirement.
3. Select the destination location according to directed putaway, slotting rules, and current capacity.
4. Confirm the destination location is active, compatible, and not blocked for maintenance or count.
5. Move stock from PRE_PUTAWAY or inbound staging using the correct equipment.
6. Scan or verify the source handling unit and destination location.
7. Create the PUTAWAY transaction in WMS with SKU, quantity, batch, and destination code.
8. Execute the transaction only after stock is physically placed and labeled.
9. Check that location labels remain visible and pallets are stored safely.
10. Clear residual staging material and update any physical handoff board if used.

## Putaway Strategies

### Directed Putaway
- Best for controlled environments with defined slotting rules.
- System or supervisor chooses the location based on product and capacity rules.
- Improves consistency and reduces operator judgment variation.

### Fixed Location Putaway
- Use for fast movers, regulated products, or SKUs that benefit from stable pick faces.
- Makes training easier and simplifies replenishment.
- Can waste space if fixed slots are oversized.

### Random or Dynamic Putaway
- Use for reserve storage or highly variable assortment.
- Maximizes space utilization when location discipline is strong.
- Requires reliable scanning and search visibility to avoid hidden stock.

### Forward Pick and Reserve Split
- Store high-access inventory in forward pick faces.
- Put excess pallet stock into reserve locations.
- Replenish forward locations from reserve rather than picking full pallets from reserve each time.

## Location Assignment Rules
- Fast-moving SKUs should be near dispatch and within the ergonomic golden zone where possible.
- Slow movers belong in higher or more remote storage.
- Heavy, bulky, or unstable goods stay at lower levels or floor storage.
- Fragile items should avoid high-traffic damage-prone lanes.
- Cold-chain items go only to approved temperature-controlled locations.
- Hazardous stock goes only to compatible hazmat locations with segregation controls.
- Products frequently ordered together may be stored in nearby pick zones, but not at the cost of safety or contamination control.

## Slotting and Storage Techniques
- Use cube and weight, not just unit count, when choosing the final slot.
- Keep one active SKU per bin unless mixed-SKU storage is explicitly allowed and clearly labeled.
- Separate lots when FEFO, quality release, or traceability requirements make commingling risky.
- Reduce honeycombing by using pallet positions that fit the pallet footprint instead of oversized empty space.
- Use overflow locations with clear purpose codes rather than ad hoc floor staging.
- For seasonal or promotional stock, use temporary high-access locations only for the campaign window.

## FEFO, FIFO, and Batch Discipline
- Older acceptable lots should be more accessible than newer lots when FEFO or FIFO applies.
- Do not bury short-dated lots behind fresh stock.
- Mixed expiry in one location should be avoided unless the pick process is scan-enforced.
- If lot separation is required by customer or regulation, never mix lots in the same pick face.

## Capacity and Safety Rules
- Never exceed bin height, weight, or pallet-position rating.
- Confirm rack condition before storing full pallets in damaged locations.
- Keep aisles, fire exits, and emergency equipment clear.
- Store unstable or leaning pallets only after rework or rewrap.
- Respect load orientation rules for crush-sensitive products.

## Exception Handling

### No Suitable Location Found
1. Check approved overflow or reserve locations in the same storage family.
2. Escalate when slotting master data is outdated or capacity is structurally insufficient.
3. Do not leave stock in aisles as an unofficial storage method.

### Full Pick Face
1. Put excess stock into reserve instead of overfilling the pick face.
2. Trigger replenishment logic if the pick face is undersized for current demand.
3. Review slot sizing during the next slotting cycle.

### Wrong Zone or Wrong Location
1. Stop and correct immediately with a MOVE transaction.
2. Record the reason if the error was caused by unclear labels, poor slotting, or bad master data.
3. Treat repeated wrong-zone putaway as a process-design issue, not only an operator issue.

### Staging Aged Too Long
1. Prioritize aged PRE_PUTAWAY stock first.
2. Separate pending-quality stock from ready-for-putaway stock so teams do not waste search time.
3. Escalate if inbound volume exceeds putaway capacity or labor coverage.

## Putaway Control Points
- Scan confirmation at both source and destination whenever possible.
- Visible location labels must face the aisle after final placement.
- Handling unit IDs should remain tied to pallet or carton after storage.
- Any deviation from directed location should be recorded with a reason.
- Daily review of empty pick faces and overloaded reserve locations helps prevent reactive firefighting.

## Putaway KPIs
- Putaway cycle time
- Dock-to-stock lead time
- Putaway accuracy
- Percentage of stock left in PRE_PUTAWAY beyond target
- Empty pick face occurrences
- Rehandle rate caused by poor first-slot decisions

## Consultant Improvement Techniques
- Build slotting rules by velocity class, cube, and handling profile rather than by habit.
- Use travel heat maps to place the top 20 percent of picked SKUs in the most ergonomic slots.
- Review overflow usage weekly; chronic overflow means slot sizes or storage profile are wrong.
- Separate putaway productivity from putaway accuracy in reporting so speed pressure does not hide location errors.
- Use dedicated putaway waves after large inbound peaks to keep staging under control.
