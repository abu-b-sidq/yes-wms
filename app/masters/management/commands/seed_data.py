"""
Management command to seed realistic warehouse demo data.

Usage:
    python manage.py seed_data
    python manage.py seed_data --volume medium --date-from 2025-01-01 --date-to 2025-03-28
    python manage.py seed_data --org-id MY-ORG --clear
    python manage.py seed_data --dry-run
"""
from __future__ import annotations

import random
import secrets
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction as db_transaction

from app.core.enums import EntityType, TransactionStatus
from app.inventory.models import InventoryBalance, InventoryLedger
from app.masters.models import (
    Facility,
    FacilityLocation,
    FacilitySKU,
    FacilityZone,
    Location,
    Organization,
    SKU,
    Zone,
)
from app.masters.services import (
    create_facility,
    create_location,
    create_organization,
    create_sku,
    create_zone,
    get_facility,
    get_location,
    get_organization,
    get_sku,
    get_zone,
)
from app.operations.models import Drop, Pick, Transaction
from app.operations.services import (
    create_and_execute_grn,
    create_and_execute_move,
    create_and_execute_order_pick,
    create_and_execute_putaway,
    create_transaction,
)

# ---------------------------------------------------------------------------
# Static master data definitions
# ---------------------------------------------------------------------------

ORG_ID_DEFAULT = "YES-DEMO"
ORG_NAME = "YES Demo Warehouse Co."

FACILITY = {"code": "FAC-MAIN", "warehouse_key": "DEMO_WH1", "name": "Main Distribution Center", "address": "Plot 14, Industrial Zone, Dubai, UAE"}

ZONES = [
    {"code": "PRE_PUTAWAY", "name": "Pre-Putaway Staging"},
    {"code": "PHARMA",      "name": "Pharmacy Storage"},
    {"code": "FMCG",        "name": "FMCG Storage"},
    {"code": "COLD",        "name": "Cold Chain Storage"},
    {"code": "DRY",         "name": "Dry Goods Storage"},
    {"code": "DISPATCH",    "name": "Dispatch Staging"},
    {"code": "RETURNS",     "name": "Returns Zone"},
]

LOCATIONS = [
    # Pharma — 4 rack positions
    {"code": "PHARMA-A01", "name": "Pharma Rack A-01", "zone_code": "PHARMA", "capacity": 500},
    {"code": "PHARMA-A02", "name": "Pharma Rack A-02", "zone_code": "PHARMA", "capacity": 500},
    {"code": "PHARMA-A03", "name": "Pharma Rack A-03", "zone_code": "PHARMA", "capacity": 500},
    {"code": "PHARMA-A04", "name": "Pharma Rack A-04", "zone_code": "PHARMA", "capacity": 500},
    # FMCG — 6 bay positions
    {"code": "FMCG-B01",   "name": "FMCG Bay B-01",   "zone_code": "FMCG",   "capacity": 1000},
    {"code": "FMCG-B02",   "name": "FMCG Bay B-02",   "zone_code": "FMCG",   "capacity": 1000},
    {"code": "FMCG-B03",   "name": "FMCG Bay B-03",   "zone_code": "FMCG",   "capacity": 1000},
    {"code": "FMCG-B04",   "name": "FMCG Bay B-04",   "zone_code": "FMCG",   "capacity": 1000},
    {"code": "FMCG-B05",   "name": "FMCG Bay B-05",   "zone_code": "FMCG",   "capacity": 1000},
    {"code": "FMCG-B06",   "name": "FMCG Bay B-06",   "zone_code": "FMCG",   "capacity": 1000},
    # Cold chain — 4 cool-cell positions
    {"code": "COLD-C01",   "name": "Cold Cell C-01",   "zone_code": "COLD",   "capacity": 200},
    {"code": "COLD-C02",   "name": "Cold Cell C-02",   "zone_code": "COLD",   "capacity": 200},
    {"code": "COLD-C03",   "name": "Cold Cell C-03",   "zone_code": "COLD",   "capacity": 200},
    {"code": "COLD-C04",   "name": "Cold Cell C-04",   "zone_code": "COLD",   "capacity": 200},
    # Dry goods — 6 shelf positions
    {"code": "DRY-D01",    "name": "Dry Shelf D-01",   "zone_code": "DRY",    "capacity": 2000},
    {"code": "DRY-D02",    "name": "Dry Shelf D-02",   "zone_code": "DRY",    "capacity": 2000},
    {"code": "DRY-D03",    "name": "Dry Shelf D-03",   "zone_code": "DRY",    "capacity": 2000},
    {"code": "DRY-D04",    "name": "Dry Shelf D-04",   "zone_code": "DRY",    "capacity": 2000},
    {"code": "DRY-D05",    "name": "Dry Shelf D-05",   "zone_code": "DRY",    "capacity": 2000},
    {"code": "DRY-D06",    "name": "Dry Shelf D-06",   "zone_code": "DRY",    "capacity": 2000},
    # Dispatch + returns
    {"code": "DISP-E01",   "name": "Dispatch Lane E-01", "zone_code": "DISPATCH", "capacity": None},
    {"code": "DISP-E02",   "name": "Dispatch Lane E-02", "zone_code": "DISPATCH", "capacity": None},
    {"code": "RET-F01",    "name": "Returns Bay F-01",   "zone_code": "RETURNS",  "capacity": 300},
    {"code": "RET-F02",    "name": "Returns Bay F-02",   "zone_code": "RETURNS",  "capacity": 300},
]

