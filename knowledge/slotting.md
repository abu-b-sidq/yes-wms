# Slotting and Storage Optimization

## Objective
Slotting places each SKU in the right physical location to balance service speed, safety, ergonomics, capacity, and replenishment cost.

## Slotting Principles
- Put the fastest-moving and highest-touch items in the easiest-to-reach slots.
- Use cube, weight, and handling profile, not just order count.
- Keep products that travel together close enough to reduce picker steps.
- Revisit slotting regularly because demand, assortment, and seasonality change.

## Core Slotting Techniques

### ABC Velocity Slotting
- A items: best access and shortest travel
- B items: standard access
- C items: remote or upper storage

### Cube-Based Slotting
- Match SKU dimensions and pallet footprint to slot capacity.
- Prevent over-slotting small items into oversized locations and under-slotting bulky items into small bins.

### Golden Zone Slotting
- Place the highest-frequency each-pick items between knee and shoulder height where safe.
- Reserve top and bottom levels for lower-frequency or equipment-handled stock.

### Affinity Slotting
- Store SKUs often ordered together in nearby locations.
- Use this for common kits, order bundles, or route clusters.

### Family Grouping
- Group products by category, handling needs, temperature, hazard class, or customer compliance profile.
- Avoid family grouping if it worsens congestion for top movers.

### Seasonality and Event Slotting
- Move promotional and seasonal winners into better slots before demand peaks.
- De-slot them after the peak to avoid wasting premium space.

## Slotting Review Process
1. Pull recent demand, line frequency, quantity per pick, and cube data.
2. Classify SKUs by velocity and handling profile.
3. Review current travel, replenishment burden, and pick-face stockouts.
4. Propose new slot assignments based on demand and safety constraints.
5. Validate zone compatibility, rack capacity, and lot-control requirements.
6. Execute relocations in a controlled wave, not ad hoc throughout the day.
7. Update location master data and train operators on changed slots.
8. Review results after the next demand cycle.

## Signs Slotting Is Wrong
- Frequent empty pick faces for top SKUs
- Excess emergency replenishment
- Pickers crossing the building for common lines
- Congestion in one aisle while nearby aisles are quiet
- Slow movers occupying premium ergonomic slots
- High mispick rate in compressed or confusing shelves

## Relocation Procedure
1. Approve the relocation list.
2. Freeze or control demand during the move window if needed.
3. Move stock with a traceable `MOVE` transaction.
4. Update labels and remove any old location references.
5. Verify downstream pick tasks point to the new slot before releasing normal work.

## Slotting Constraints
- Respect temperature, hazmat, security, and customer segregation rules.
- Keep heavy or crush-sensitive products in safe storage positions.
- Do not create mixed-SKU clutter just to maximize cube use.
- Consider replenishment frequency; a perfect pick slot is still bad if reserve support is far away.

## Slotting KPIs
- Pick travel distance
- Lines picked per hour
- Replenishment touches per order line
- Pick-face stockout rate
- Mispick rate by zone
- Space utilization

## Consultant Improvement Techniques
- Use cube movement or COI-style thinking: place items with the highest movement-to-space impact in the best slots.
- Re-slot top movers monthly and the full profile quarterly or seasonally.
- Use a small pilot area before moving the entire warehouse.
- Measure net effect, not only travel savings; good slotting also improves safety and count accuracy.
