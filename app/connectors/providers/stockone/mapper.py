"""Map StockOne API responses → YES WMS service input dicts.

Each function takes a single raw StockOne record (dict) and returns a dict
that can be passed directly to the corresponding YES WMS service function.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any


# ------------------------------------------------------------------
# Products → SKU
# ------------------------------------------------------------------

def map_product_to_sku(record: dict[str, Any]) -> dict[str, Any]:
    """Map a StockOne product record to a YES WMS SKU create/update dict.

    Target: masters.services.create_sku(org, data) / update_sku(org, code, data)
    SKU fields: code, name, is_active, unit_of_measure, metadata
    """
    return {
        "code": record["sku_code"],
        "name": record.get("sku_desc") or record["sku_code"],
        "is_active": bool(record.get("active", 1)),
        "unit_of_measure": record.get("measurement_type") or "EA",
        "metadata": {
            "source": "stockone",
            "stockone_id": record.get("id"),
            "sku_brand": record.get("sku_brand", ""),
            "sku_category": record.get("sku_category", ""),
            "sub_category": record.get("sub_category", ""),
            "sku_class": record.get("sku_class", ""),
            "sku_type": record.get("sku_type", ""),
            "sku_size": record.get("sku_size", ""),
            "hsn_code": record.get("hsn_code", ""),
            "ean_number": record.get("ean_number", ""),
            "price": record.get("price"),
            "mrp": record.get("mrp"),
            "cost_price": record.get("cost_price"),
            "batch_based": record.get("batch_based", False),
            "image_url": record.get("image_url", ""),
            "threshold_quantity": record.get("threshold_quantity", 0),
            "product_shelf_life": record.get("product_shelf_life"),
            "customer_shelf_life": record.get("customer_shelf_life"),
        },
    }


def get_product_external_id(record: dict[str, Any]) -> str:
    return str(record["sku_code"])


# ------------------------------------------------------------------
# Inventory → InventoryBalance upsert data
# ------------------------------------------------------------------

def map_inventory_to_balance(record: dict[str, Any]) -> dict[str, Any]:
    """Map a StockOne inventory record to InventoryBalance upsert fields.

    StockOne inventory structure:
      sku, sku_desc, sku_uom, available_quantity, reserved_quantity,
      total_quantity, open_order_quantity, batch_details[...]

    We sync the aggregate (non-batch) level.  Batch details are stored
    in metadata for reference.
    """
    return {
        "sku_code": record["sku"],
        "quantity_on_hand": Decimal(str(record.get("total_quantity", 0))),
        "quantity_reserved": Decimal(str(record.get("reserved_quantity", 0))),
        "quantity_available": Decimal(str(record.get("available_quantity", 0))),
        "metadata": {
            "source": "stockone",
            "open_order_quantity": record.get("open_order_quantity", 0),
            "batch_details": record.get("batch_details", []),
        },
    }


def get_inventory_external_id(record: dict[str, Any]) -> str:
    return str(record["sku"])


# ------------------------------------------------------------------
# Orders → Transaction (ORDER_PICK) input
# ------------------------------------------------------------------

def map_order_to_transaction(record: dict[str, Any]) -> dict[str, Any]:
    """Map a StockOne order record to YES WMS transaction creation input.

    StockOne order structure:
      order_id, customer_po_number, order_type, items[{sku_code,
      order_quantity, picked_quantity, dispatched_quantity, ...}]
    """
    items = []
    for item in record.get("items", []):
        items.append({
            "sku_code": item.get("sku_code", ""),
            "quantity": Decimal(str(item.get("order_quantity", 0))),
            "picked_quantity": Decimal(str(item.get("picked_quantity", 0))),
            "dispatched_quantity": Decimal(str(item.get("dispatched_quantity", 0))),
            "status": item.get("status", ""),
            "unit_price": item.get("unit_price", 0),
            "line_reference": item.get("line_reference", ""),
        })

    return {
        "external_order_id": record.get("order_id", ""),
        "order_reference": record.get("customer_po_number", ""),
        "order_type": record.get("order_type", ""),
        "items": items,
        "metadata": {
            "source": "stockone",
        },
    }


def get_order_external_id(record: dict[str, Any]) -> str:
    return str(record.get("order_id", ""))


# ------------------------------------------------------------------
# Purchase Orders → Transaction (GRN) input
# ------------------------------------------------------------------

def map_purchase_order_to_transaction(record: dict[str, Any]) -> dict[str, Any]:
    """Map a StockOne PO record to YES WMS transaction creation input."""
    items = []
    for item in record.get("items", []):
        items.append({
            "sku_code": item.get("sku_code", ""),
            "quantity": Decimal(str(item.get("quantity", 0))),
            "received_quantity": Decimal(str(item.get("received_quantity", 0))),
            "receivable_quantity": Decimal(str(item.get("receivable_quantity", 0))),
            "price": item.get("price", 0),
            "mrp": item.get("mrp", 0),
        })

    return {
        "po_number": record.get("po_number", ""),
        "po_reference": record.get("po_reference", ""),
        "po_type": record.get("po_type", ""),
        "supplier_id": record.get("supplier_id", ""),
        "supplier_name": record.get("supplier_name", ""),
        "warehouse": record.get("warehouse", ""),
        "items": items,
        "metadata": {
            "source": "stockone",
            "po_date": record.get("po_date", ""),
            "total_order_quantity": record.get("total_order_quantity"),
        },
    }


def get_purchase_order_external_id(record: dict[str, Any]) -> str:
    return str(record.get("po_number", "") or record.get("po_reference", ""))


# ------------------------------------------------------------------
# Suppliers
# ------------------------------------------------------------------

def map_supplier(record: dict[str, Any]) -> dict[str, Any]:
    return {
        "supplier_id": record.get("supplier_id", ""),
        "name": record.get("name", ""),
        "supplier_reference": record.get("supplier_reference", ""),
        "address": record.get("address", ""),
        "city": record.get("city", ""),
        "state": record.get("state", ""),
        "country": record.get("country", ""),
        "pincode": record.get("pincode", ""),
        "phone_number": record.get("phone_number", ""),
        "email_id": record.get("email_id", ""),
        "supplier_type": record.get("supplier_type", ""),
        "metadata": {"source": "stockone", "stockone_id": record.get("id")},
    }


def get_supplier_external_id(record: dict[str, Any]) -> str:
    return str(record.get("supplier_id", "") or record.get("id", ""))


# ------------------------------------------------------------------
# Customers
# ------------------------------------------------------------------

def map_customer(record: dict[str, Any]) -> dict[str, Any]:
    return {
        "customer_reference": record.get("customer_reference", ""),
        "name": record.get("name", ""),
        "phone_number": record.get("phone_number", ""),
        "city": record.get("city", ""),
        "state": record.get("state", ""),
        "address": record.get("address", ""),
        "shipping_address": record.get("shipping_address", ""),
        "metadata": {"source": "stockone"},
    }


def get_customer_external_id(record: dict[str, Any]) -> str:
    return str(record.get("customer_reference", ""))
