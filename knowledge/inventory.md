# Inventory Management Procedures

## Inventory Concepts
- `on_hand`: total physical quantity currently recorded in a storage or logical entity
- `reserved`: quantity committed to demand and not available for new allocation
- `available`: `on_hand - reserved`, which is the quantity that can still be promised or picked
- `allocated`: stock linked to a specific order, wave, or downstream activity
- `quarantine` or `hold`: stock physically present but blocked from normal use

## Inventory Control Principles
- Accuracy matters more than volume if the operation depends on fast picks and promise dates.
- Keep one source of truth for every movement. Manual side lists create reconciliation gaps.
- Separate usable, damaged, expired, returned, and quality-hold stock statuses.
- Investigate root causes, not only quantity differences. Repeated errors usually come from process design.

## Inventory Segmentation Techniques

### ABC Analysis
- A items: high-value or high-velocity SKUs needing tight control and frequent review
- B items: medium importance with standard control
- C items: low impact items with lighter counting frequency

### XYZ or Demand Variability
- X items: stable demand
- Y items: seasonal or moderately variable demand
- Z items: erratic demand

### Combining ABC and XYZ
- AX items deserve the strongest service-level and counting discipline.
- CZ items may need simpler controls and more cautious replenishment.
- Use combined segmentation to set count frequency, slotting priority, and safety stock policy.

## Cycle Counting
Cycle counting is the process of counting a subset of inventory regularly instead of shutting down for a full wall-to-wall count.

### Cycle Count Process
1. Freeze the target locations or SKUs where policy requires count integrity.
2. Select count tasks based on ABC class, discrepancy history, and recent movement risk.
3. Use blind counting where possible so counters do not see the system quantity first.
4. Count physical stock by SKU, lot, and unit of measure.
5. Recount variances above tolerance with a second person.
6. Check recent transactions, open tasks, and mislocated stock before adjusting.
7. Create a `CYCLE_COUNT` transaction or approved adjustment in WMS.
8. Execute the correction only after the investigation is documented.
9. Classify the root cause and assign corrective action.

### Count Frequency Guidance
- A items or high-risk pick faces: weekly or more often
- B items: monthly
- C items: quarterly
- High-value cages, cold chain, and problem zones: based on risk, not just value

### Best Practices
- Count after the major wave closes, not during the busiest movement window.
- Count by logical area so one team can own the correction path.
- Track first-count accuracy separately from final reconciled accuracy.

## Inventory Adjustments
Use `ADJUSTMENT` transactions for:
- damaged goods write-off
- found stock after validation
- shrinkage or loss confirmation
- quantity corrections after approved count review
- quality-release conversions if a formal movement type does not exist

### Adjustment Governance
- Every adjustment needs a reason code and narrative note.
- Material financial impact should require supervisor approval.
- Repeated adjustments on the same SKU or location should trigger a root-cause review.
- Never use adjustments to hide poor receiving, putaway, or picking discipline.

## Inventory Discrepancy Investigation
When a discrepancy is found:
1. Check the inventory ledger for the last relevant movements.
2. Look for open, failed, or partially completed transactions.
3. Confirm whether stock was moved without execution or staged in the wrong zone.
4. Inspect nearby bins for mislocated cartons or pallets.
5. Review recent receipts, replenishments, picks, and returns involving the SKU.
6. Check whether unit-of-measure conversion caused the mismatch.
7. Correct with an approved adjustment only after the likely root cause is understood.

## Negative Inventory Prevention
- Do not allow picks from unconfirmed or stale locations.
- Tighten execution timing so physical movement and system movement happen together.
- Require scan confirmation for high-risk steps such as reserve-to-pick replenishment.
- Investigate any pattern where one zone frequently goes negative while another carries unexplained excess.

## Aging and Obsolescence Management
- Review slow-moving and non-moving inventory on a recurring cadence.
- Separate excess, obsolete, damaged, and customer-return stock so action plans are clear.
- Use inventory aging buckets such as 0-30, 31-60, 61-90, and 90+ days.
- Actions may include promotion, relocation, supplier return, kitting, rework, or write-down planning.

## Reservation and Availability
- Reserved stock cannot be used for new demand until reservation is released.
- Available quantity is the decision field for new commitments, not raw `on_hand`.
- Review aged reservations because stale allocations reduce apparent service capacity.
- For wave operations, release reservations quickly when orders are cancelled or de-prioritized.

## Inventory Health KPIs
- Inventory accuracy
- First-count accuracy
- Adjustment rate
- Negative inventory incidents
- Aged inventory percentage
- Reservation aging
- Stockout frequency
- Fill rate on available inventory

## Querying Available Inventory for a SKU

When a user asks "what is the available inventory for SKU X", "how much stock do we have of SKU X", "what is the on-hand quantity for SKU X", or any similar inventory availability question, always filter by `entity_type = LOCATION`.

The `InventoryBalance` table tracks stock across multiple entity types: `LOCATION`, `ZONE`, `INVOICE`, `VIRTUAL_BUCKET`, `SUPPLIER`, and `CUSTOMER`. Only the `LOCATION` entity type represents physical stock sitting in warehouse storage locations. The other entity types represent stock that is in transit, staged, or allocated:

- `LOCATION`: physical bin or shelf inventory and the true answer for storage availability
- `ZONE`: staging or operational areas such as `PRE_PUTAWAY`; useful for process visibility, not customer promise stock
- `INVOICE`: stock already picked or assigned to an order
- `VIRTUAL_BUCKET`, `SUPPLIER`, `CUSTOMER`: logical or accounting-oriented balances, not shelf stock

Summing all entity types will double-count units. The same goods can appear in a `ZONE` while staged and later in a `LOCATION` after putaway. Always use `entity_type="LOCATION"` when calling `wms_get_inventory_balances` to answer availability questions.

Example: to answer "how much SKU-001 is available?", call `wms_get_inventory_balances` with `sku_code="SKU-001"` and `entity_type="LOCATION"`.

## Consultant Improvement Techniques
- Use Pareto analysis to identify the top SKUs and locations driving most discrepancies.
- Classify every discrepancy by root cause category so training, slotting, and master-data fixes are visible.
- Review adjustment reasons weekly with operations, inventory control, and warehouse leadership together.
- Use count accuracy by process area to find whether the real issue sits in receiving, putaway, replenishment, picking, or returns.