# category → (sku_code, name, uom, zone_code, qty_range, use_batch)
SKUS: list[dict] = [
    # Pharma
    {"code": "PARA-500",    "name": "Paracetamol 500mg Tabs",       "unit_of_measure": "EA",  "category": "PHARMA", "qty_range": (20, 120),   "use_batch": True,  "metadata": {"temperature": "ambient", "schedule": "OTC"}},
    {"code": "AMOX-250",    "name": "Amoxicillin 250mg Caps",        "unit_of_measure": "EA",  "category": "PHARMA", "qty_range": (10, 80),    "use_batch": True,  "metadata": {"temperature": "ambient", "schedule": "Rx"}},
    {"code": "VITC-1000",   "name": "Vitamin C 1000mg Effervescent", "unit_of_measure": "EA",  "category": "PHARMA", "qty_range": (30, 200),   "use_batch": True,  "metadata": {"temperature": "ambient", "schedule": "OTC"}},
    {"code": "CETIRIZ-10",  "name": "Cetirizine 10mg Tabs",          "unit_of_measure": "EA",  "category": "PHARMA", "qty_range": (15, 100),   "use_batch": True,  "metadata": {"temperature": "ambient", "schedule": "OTC"}},
    {"code": "INS-RAPID",   "name": "Insulin Rapid-Acting 10ml",     "unit_of_measure": "EA",  "category": "PHARMA", "qty_range": (5,  40),    "use_batch": True,  "metadata": {"temperature": "refrigerated", "schedule": "Rx"}},
    # FMCG
    {"code": "COLA-330",    "name": "Cola Soft Drink 330ml Can",     "unit_of_measure": "EA",  "category": "FMCG",   "qty_range": (50, 300),   "use_batch": False, "metadata": {"brand": "SuperCola", "pack_size": 24}},
    {"code": "BISCUIT-PKT", "name": "Butter Biscuits 200g Pack",     "unit_of_measure": "EA",  "category": "FMCG",   "qty_range": (40, 250),   "use_batch": False, "metadata": {"brand": "CrunchMate", "pack_size": 12}},
    {"code": "SHAMPOO-200", "name": "Anti-Dandruff Shampoo 200ml",   "unit_of_measure": "EA",  "category": "FMCG",   "qty_range": (20, 150),   "use_batch": False, "metadata": {"brand": "FreshScalp"}},
    {"code": "DETERG-1KG",  "name": "Laundry Detergent Powder 1kg",  "unit_of_measure": "KG",  "category": "FMCG",   "qty_range": (30, 200),   "use_batch": False, "metadata": {"brand": "CleanPro", "scent": "lemon"}},
    {"code": "CHIPS-100",   "name": "Potato Chips 100g",             "unit_of_measure": "EA",  "category": "FMCG",   "qty_range": (50, 400),   "use_batch": False, "metadata": {"brand": "CrunchMax", "flavour": "salted"}},
    # Cold chain
    {"code": "MILK-1L",     "name": "Full-Cream Milk 1L",            "unit_of_measure": "EA",  "category": "COLD",   "qty_range": (20, 100),   "use_batch": True,  "metadata": {"temperature_max_c": 4}},
    {"code": "YOGURT-200",  "name": "Plain Yogurt 200g Cup",         "unit_of_measure": "EA",  "category": "COLD",   "qty_range": (30, 120),   "use_batch": True,  "metadata": {"temperature_max_c": 4}},
    {"code": "ICE-CREAM-500","name": "Vanilla Ice Cream 500ml",      "unit_of_measure": "EA",  "category": "COLD",   "qty_range": (10, 60),    "use_batch": True,  "metadata": {"temperature_max_c": -18}},
    {"code": "BUTTER-100",  "name": "Unsalted Butter 100g Block",    "unit_of_measure": "EA",  "category": "COLD",   "qty_range": (20, 80),    "use_batch": True,  "metadata": {"temperature_max_c": 4}},
    # Dry goods
    {"code": "RICE-5KG",    "name": "Basmati Rice 5kg Bag",          "unit_of_measure": "KG",  "category": "DRY",    "qty_range": (50, 500),   "use_batch": False, "metadata": {"origin": "Pakistan"}},
    {"code": "FLOUR-1KG",   "name": "All-Purpose Flour 1kg",         "unit_of_measure": "KG",  "category": "DRY",    "qty_range": (50, 400),   "use_batch": False, "metadata": {"origin": "UAE"}},
    {"code": "SUGAR-1KG",   "name": "Refined White Sugar 1kg",       "unit_of_measure": "KG",  "category": "DRY",    "qty_range": (50, 400),   "use_batch": False, "metadata": {"origin": "Brazil"}},
    {"code": "LENTIL-500",  "name": "Red Lentils 500g Pack",         "unit_of_measure": "KG",  "category": "DRY",    "qty_range": (30, 200),   "use_batch": False, "metadata": {}},
    {"code": "OIL-1L",      "name": "Sunflower Cooking Oil 1L",      "unit_of_measure": "EA",  "category": "DRY",    "qty_range": (30, 250),   "use_batch": False, "metadata": {"origin": "Ukraine"}},
    {"code": "SALT-500",    "name": "Iodised Table Salt 500g",       "unit_of_measure": "KG",  "category": "DRY",    "qty_range": (30, 200),   "use_batch": False, "metadata": {}},
]

