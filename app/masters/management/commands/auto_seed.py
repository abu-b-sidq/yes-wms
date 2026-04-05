"""
Management command to continuously seed realistic warehouse demo data on an interval.

Keeps running until stopped (Ctrl+C), generating new transactions each cycle.
Master data (org, facility, zones, locations, SKUs) is created once and reused.
Existing warehouse data is preserved unless --clear is used.

Usage:
    python manage.py auto_seed
    python manage.py auto_seed --org-id YES-DEMO --volume medium --interval 10
    python manage.py auto_seed --org-id YES-DEMO --max-iterations 5 --interval 2
    python manage.py auto_seed --org-id YES-DEMO --clear --volume heavy
"""
from __future__ import annotations

import random
import secrets
import signal
import time
from datetime import date, datetime, timezone
from decimal import Decimal

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction as db_transaction

from app.core.enums import EntityType
from app.inventory.models import InventoryBalance, InventoryLedger
from app.masters.models import (
    AppUser,
    AppUserStatus,
    Facility,
    Location,
    MembershipStatus,
    Organization,
    Role,
    SKU,
    UserOrgMembership,
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
)

# ---------------------------------------------------------------------------
# Static master data definitions (shared with seed_data.py)
# ---------------------------------------------------------------------------

ORG_ID_DEFAULT = "YES-DEMO"
ORG_NAME = "YES Demo Warehouse Co."

FACILITY = {
    "code": "FAC-MAIN",
    "warehouse_key": "DEMO_WH1",
    "name": "Main Distribution Center",
    "address": "Plot 14, Industrial Zone, Dubai, UAE",
}

ZONES = [
    {"code": "PRE_PUTAWAY", "name": "Pre-Putaway Staging"},
    {"code": "PHARMA", "name": "Pharmacy Storage"},
    {"code": "FMCG", "name": "FMCG Storage"},
    {"code": "COLD", "name": "Cold Chain Storage"},
    {"code": "DRY", "name": "Dry Goods Storage"},
    {"code": "DISPATCH", "name": "Dispatch Staging"},
    {"code": "RETURNS", "name": "Returns Zone"},
]

LOCATIONS = [
    # Pharma — 4 rack positions
    {"code": "PHARMA-A01", "name": "Pharma Rack A-01", "zone_code": "PHARMA", "capacity": 500},
    {"code": "PHARMA-A02", "name": "Pharma Rack A-02", "zone_code": "PHARMA", "capacity": 500},
    {"code": "PHARMA-A03", "name": "Pharma Rack A-03", "zone_code": "PHARMA", "capacity": 500},
    {"code": "PHARMA-A04", "name": "Pharma Rack A-04", "zone_code": "PHARMA", "capacity": 500},
    # FMCG — 6 bay positions
    {"code": "FMCG-B01", "name": "FMCG Bay B-01", "zone_code": "FMCG", "capacity": 1000},
    {"code": "FMCG-B02", "name": "FMCG Bay B-02", "zone_code": "FMCG", "capacity": 1000},
    {"code": "FMCG-B03", "name": "FMCG Bay B-03", "zone_code": "FMCG", "capacity": 1000},
    {"code": "FMCG-B04", "name": "FMCG Bay B-04", "zone_code": "FMCG", "capacity": 1000},
    {"code": "FMCG-B05", "name": "FMCG Bay B-05", "zone_code": "FMCG", "capacity": 1000},
    {"code": "FMCG-B06", "name": "FMCG Bay B-06", "zone_code": "FMCG", "capacity": 1000},
    # Cold chain — 4 cool-cell positions
    {"code": "COLD-C01", "name": "Cold Cell C-01", "zone_code": "COLD", "capacity": 200},
    {"code": "COLD-C02", "name": "Cold Cell C-02", "zone_code": "COLD", "capacity": 200},
    {"code": "COLD-C03", "name": "Cold Cell C-03", "zone_code": "COLD", "capacity": 200},
    {"code": "COLD-C04", "name": "Cold Cell C-04", "zone_code": "COLD", "capacity": 200},
    # Dry goods — 6 shelf positions
    {"code": "DRY-D01", "name": "Dry Shelf D-01", "zone_code": "DRY", "capacity": 2000},
    {"code": "DRY-D02", "name": "Dry Shelf D-02", "zone_code": "DRY", "capacity": 2000},
    {"code": "DRY-D03", "name": "Dry Shelf D-03", "zone_code": "DRY", "capacity": 2000},
    {"code": "DRY-D04", "name": "Dry Shelf D-04", "zone_code": "DRY", "capacity": 2000},
    {"code": "DRY-D05", "name": "Dry Shelf D-05", "zone_code": "DRY", "capacity": 2000},
    {"code": "DRY-D06", "name": "Dry Shelf D-06", "zone_code": "DRY", "capacity": 2000},
    # Dispatch + returns
    {"code": "DISP-E01", "name": "Dispatch Lane E-01", "zone_code": "DISPATCH", "capacity": None},
    {"code": "DISP-E02", "name": "Dispatch Lane E-02", "zone_code": "DISPATCH", "capacity": None},
    {"code": "RET-F01", "name": "Returns Bay F-01", "zone_code": "RETURNS", "capacity": 300},
    {"code": "RET-F02", "name": "Returns Bay F-02", "zone_code": "RETURNS", "capacity": 300},
]

