# Replenishment Procedures

## Objective
Replenishment keeps forward pick locations stocked from reserve or bulk storage so picks can happen without delay or search.

## When Replenishment Should Trigger
- Min-max trigger: replenish when the pick face falls below the minimum quantity.
- Wave trigger: top up locations before a planned pick wave.
- Demand trigger: replenish when upcoming allocated demand exceeds current pick-face available stock.
- Calendar trigger: run scheduled top-offs at defined times for stable operations.
- Visual trigger: use only as a last resort or backup, because visual-only replenishment is easy to miss.

## Replenishment Strategies

### Min-Max Replenishment
- Define a minimum and maximum quantity for each pick face.
- Replenish back to max when stock drops below min.
- Works best for stable demand patterns.

### Demand-Based Replenishment
- Calculate replenishment based on short-term order demand and expected picks.
- Better for volatile or promotional items.
- Requires accurate reservation and wave visibility.

### Time-Based Top-Off
- Replenish before shift start, lunch break, or evening wave.
- Useful in operations where pick disruption is more costly than extra movement.

### Emergency Replenishment
- Triggered during active picking when a picker hits an empty or insufficient location.
- Should be measured closely because too much emergency replenishment signals poor slotting or planning.

## Standard Replenishment Process
1. Review replenishment tasks and prioritize by wave urgency, stockout risk, and route efficiency.
2. Confirm source reserve location, destination pick face, SKU, lot, and quantity.
3. Verify the source location contains the expected stock and the destination is ready to receive it.
4. Move the stock using the correct equipment and handling unit controls.
5. Scan or verify source and destination locations.
6. Create and execute the replenishment movement, typically as a `MOVE` transaction when no separate replenishment type exists.
7. Confirm the destination pick face quantity and label visibility.
8. Clear the source location accurately if the pallet or carton is fully consumed.

## Replenishment Priority Rules
- Service-critical and same-day orders first
- Empty pick faces before low-stock pick faces
- High-velocity A items before slow movers
- Frozen, chilled, hazmat, or compliance-sensitive stock based on product handling deadlines
- Full-pallet reserve moves before broken-case scavenging where possible

## Lot and Shelf-Life Rules
- Replenish with the correct FEFO or FIFO lot.
- Do not top up a short-dated front lot with a fresher lot behind it if the picker cannot clearly distinguish them.
- Avoid mixing lots in one pick face unless the process is scan-controlled and policy allows it.

## Source and Destination Rules
- Reserve locations should hold the cleanest available replenishment source.
- Pick faces should be sized for their actual demand profile, not historical habit.
- Do not replenish into blocked, count-frozen, or damaged locations.
- If the pick face repeatedly needs emergency replenishment, review min-max settings or slot size.

## Exception Handling

### Source Not Found
1. Search approved alternate reserve locations.
2. Check if the source stock was already moved, picked, or mislocated.
3. Raise an inventory accuracy issue if the reserve balance is not physically present.

### Destination Full
1. Recount the destination location.
2. Verify whether residual stock, empty packaging, or mixed cartons are occupying capacity.
3. Move only the quantity that fits safely and revise the remaining replenishment plan.

### Wrong Lot in Pick Face
1. Stop the replenishment.
2. Correct the existing lot issue before adding more stock.
3. Escalate if pick-face design does not support required lot rotation.

## Replenishment KPIs
- Emergency replenishment rate
- Pick-face stockout frequency
- Replenishment response time
- Replenishment accuracy
- Reserve-to-pick travel time
- Number of picker waits caused by missing replenishment

## Consultant Improvement Techniques
- Tie replenishment logic to demand class and wave schedule, not a one-size-fits-all threshold.
- Use heat maps to place reserve stock close to the pick zones it supports most.
- Track emergency replenishment by SKU to identify poor slot sizing and bad min-max settings.
- Separate replenishment labor from picking labor during peak hours if pick interruptions are frequent.
