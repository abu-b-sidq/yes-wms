# Warehouse Zones and Locations

## Zone Design Principles
- Every zone should have a clear purpose, ownership, and movement rule.
- Inventory visibility improves when temporary zones are explicit instead of informal floor staging.
- Fast-moving work should be close to the next process step.
- Incompatible material flows should be physically separated to reduce errors and safety risk.

## Recommended Zone Types

### PRE_PUTAWAY
- Temporary holding zone for newly received stock
- Should be cleared within the target dock-to-stock window
- Not a long-term storage area
- Stock here should not be treated as normal pick-face availability

### Forward Pick Zone
- Primary picking area for fast-moving SKUs
- Sized for easy access and rapid replenishment
- Best suited to each-pick or case-pick demand

### Reserve Storage
- Overflow or pallet storage supporting replenishment
- Optimized for space, not direct picking speed
- Use disciplined labeling because search time grows fast in reserve areas

### Cross-Dock Zone
- For inbound stock that is already committed to urgent outbound demand
- Minimize dwell time and avoid unnecessary putaway
- Requires tight document and quantity control

### Dispatch Staging
- Temporary holding area for picked and consolidated orders awaiting loading
- Organize by route, carrier, vehicle, wave, or cutoff time
- Orders should not remain here longer than policy allows

### Quarantine or Quality Hold
- Restricted area for damaged, expired, suspect, or inspection-pending stock
- Physically and systemically separated from usable inventory
- Release requires approved disposition

### Returns Zone
- Dedicated reverse-logistics area for customer returns
- Separate unopened, damaged, refurbishable, and RTV material
- Do not mix returns with normal putaway queues

### Value-Added Services or Kitting
- For relabeling, promotional bundling, light assembly, or compliance preparation
- Keep material control tight so partially processed stock does not disappear between statuses

### COLD Zone
- Controlled-temperature storage for sensitive products
- Monitor and log temperature according to product policy
- Keep exposure time outside controlled space to a minimum

### HAZ Zone
- Restricted hazardous materials storage
- Follow segregation, documentation, and certification requirements
- Use only approved containers and handling methods

## Storage Zone Profiles
- Zone A: high-velocity, ergonomic access, close to dispatch
- Zone B: medium-velocity storage
- Zone C: low-velocity or higher-level storage
- Zone D: floor storage for bulky or pallet-heavy items

These labels are examples. The real rule is to assign zones by operational purpose, not only alphabetically.

## Location Code Format
Location codes should be human-readable and scan-friendly.

Recommended format: `ZONE-AISLE-BAY-LEVEL-POSITION`

Examples:
- `A-01-03-02-01`
- `B-02-05-01-02`
- `COLD-04-01-01-01`

## Location Master Data Standards
- Every location should carry zone, aisle, bay, level, and position attributes.
- Record capacity by pallet, carton, cube, or weight as appropriate.
- Mark blocked, count-frozen, or maintenance locations clearly in both WMS and on the floor.
- Use consistent naming for pick faces, reserve racks, floor slots, and staging lanes.

## Compatibility Rules
- Do not place food, chemicals, and odor-sensitive goods together unless policy explicitly allows it.
- Keep hazardous classes segregated according to safety rules.
- Keep high-value stock in controlled-access zones.
- Place fragile goods where collision and crush risk are low.
- Separate returns and suspect stock from saleable inventory.

## 5S and Housekeeping Expectations
- No unlabeled stock on the floor
- No unofficial overflow in aisles or near exits
- Empty pallets and dunnage removed quickly
- Damaged rack, labels, or floor markings repaired promptly
- Zone ownership assigned for daily visual control

## Zone Review Triggers
- PRE_PUTAWAY aging beyond target
- Dispatch congestion before carrier cutoff
- Repeated stockouts in the forward pick zone
- Chronic overflow in reserve or floor staging
- High count variance concentrated in one zone
- Repeated wrong-location or wrong-zone moves

## Finding Available Locations
Use `wms_get_inventory_balances` filtered by `entity_type=LOCATION` to understand which bins currently contain stock.

For empty-slot decisions:
- an absent balance record may indicate an empty location
- a zero `on_hand` quantity may also indicate an empty location
- always validate the location is active, compatible, and not blocked before assigning new stock

## Consultant Improvement Techniques
- Use travel heat maps to redesign zone adjacency based on actual movement paths.
- Split operational zones when one area serves conflicting purposes, such as staging and storage together.
- Treat recurring aisle congestion as a layout problem, not only a staffing problem.
- Review temporary zones every month; temporary zones often become permanent bad habits unless deliberately cleaned up.
