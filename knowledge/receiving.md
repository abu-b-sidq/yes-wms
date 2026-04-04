# Goods Receiving (GRN) Procedures

## Objective
Receiving converts inbound supplier stock into controlled warehouse inventory. The goal is to get product from dock to a verified internal status quickly, accurately, and with full traceability.

## Core Receiving Principles
- Never receive against assumptions. Match physical stock to documents, labels, and expected SKU data.
- Separate physical receipt from financial acceptance when quality status is uncertain.
- Keep dock work fast, but do not skip lot, expiry, serial, or damage checks that affect downstream traceability.
- Treat receiving as the first inventory-accuracy control point. Bad receipts create putaway, picking, and reconciliation problems later.

## Standard GRN Process
1. Confirm the inbound appointment, supplier, PO or reference number, vehicle number, and expected unload window.
2. Check trailer seal, vehicle condition, temperature logs when applicable, and obvious transit damage before unloading.
3. Stage goods by supplier document or ASN line to prevent mixing multiple receipts.
4. Perform a three-way comparison between PO or ASN, physical labels, and actual quantity received.
5. Count units using the correct handling unit logic: pallet, case, inner pack, or each.
6. Inspect packaging integrity, expiry date, batch or lot number, serial number, and labeling compliance.
7. Segregate damaged, short, over-delivered, or unidentified material before system posting.
8. Create the GRN in WMS using the supplier reference, document date, and receiving notes.
9. Enter each SKU with the quantity actually accepted into warehouse control.
10. Capture lot, batch, serial, expiry, temperature, and pallet ID data where required.
11. Execute the GRN so inventory lands in the PRE_PUTAWAY or designated inbound staging zone.
12. Attach or record discrepancy notes, photos, and exception reason codes before handoff to putaway or quality.

## Receiving Techniques

### Appointment Scheduling
- Use dock appointments to smooth labor and equipment demand across the day.
- Separate fast unloads, floor-loaded containers, chilled trucks, and inspection-heavy receipts into different appointment classes.
- Keep priority windows for critical SKUs, launch stock, and stockout recovery receipts.

### ASN and Pre-Advice
- Use ASN or supplier pre-alert data to pre-create receipt expectations and speed validation.
- Flag inbound lines for urgent cross-dock, quarantine, cold chain, or hazmat handling before the truck arrives.
- Pre-print pallet IDs or receiving labels when inbound volume is predictable.

### Blind Receiving
- For high-risk suppliers or audit programs, hide expected quantity from the receiver and require a physical count first.
- Compare blind count to expected quantity only after entry to reduce bias.
- Use blind receiving selectively because it improves control but can slow throughput.

### Tolerance Rules
- Define acceptable over, short, and damage tolerance by supplier and SKU class.
- Examples: consumer packaged goods may allow minor carton count variance; regulated or serialized items should allow no tolerance.
- Quantities outside tolerance require supervisor approval before GRN execution.

### Cross-Dock Identification
- If an inbound SKU is already committed to urgent customer demand, flag it for cross-dock instead of standard putaway.
- Cross-dock candidates should skip long staging dwell and move directly to dispatch or order consolidation.
- Use this only when documentation, quality, and quantity checks are complete.

### FEFO and Shelf-Life Control
- For perishable inventory, capture manufacturing date, expiry date, and remaining shelf life at receipt.
- Reject or quarantine stock below minimum remaining shelf-life policy.
- Older acceptable lots should be prioritized for putaway into pick faces that support FEFO execution.

### Serial and Lot Capture
- Serialized products require scan verification at receipt to prevent downstream traceability gaps.
- Mixed-lot pallets should be split or clearly labeled before staging.
- Never combine unidentified lots during receiving just to accelerate unloading.

## Material Handling Rules at Receiving
- Keep pallets stable before forklift movement. Re-wrap damaged loads immediately.
- Use a quarantine tag for any stock with unresolved quality or identity issues.
- Chilled and frozen goods should move first to controlled-temperature staging.
- High-value items should be counted in a supervised cage or controlled dock lane.
- Hazardous material receipts require compatibility review before any temporary staging decision.

## Exception Handling

### Short Delivery
1. Count again using a second operator or supervisor.
2. Confirm whether the shortage is line-level, pallet-level, or document-level.
3. GRN only the physical quantity received.
4. Record shortage details with supplier line references and photos if useful.

### Over Delivery
1. Verify whether extra units are approved tolerance, bonus quantity, or a supplier error.
2. Hold excess stock separately until procurement or warehouse leadership confirms disposition.
3. Do not silently receive excess stock into normal inventory without approval.

### Damaged Goods
1. Segregate damaged units immediately.
2. Record exact quantity and visible damage type.
3. Decide between reject-at-dock, accept-to-quarantine, or accept-with-claim based on policy.

### Unidentified or Mislabeled Goods
1. Stop the receipt line for that material.
2. Move material to quarantine or investigation area.
3. Contact masters or procurement to validate SKU identity before system posting.

### Temperature Excursion
1. Record actual product or trailer temperature.
2. Notify quality immediately if goods are outside policy range.
3. Hold stock in quality status until release decision is documented.

### Duplicate GRN Risk
1. Search existing receipts by supplier reference, ASN, PO, and vehicle date.
2. Confirm whether the inbound is a continuation, split unload, or duplicate entry.
3. Post only the net new quantity not already received.

## Quality Control Decision Tree
- Accept to stock: Product, quantity, traceability, and packaging are compliant.
- Accept to quarantine: Product is physically present but pending inspection or disposition.
- Reject at dock: Product is not acceptable and should not enter usable inventory.
- Accept with deviation: Use only when approved by quality or business owner with documented reason.

## Control Points and Audit Checks
- Receiver and checker should be different people on high-risk receipts.
- Use standard reason codes for short, over, damage, expiry, wrong item, and missing labels.
- Keep photo evidence for claims, severe damage, and temperature exceptions.
- Reconcile receiving logs against open dock appointments every shift.
- Review any PRE_PUTAWAY stock older than target dock-to-stock time.

## Inbound KPIs
- Dock-to-stock time
- Receipt accuracy percentage
- Supplier over or short percentage
- Damage-on-receipt percentage
- Receipt lines per labor hour
- Quarantine release lead time
- Putaway aging from GRN timestamp

## Consultant Improvement Techniques
- Use dock door zoning by supplier type or handling method to reduce congestion.
- Build a supplier scorecard around OTIF, ASN accuracy, damage rate, and labeling compliance.
- Apply Pareto analysis to identify the suppliers causing most receiving delays or claims.
- Use a recurring 5 Whys review for the top inbound discrepancies each week.
- Create standard pallet and carton labeling rules so inbound teams do not decode supplier-specific formats every day.