# Map SKU category → preferred storage location codes
CATEGORY_LOCATIONS: dict[str, list[str]] = {
    "PHARMA": ["PHARMA-A01", "PHARMA-A02", "PHARMA-A03", "PHARMA-A04"],
    "FMCG":   ["FMCG-B01",  "FMCG-B02",  "FMCG-B03",  "FMCG-B04",  "FMCG-B05",  "FMCG-B06"],
    "COLD":   ["COLD-C01",  "COLD-C02",  "COLD-C03",  "COLD-C04"],
    "DRY":    ["DRY-D01",   "DRY-D02",   "DRY-D03",   "DRY-D04",   "DRY-D05",   "DRY-D06"],
}

VOLUME_CONFIG = {
    "light":  {"grns": (4, 7),   "putaways_per_grn": (2, 5),  "order_picks": (10, 20), "moves": (3, 7)},
    "medium": {"grns": (12, 18), "putaways_per_grn": (4, 8),  "order_picks": (40, 65), "moves": (10, 20)},
    "heavy":  {"grns": (40, 60), "putaways_per_grn": (8, 15), "order_picks": (120, 180), "moves": (40, 60)},
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _batch_number() -> str:
    return f"BCH-{secrets.token_hex(3).upper()}"


def _rand_dt(start: date, end: date) -> datetime:
    delta = (end - start).days
    offset_days = random.uniform(0, max(delta, 1))
    offset_hours = random.uniform(6, 20)  # business hours flavour
    dt = datetime(start.year, start.month, start.day, tzinfo=timezone.utc)
    dt = dt + timedelta(days=offset_days, hours=offset_hours)
    return dt


def _backdate(txn: Transaction, dt: datetime) -> None:
    Transaction.objects.filter(id=txn.id).update(
        created_at=dt,
        updated_at=dt,
        started_at=dt,
        completed_at=dt + timedelta(minutes=random.randint(1, 30)),
    )


def _get_or_create_org(org_id: str) -> tuple[Organization, bool]:
    try:
        return get_organization(org_id), False
    except Exception:
        return create_organization({"id": org_id, "name": ORG_NAME}), True


def _get_or_create_facility(org: Organization) -> tuple[Facility, bool]:
    try:
        return get_facility(org, FACILITY["code"]), False
    except Exception:
        return create_facility(org, FACILITY, user="seed"), True


def _get_or_create_zone(org: Organization, zone_data: dict) -> Zone:
    try:
        return get_zone(org, zone_data["code"])
    except Exception:
        return create_zone(org, zone_data, user="seed")


def _get_or_create_location(org: Organization, loc_data: dict) -> Location:
    try:
        return get_location(org, loc_data["code"])
    except Exception:
        return create_location(org, loc_data, user="seed")


def _get_or_create_sku(org: Organization, sku_data: dict) -> SKU:
    try:
        return get_sku(org, sku_data["code"])
    except Exception:
        payload = {k: v for k, v in sku_data.items() if k not in ("category", "qty_range", "use_batch")}
        return create_sku(org, payload, user="seed")


# ---------------------------------------------------------------------------
# Command
# ---------------------------------------------------------------------------

class Command(BaseCommand):
    help = "Seed realistic warehouse demo data (org, facility, SKUs, transactions)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--org-id",
            default=ORG_ID_DEFAULT,
            help=f"Organization ID to seed into (default: {ORG_ID_DEFAULT})",
        )
        parser.add_argument(
            "--volume",
            choices=["light", "medium", "heavy"],
            default="light",
            help="Transaction volume scale (default: light)",
        )
        parser.add_argument(
            "--date-from",
            default=None,
            help="Start date for backdated transactions, YYYY-MM-DD (default: 30 days ago)",
        )
        parser.add_argument(
            "--date-to",
            default=None,
            help="End date for backdated transactions, YYYY-MM-DD (default: today)",
        )
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Delete existing transactions and inventory for this org before seeding",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Print what would be created without touching the database",
        )

    def handle(self, *args, **options):
        org_id: str = options["org_id"]
        volume: str = options["volume"]
        dry_run: bool = options["dry_run"]
        clear: bool = options["clear"]

        # Parse date range
        today = date.today()
        try:
            date_from = date.fromisoformat(options["date_from"]) if options["date_from"] else today - timedelta(days=30)
            date_to   = date.fromisoformat(options["date_to"])   if options["date_to"]   else today
        except ValueError as exc:
            raise CommandError(f"Invalid date: {exc}") from exc

        if date_from > date_to:
            raise CommandError("--date-from must be before --date-to")

        vol = VOLUME_CONFIG[volume]
        n_grns        = random.randint(*vol["grns"])
        n_order_picks = random.randint(*vol["order_picks"])
        n_moves       = random.randint(*vol["moves"])

        self.stdout.write(self.style.MIGRATE_HEADING("\n=== YES WMS Seed Data ==="))
        self.stdout.write(f"  Org:         {org_id}")
        self.stdout.write(f"  Volume:      {volume}  (GRNs={n_grns}, order-picks={n_order_picks}, moves={n_moves})")
        self.stdout.write(f"  Date range:  {date_from} → {date_to}")
        if dry_run:
            self.stdout.write(self.style.WARNING("  DRY RUN — no database changes"))
        self.stdout.write("")

        if dry_run:
            self._dry_run_summary(n_grns, vol, n_order_picks, n_moves)
            return

        with db_transaction.atomic():
            self._run(org_id, volume, vol, date_from, date_to, n_grns, n_order_picks, n_moves, clear)

    # ------------------------------------------------------------------

    def _dry_run_summary(self, n_grns, vol, n_order_picks, n_moves):
        n_putaways_min = n_grns * vol["putaways_per_grn"][0]
        n_putaways_max = n_grns * vol["putaways_per_grn"][1]
        self.stdout.write("Would create:")
        self.stdout.write(f"  • 1 organization, 1 facility")
        self.stdout.write(f"  • {len(ZONES)} zones, {len(LOCATIONS)} locations, {len(SKUS)} SKUs")
        self.stdout.write(f"  • {n_grns} GRN transactions")
        self.stdout.write(f"  • {n_putaways_min}–{n_putaways_max} putaway transactions")
        self.stdout.write(f"  • {n_order_picks} order-pick transactions")
        self.stdout.write(f"  • {n_moves} inventory move transactions")

    def _run(self, org_id, volume, vol, date_from, date_to, n_grns, n_order_picks, n_moves, clear):
        # ---- Masters ----
        self.stdout.write(self.style.MIGRATE_HEADING("1/5  Setting up master data…"))
        org, org_created = _get_or_create_org(org_id)
        self.stdout.write(f"     Org: {org.id} ({'created' if org_created else 'existing'})")

        facility, fac_created = _get_or_create_facility(org)
        self.stdout.write(f"     Facility: {facility.code} ({'created' if fac_created else 'existing'})")

        for z in ZONES:
            _get_or_create_zone(org, z)
        self.stdout.write(f"     Zones: {len(ZONES)} ready")

        for loc in LOCATIONS:
            _get_or_create_location(org, loc)
        self.stdout.write(f"     Locations: {len(LOCATIONS)} ready")

        skus_map: dict[str, dict] = {}
        for s in SKUS:
            _get_or_create_sku(org, s)
            skus_map[s["code"]] = s
        self.stdout.write(f"     SKUs: {len(SKUS)} ready")

        # ---- Clear ----
        if clear:
            self.stdout.write(self.style.WARNING("     Clearing existing transactions & inventory…"))
            Drop.objects.filter(org=org).delete()
            Pick.objects.filter(org=org).delete()
            InventoryLedger.objects.filter(org=org).delete()
            InventoryBalance.objects.filter(org=org).delete()
            Transaction.objects.filter(org=org).delete()

        # ---- In-memory inventory tracker ----
        # { (sku_code, location_code, batch): Decimal }
        inventory: dict[tuple[str, str, str], Decimal] = {}

        def _add_inv(sku_code, loc_code, batch, qty):
            key = (sku_code, loc_code, batch)
            inventory[key] = inventory.get(key, Decimal("0")) + qty

        def _consume_inv(sku_code, loc_code, batch, qty) -> bool:
            key = (sku_code, loc_code, batch)
            if inventory.get(key, Decimal("0")) >= qty:
                inventory[key] -= qty
                return True
            return False

        # ---- GRNs ----
        self.stdout.write(self.style.MIGRATE_HEADING("2/5  Creating GRNs…"))
        grn_records = []  # list of (txn, [{sku_code, batch, qty}])

        grn_dts = sorted(_rand_dt(date_from, date_to) for _ in range(n_grns))

        for i, dt in enumerate(grn_dts):
            ref = f"PO-{random.randint(10000, 99999)}"
            # Pick a random subset of SKUs for this GRN (2–6 items)
            batch_skus = random.sample(SKUS, k=random.randint(2, min(6, len(SKUS))))
            items = []
            item_meta = []
            for s in batch_skus:
                qty = Decimal(str(random.randint(*s["qty_range"])))
                batch = _batch_number() if s["use_batch"] else ""
                items.append({"sku_code": s["code"], "quantity": qty, "batch_number": batch})
                item_meta.append({"sku_code": s["code"], "qty": qty, "batch": batch})

            txn = create_and_execute_grn(
                org, facility,
                {"items": items, "reference_number": ref, "notes": f"Supplier delivery {ref}"},
                user="seed",
            )
            _backdate(txn, dt)
            grn_records.append((txn, item_meta))
            self.stdout.write(f"     GRN {i+1}/{n_grns}: {ref}  ({len(items)} lines)", ending="\r")

        self.stdout.write(f"     {n_grns} GRNs done                          ")

        # ---- Putaways ----
        self.stdout.write(self.style.MIGRATE_HEADING("3/5  Putaway from staging to locations…"))
        n_putaways = 0
        putaway_dts = iter(sorted(
            _rand_dt(date_from, date_to)
            for _ in range(n_grns * vol["putaways_per_grn"][1])
        ))

        for _txn, item_metas in grn_records:
            # Putaway randint(putaways_per_grn) items from this GRN
            n_to_putaway = random.randint(*vol["putaways_per_grn"])
            chosen = random.sample(item_metas, k=min(n_to_putaway, len(item_metas)))
            for meta in chosen:
                sku_code = meta["sku_code"]
                qty      = meta["qty"]
                batch    = meta["batch"]
                category = skus_map[sku_code]["category"]
                dest_loc = random.choice(CATEGORY_LOCATIONS[category])

                try:
                    dt = next(putaway_dts)
                except StopIteration:
                    dt = _rand_dt(date_from, date_to)

                txn = create_and_execute_putaway(
                    org, facility,
                    {
                        "sku_code": sku_code,
                        "dest_entity_code": dest_loc,
                        "quantity": qty,
                        "batch_number": batch,
                        "reference_number": f"PUT-{random.randint(1000, 9999)}",
                    },
                    user="seed",
                )
                _backdate(txn, dt)
                _add_inv(sku_code, dest_loc, batch, qty)
                n_putaways += 1

        self.stdout.write(f"     {n_putaways} putaway transactions done")

        # ---- Order Picks ----
        self.stdout.write(self.style.MIGRATE_HEADING("4/5  Simulating order picks…"))
        # Build a list of available inventory tuples we can pick from
        available_items = [
            (sku_code, loc_code, batch, qty)
            for (sku_code, loc_code, batch), qty in inventory.items()
            if qty > 0
        ]

        pick_dts = iter(sorted(_rand_dt(date_from, date_to) for _ in range(n_order_picks)))
        n_picked = 0
        order_counter = random.randint(1000, 5000)

        for _ in range(n_order_picks):
            if not available_items:
                break
            sku_code, loc_code, batch, avail = random.choice(available_items)
            if avail <= 0:
                continue
            pick_qty = Decimal(str(random.randint(1, max(1, int(avail // 2)))))
            if not _consume_inv(sku_code, loc_code, batch, pick_qty):
                continue

            order_counter += random.randint(1, 5)
            order_ref = f"ORD-{order_counter}"
            try:
                dt = next(pick_dts)
            except StopIteration:
                dt = _rand_dt(date_from, date_to)

            txn = create_and_execute_order_pick(
                org, facility,
                {
                    "sku_code": sku_code,
                    "source_entity_code": loc_code,
                    "dest_entity_code": order_ref,
                    "quantity": pick_qty,
                    "batch_number": batch,
                    "reference_number": order_ref,
                    "notes": f"Fulfilment for {order_ref}",
                },
                user="seed",
            )
            _backdate(txn, dt)
            n_picked += 1

            # Refresh available items list
            available_items = [
                (sc, lc, b, qty)
                for (sc, lc, b), qty in inventory.items()
                if qty > 0
            ]

        self.stdout.write(f"     {n_picked} order picks done")

        # ---- Moves ----
        self.stdout.write(self.style.MIGRATE_HEADING("5/5  Simulating inventory moves (consolidation)…"))
        move_dts = iter(sorted(_rand_dt(date_from, date_to) for _ in range(n_moves)))
        n_moved = 0

        available_items = [
            (sku_code, loc_code, batch, qty)
            for (sku_code, loc_code, batch), qty in inventory.items()
            if qty > 0
        ]

        for _ in range(n_moves):
            if not available_items:
                break
            sku_code, src_loc, batch, avail = random.choice(available_items)
            if avail <= 0:
                continue

            category = skus_map[sku_code]["category"]
            # Pick a different location in the same category zone
            candidate_locs = [l for l in CATEGORY_LOCATIONS[category] if l != src_loc]
            if not candidate_locs:
                continue
            dest_loc = random.choice(candidate_locs)
            move_qty = Decimal(str(random.randint(1, max(1, int(avail // 3)))))

            if not _consume_inv(sku_code, src_loc, batch, move_qty):
                continue

            try:
                dt = next(move_dts)
            except StopIteration:
                dt = _rand_dt(date_from, date_to)

            txn = create_and_execute_move(
                org, facility,
                {
                    "sku_code": sku_code,
                    "source_entity_code": src_loc,
                    "dest_entity_code": dest_loc,
                    "quantity": move_qty,
                    "batch_number": batch,
                    "reference_number": f"MOV-{random.randint(100, 999)}",
                    "notes": "Stock consolidation",
                },
                user="seed",
            )
            _backdate(txn, dt)
            _add_inv(sku_code, dest_loc, batch, move_qty)
            n_moved += 1

            available_items = [
                (sc, lc, b, qty)
                for (sc, lc, b), qty in inventory.items()
                if qty > 0
            ]

        self.stdout.write(f"     {n_moved} moves done")

        # ---- Leave a few transactions in non-completed states ----
        self._seed_pending_and_cancelled(org, facility, skus_map, date_from, date_to)

        # ---- Summary ----
        self._print_summary(org, facility)

    def _seed_pending_and_cancelled(self, org, facility, skus_map, date_from, date_to):
        """Create 1 PENDING GRN and 1 CANCELLED GRN for realism."""
        from app.operations.services import create_transaction, cancel_transaction

        # Pending GRN (received but not yet executed)
        pending_sku = random.choice(SKUS)
        qty = Decimal(str(random.randint(*pending_sku["qty_range"])))
        batch = _batch_number() if pending_sku["use_batch"] else ""
        ref = f"PO-PENDING-{random.randint(100, 999)}"
        txn_data = {
            "transaction_type": "GRN",
            "reference_number": ref,
            "notes": "Awaiting quality check",
            "picks": [],
            "drops": [
                {
                    "sku_code": pending_sku["code"],
                    "dest_entity_type": EntityType.ZONE,
                    "dest_entity_code": "PRE_PUTAWAY",
                    "quantity": qty,
                    "batch_number": batch,
                }
            ],
        }
        pending_txn = create_transaction(org, facility, txn_data, user="seed")
        dt = _rand_dt(date_from, date_to)
        Transaction.objects.filter(id=pending_txn.id).update(created_at=dt, updated_at=dt)

        # Cancelled GRN
        cancel_sku = random.choice(SKUS)
        qty2 = Decimal(str(random.randint(*cancel_sku["qty_range"])))
        batch2 = _batch_number() if cancel_sku["use_batch"] else ""
        ref2 = f"PO-CANCEL-{random.randint(100, 999)}"
        txn_data2 = {
            "transaction_type": "GRN",
            "reference_number": ref2,
            "notes": "Supplier order cancelled",
            "picks": [],
            "drops": [
                {
                    "sku_code": cancel_sku["code"],
                    "dest_entity_type": EntityType.ZONE,
                    "dest_entity_code": "PRE_PUTAWAY",
                    "quantity": qty2,
                    "batch_number": batch2,
                }
            ],
        }
        cancel_txn = create_transaction(org, facility, txn_data2, user="seed")
        cancel_transaction(cancel_txn)
        dt2 = _rand_dt(date_from, date_to)
        Transaction.objects.filter(id=cancel_txn.id).update(created_at=dt2, updated_at=dt2, cancelled_at=dt2)

    def _print_summary(self, org, facility):
        from app.inventory.models import InventoryBalance
        from app.operations.models import Transaction

        txn_counts = {}
        for txn in Transaction.objects.filter(org=org, facility=facility):
            key = f"{txn.transaction_type}/{txn.status}"
            txn_counts[key] = txn_counts.get(key, 0) + 1

        balance_count = InventoryBalance.objects.filter(org=org, facility=facility).count()
        skus_with_stock = (
            InventoryBalance.objects.filter(org=org, facility=facility, quantity_on_hand__gt=0)
            .values("sku__code")
            .distinct()
            .count()
        )

        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("=== Seed complete ==="))
        self.stdout.write(f"  Transactions:")
        for key, cnt in sorted(txn_counts.items()):
            self.stdout.write(f"    {key:<35} {cnt:>4}")
        self.stdout.write(f"  Inventory balance rows: {balance_count}")
        self.stdout.write(f"  SKUs with stock:        {skus_with_stock}")
        self.stdout.write("")
        self.stdout.write(f"  Verify with MCP:")
        self.stdout.write(f"    wms_list_organizations()")
        self.stdout.write(f"    wms_get_inventory_balances(org_id=\"{org.id}\", facility_id=\"{FACILITY['code']}\")")
        self.stdout.write(f"    wms_list_transactions(org_id=\"{org.id}\")")
        self.stdout.write("")