SKUS = [
    # Pharma
    {"code": "PARA-500", "name": "Paracetamol 500mg Tabs", "unit_of_measure": "EA", "category": "PHARMA", "qty_range": (20, 120), "use_batch": True, "metadata": {"temperature": "ambient", "schedule": "OTC"}},
    {"code": "AMOX-250", "name": "Amoxicillin 250mg Caps", "unit_of_measure": "EA", "category": "PHARMA", "qty_range": (10, 80), "use_batch": True, "metadata": {"temperature": "ambient", "schedule": "Rx"}},
    {"code": "VITC-1000", "name": "Vitamin C 1000mg Effervescent", "unit_of_measure": "EA", "category": "PHARMA", "qty_range": (30, 200), "use_batch": True, "metadata": {"temperature": "ambient", "schedule": "OTC"}},
    {"code": "CETIRIZ-10", "name": "Cetirizine 10mg Tabs", "unit_of_measure": "EA", "category": "PHARMA", "qty_range": (15, 100), "use_batch": True, "metadata": {"temperature": "ambient", "schedule": "OTC"}},
    {"code": "INS-RAPID", "name": "Insulin Rapid-Acting 10ml", "unit_of_measure": "EA", "category": "PHARMA", "qty_range": (5, 40), "use_batch": True, "metadata": {"temperature": "refrigerated", "schedule": "Rx"}},
    # FMCG
    {"code": "COLA-330", "name": "Cola Soft Drink 330ml Can", "unit_of_measure": "EA", "category": "FMCG", "qty_range": (50, 300), "use_batch": False, "metadata": {"brand": "SuperCola", "pack_size": 24}},
    {"code": "BISCUIT-PKT", "name": "Butter Biscuits 200g Pack", "unit_of_measure": "EA", "category": "FMCG", "qty_range": (40, 250), "use_batch": False, "metadata": {"brand": "CrunchMate", "pack_size": 12}},
    {"code": "SHAMPOO-200", "name": "Anti-Dandruff Shampoo 200ml", "unit_of_measure": "EA", "category": "FMCG", "qty_range": (20, 150), "use_batch": False, "metadata": {"brand": "FreshScalp"}},
    {"code": "DETERG-1KG", "name": "Laundry Detergent Powder 1kg", "unit_of_measure": "KG", "category": "FMCG", "qty_range": (30, 200), "use_batch": False, "metadata": {"brand": "CleanPro", "scent": "lemon"}},
    {"code": "CHIPS-100", "name": "Potato Chips 100g", "unit_of_measure": "EA", "category": "FMCG", "qty_range": (50, 400), "use_batch": False, "metadata": {"brand": "CrunchMax", "flavour": "salted"}},
    # Cold chain
    {"code": "MILK-1L", "name": "Full-Cream Milk 1L", "unit_of_measure": "EA", "category": "COLD", "qty_range": (20, 100), "use_batch": True, "metadata": {"temperature_max_c": 4}},
    {"code": "YOGURT-200", "name": "Plain Yogurt 200g Cup", "unit_of_measure": "EA", "category": "COLD", "qty_range": (30, 120), "use_batch": True, "metadata": {"temperature_max_c": 4}},
    {"code": "ICE-CREAM-500", "name": "Vanilla Ice Cream 500ml", "unit_of_measure": "EA", "category": "COLD", "qty_range": (10, 60), "use_batch": True, "metadata": {"temperature_max_c": -18}},
    {"code": "BUTTER-100", "name": "Unsalted Butter 100g Block", "unit_of_measure": "EA", "category": "COLD", "qty_range": (20, 80), "use_batch": True, "metadata": {"temperature_max_c": 4}},
    # Dry goods
    {"code": "RICE-5KG", "name": "Basmati Rice 5kg Bag", "unit_of_measure": "KG", "category": "DRY", "qty_range": (50, 500), "use_batch": False, "metadata": {"origin": "Pakistan"}},
    {"code": "FLOUR-1KG", "name": "All-Purpose Flour 1kg", "unit_of_measure": "KG", "category": "DRY", "qty_range": (50, 400), "use_batch": False, "metadata": {"origin": "UAE"}},
    {"code": "SUGAR-1KG", "name": "Refined White Sugar 1kg", "unit_of_measure": "KG", "category": "DRY", "qty_range": (50, 400), "use_batch": False, "metadata": {"origin": "Brazil"}},
    {"code": "LENTIL-500", "name": "Red Lentils 500g Pack", "unit_of_measure": "KG", "category": "DRY", "qty_range": (30, 200), "use_batch": False, "metadata": {}},
    {"code": "OIL-1L", "name": "Sunflower Cooking Oil 1L", "unit_of_measure": "EA", "category": "DRY", "qty_range": (30, 250), "use_batch": False, "metadata": {"origin": "Ukraine"}},
    {"code": "SALT-500", "name": "Iodised Table Salt 500g", "unit_of_measure": "KG", "category": "DRY", "qty_range": (30, 200), "use_batch": False, "metadata": {}},
]

CATEGORY_LOCATIONS = {
    "PHARMA": ["PHARMA-A01", "PHARMA-A02", "PHARMA-A03", "PHARMA-A04"],
    "FMCG": ["FMCG-B01", "FMCG-B02", "FMCG-B03", "FMCG-B04", "FMCG-B05", "FMCG-B06"],
    "COLD": ["COLD-C01", "COLD-C02", "COLD-C03", "COLD-C04"],
    "DRY": ["DRY-D01", "DRY-D02", "DRY-D03", "DRY-D04", "DRY-D05", "DRY-D06"],
}

VOLUME_CONFIG = {
    "light": {"grns": (4, 7), "putaways_per_grn": (2, 5), "order_picks": (10, 20), "moves": (3, 7)},
    "medium": {"grns": (12, 18), "putaways_per_grn": (4, 8), "order_picks": (40, 65), "moves": (10, 20)},
    "heavy": {"grns": (40, 60), "putaways_per_grn": (8, 15), "order_picks": (120, 180), "moves": (40, 60)},
}

# Demo users (no real Firebase account — firebase_uid used as created_by/performed_by key)
USERS = [
    {
        "firebase_uid": "seed-user-admin",
        "email": "admin@yes-demo.com",
        "display_name": "Admin User",
        "role_code": "org_admin",
        "status": AppUserStatus.ACTIVE,
    },
    {
        "firebase_uid": "seed-user-manager",
        "email": "manager@yes-demo.com",
        "display_name": "Facility Manager",
        "role_code": "facility_manager",
        "status": AppUserStatus.ACTIVE,
    },
    {
        "firebase_uid": "seed-user-operator1",
        "email": "operator1@yes-demo.com",
        "display_name": "Warehouse Operator 1",
        "role_code": "operator",
        "status": AppUserStatus.ACTIVE,
    },
    {
        "firebase_uid": "seed-user-operator2",
        "email": "operator2@yes-demo.com",
        "display_name": "Warehouse Operator 2",
        "role_code": "operator",
        "status": AppUserStatus.ACTIVE,
    },
    {
        "firebase_uid": "seed-user-viewer",
        "email": "viewer@yes-demo.com",
        "display_name": "Read-Only Viewer",
        "role_code": "viewer",
        "status": AppUserStatus.ACTIVE,
    },
]

# User IDs (firebase_uids) that perform warehouse operations — used to vary created_by/performed_by
OPERATOR_UIDS = ["seed-user-manager", "seed-user-operator1", "seed-user-operator2"]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _batch_number() -> str:
    return f"BCH-{secrets.token_hex(3).upper()}"


def _get_or_create_org(org_id: str) -> tuple[Organization, bool]:
    try:
        return get_organization(org_id), False
    except Exception:
        return create_organization({"id": org_id, "name": ORG_NAME}), True


def _get_or_create_facility(org: Organization) -> tuple[Facility, bool]:
    try:
        return get_facility(org, FACILITY["code"]), False
    except Exception:
        return create_facility(org, FACILITY, user="auto_seed"), True


def _get_or_create_zone(org: Organization, zone_data: dict) -> Zone:
    try:
        return get_zone(org, zone_data["code"])
    except Exception:
        return create_zone(org, zone_data, user="auto_seed")


def _get_or_create_location(org: Organization, loc_data: dict) -> Location:
    try:
        return get_location(org, loc_data["code"])
    except Exception:
        return create_location(org, loc_data, user="auto_seed")


def _get_or_create_sku(org: Organization, sku_data: dict) -> SKU:
    try:
        return get_sku(org, sku_data["code"])
    except Exception:
        payload = {k: v for k, v in sku_data.items() if k not in ("category", "qty_range", "use_batch")}
        return create_sku(org, payload, user="auto_seed")


def _seed_users(org: Organization) -> list[AppUser]:
    """Create demo AppUsers and attach them to the org with appropriate roles."""
    seeded = []
    for u in USERS:
        user, _ = AppUser.objects.get_or_create(
            firebase_uid=u["firebase_uid"],
            defaults={
                "email": u["email"],
                "display_name": u["display_name"],
                "status": u["status"],
            },
        )
        user.status = u["status"]
        user.display_name = u["display_name"]
        user.save(update_fields=["status", "display_name"])

        try:
            role = Role.objects.get(code=u["role_code"])
        except Role.DoesNotExist:
            seeded.append(user)
            continue

        UserOrgMembership.objects.get_or_create(
            user=user,
            org=org,
            defaults={"role": role, "status": MembershipStatus.ACTIVE},
        )
        seeded.append(user)
    return seeded


# ---------------------------------------------------------------------------
# Command
# ---------------------------------------------------------------------------


class Command(BaseCommand):
    help = "Continuously seed realistic warehouse transactions at regular intervals."

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._stop_requested = False

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
            help="Transaction volume per cycle (default: light)",
        )
        parser.add_argument(
            "--interval",
            type=int,
            default=10,
            help="Seconds to wait between seed cycles (default: 10)",
        )
        parser.add_argument(
            "--max-iterations",
            type=int,
            default=None,
            help="Maximum number of seed cycles before stopping (default: infinite until Ctrl+C)",
        )
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Clear existing transactions and inventory before starting (WARNING: destructive)",
        )

    def handle(self, *args, **options):
        org_id = options["org_id"]
        volume = options["volume"]
        interval = options["interval"]
        max_iterations = options["max_iterations"]
        clear = options["clear"]

        # Validate interval
        if interval < 1:
            raise CommandError("--interval must be at least 1 second")

        self.stdout.write(self.style.MIGRATE_HEADING("\n=== Auto Seed Warehouse Data ==="))
        self.stdout.write(f"  Org:           {org_id}")
        self.stdout.write(f"  Volume:        {volume}")
        self.stdout.write(f"  Interval:      {interval}s")
        if max_iterations:
            self.stdout.write(f"  Max iterations: {max_iterations}")
        else:
            self.stdout.write(f"  Max iterations: ∞ (until Ctrl+C)")
        self.stdout.write(f"  Clear:         {'YES (data will be deleted!)' if clear else 'NO (preserving existing data)'}")
        self.stdout.write("")

        # Setup signal handler for graceful shutdown
        def _signal_handler(signum, frame):
            self._stop_requested = True
            self.stdout.write(self.style.WARNING("\nShutdown requested…"))

        signal.signal(signal.SIGINT, _signal_handler)

        # One-time master data setup
        self.stdout.write(self.style.MIGRATE_HEADING("Setting up master data…"))
        org, facility, skus_map = self._setup_master_data(org_id, clear)
        self.stdout.write(self.style.SUCCESS(f"Master data ready: {org.id}, {facility.code}\n"))

        # Main loop
        iteration = 0
        total_counts = {"grns": 0, "putaways": 0, "picks": 0, "moves": 0}

        try:
            while True:
                iteration += 1

                if max_iterations and iteration > max_iterations:
                    break

                if self._stop_requested:
                    break

                self.stdout.write(self.style.MIGRATE_HEADING(f"[Iteration {iteration}] Seeding transactions…"))

                try:
                    counts = self._seed_iteration(org, facility, skus_map, volume)
                    total_counts["grns"] += counts["grns"]
                    total_counts["putaways"] += counts["putaways"]
                    total_counts["picks"] += counts["picks"]
                    total_counts["moves"] += counts["moves"]

                    self.stdout.write(
                        f"  ✓ GRNs: {counts['grns']}, Putaways: {counts['putaways']}, "
                        f"Picks: {counts['picks']}, Moves: {counts['moves']}"
                    )
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"  ✗ Error during seeding: {e}"))
                    # Continue to next iteration instead of crashing

                if max_iterations and iteration >= max_iterations:
                    break

                if self._stop_requested:
                    break

                self.stdout.write(f"  Waiting {interval}s until next cycle (Ctrl+C to stop)…\n")
                time.sleep(interval)

        except KeyboardInterrupt:
            self._stop_requested = True

        # Print summary
        self._print_summary(org, facility, iteration, total_counts)

    def _setup_master_data(self, org_id: str, clear: bool) -> tuple[Organization, Facility, dict]:
        """Setup org, facility, zones, locations, SKUs. Returns (org, facility, skus_map)."""
        org, org_created = _get_or_create_org(org_id)
        self.stdout.write(f"  Org: {org.id} ({'created' if org_created else 'existing'})")

        facility, fac_created = _get_or_create_facility(org)
        self.stdout.write(f"  Facility: {facility.code} ({'created' if fac_created else 'existing'})")

        seeded_users = _seed_users(org)
        self.stdout.write(f"  Users: {len(seeded_users)} ready")

        for z in ZONES:
            _get_or_create_zone(org, z)
        self.stdout.write(f"  Zones: {len(ZONES)} ready")

        for loc in LOCATIONS:
            _get_or_create_location(org, loc)
        self.stdout.write(f"  Locations: {len(LOCATIONS)} ready")

        skus_map = {}
        for s in SKUS:
            _get_or_create_sku(org, s)
            skus_map[s["code"]] = s
        self.stdout.write(f"  SKUs: {len(SKUS)} ready")

        # Clear if requested
        if clear:
            self.stdout.write(self.style.WARNING("  Clearing existing transactions & inventory…"))
            Drop.objects.filter(org=org).delete()
            Pick.objects.filter(org=org).delete()
            InventoryLedger.objects.filter(org=org).delete()
            InventoryBalance.objects.filter(org=org).delete()
            Transaction.objects.filter(org=org).delete()

        return org, facility, skus_map

    def _seed_iteration(self, org: Organization, facility: Facility, skus_map: dict, volume: str) -> dict:
        """Generate one cycle of transactions. Returns counts."""
        vol = VOLUME_CONFIG[volume]
        n_grns = random.randint(*vol["grns"])
        n_order_picks = random.randint(*vol["order_picks"])
        n_moves = random.randint(*vol["moves"])

        counts = self._generate_transactions(org, facility, skus_map, vol, n_grns, n_order_picks, n_moves)
        return counts

    def _generate_transactions(
        self,
        org: Organization,
        facility: Facility,
        skus_map: dict,
        vol: dict,
        n_grns: int,
        n_order_picks: int,
        n_moves: int,
    ) -> dict:
        """Generate GRNs, putaways, order picks, and moves. Returns transaction counts."""
        with db_transaction.atomic():
            # In-memory inventory tracker: {(sku_code, location_code, batch): Decimal}
            inventory = {}

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
            n_putaways_generated = 0
            grn_records = []

            for _ in range(n_grns):
                ref = f"PO-{random.randint(10000, 99999)}"
                batch_skus = random.sample(SKUS, k=random.randint(2, min(6, len(SKUS))))
                items = []
                item_meta = []

                for s in batch_skus:
                    qty = Decimal(str(random.randint(*s["qty_range"])))
                    batch = _batch_number() if s["use_batch"] else ""
                    items.append({"sku_code": s["code"], "quantity": qty, "batch_number": batch})
                    item_meta.append({"sku_code": s["code"], "qty": qty, "batch": batch})

                txn = create_and_execute_grn(
                    org,
                    facility,
                    {"items": items, "reference_number": ref, "notes": f"Auto-seed delivery {ref}"},
                    user=random.choice(OPERATOR_UIDS),
                )
                grn_records.append((txn, item_meta))

            # ---- Putaways ----
            for _txn, item_metas in grn_records:
                n_to_putaway = random.randint(*vol["putaways_per_grn"])
                chosen = random.sample(item_metas, k=min(n_to_putaway, len(item_metas)))

                for meta in chosen:
                    sku_code = meta["sku_code"]
                    qty = meta["qty"]
                    batch = meta["batch"]
                    category = skus_map[sku_code]["category"]
                    dest_loc = random.choice(CATEGORY_LOCATIONS[category])

                    txn = create_and_execute_putaway(
                        org,
                        facility,
                        {
                            "sku_code": sku_code,
                            "dest_entity_code": dest_loc,
                            "quantity": qty,
                            "batch_number": batch,
                            "reference_number": f"PUT-{random.randint(1000, 9999)}",
                        },
                        user=random.choice(OPERATOR_UIDS),
                    )
                    _add_inv(sku_code, dest_loc, batch, qty)
                    n_putaways_generated += 1

            # ---- Order Picks ----
            available_items = [
                (sku_code, loc_code, batch, qty)
                for (sku_code, loc_code, batch), qty in inventory.items()
                if qty > 0
            ]

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

                txn = create_and_execute_order_pick(
                    org,
                    facility,
                    {
                        "sku_code": sku_code,
                        "source_entity_code": loc_code,
                        "dest_entity_code": order_ref,
                        "quantity": pick_qty,
                        "batch_number": batch,
                        "reference_number": order_ref,
                        "notes": f"Auto-seed fulfilment for {order_ref}",
                    },
                    user=random.choice(OPERATOR_UIDS),
                )
                n_picked += 1

                # Refresh available items
                available_items = [
                    (sc, lc, b, qty)
                    for (sc, lc, b), qty in inventory.items()
                    if qty > 0
                ]

            # ---- Moves ----
            available_items = [
                (sku_code, loc_code, batch, qty)
                for (sku_code, loc_code, batch), qty in inventory.items()
                if qty > 0
            ]

            n_moved = 0

            for _ in range(n_moves):
                if not available_items:
                    break
                sku_code, src_loc, batch, avail = random.choice(available_items)
                if avail <= 0:
                    continue

                category = skus_map[sku_code]["category"]
                candidate_locs = [l for l in CATEGORY_LOCATIONS[category] if l != src_loc]
                if not candidate_locs:
                    continue
                dest_loc = random.choice(candidate_locs)
                move_qty = Decimal(str(random.randint(1, max(1, int(avail // 3)))))

                if not _consume_inv(sku_code, src_loc, batch, move_qty):
                    continue

                txn = create_and_execute_move(
                    org,
                    facility,
                    {
                        "sku_code": sku_code,
                        "source_entity_code": src_loc,
                        "dest_entity_code": dest_loc,
                        "quantity": move_qty,
                        "batch_number": batch,
                        "reference_number": f"MOV-{random.randint(100, 999)}",
                        "notes": "Auto-seed stock consolidation",
                    },
                    user=random.choice(OPERATOR_UIDS),
                )
                _add_inv(sku_code, dest_loc, batch, move_qty)
                n_moved += 1

                available_items = [
                    (sc, lc, b, qty)
                    for (sc, lc, b), qty in inventory.items()
                    if qty > 0
                ]

            return {
                "grns": len(grn_records),
                "putaways": n_putaways_generated,
                "picks": n_picked,
                "moves": n_moved,
            }

    def _print_summary(self, org: Organization, facility: Facility, iterations: int, total_counts: dict):
        """Print final summary before exit."""
        from app.inventory.models import InventoryBalance
        from app.operations.models import Transaction

        self.stdout.write("\n")
        self.stdout.write(self.style.SUCCESS("=== Auto Seed Complete ==="))
        self.stdout.write(f"  Iterations completed: {iterations}")
        self.stdout.write(f"  Total transactions generated:")
        self.stdout.write(f"    GRNs:     {total_counts['grns']}")
        self.stdout.write(f"    Putaways: {total_counts['putaways']}")
        self.stdout.write(f"    Picks:    {total_counts['picks']}")
        self.stdout.write(f"    Moves:    {total_counts['moves']}")

        txn_count = Transaction.objects.filter(org=org, facility=facility).count()
        balance_count = InventoryBalance.objects.filter(org=org, facility=facility).count()
        skus_with_stock = (
            InventoryBalance.objects.filter(org=org, facility=facility, quantity_on_hand__gt=0)
            .values("sku__code")
            .distinct()
            .count()
        )

        self.stdout.write(f"  Current warehouse state:")
        self.stdout.write(f"    Total transactions: {txn_count}")
        self.stdout.write(f"    Inventory balances: {balance_count}")
        self.stdout.write(f"    SKUs with stock:    {skus_with_stock}")
        self.stdout.write("")
        self.stdout.write(f"  Verify with MCP:")
        self.stdout.write(f"    wms_list_transactions(org_id=\"{org.id}\")")
        self.stdout.write(f"    wms_get_inventory_balances(org_id=\"{org.id}\", facility_id=\"{facility.code}\")")
        self.stdout.write("")
