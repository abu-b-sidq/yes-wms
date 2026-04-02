from django.db import models


class ConnectorType(models.TextChoices):
    STOCKONE = "STOCKONE", "StockOne"
    SAP = "SAP", "SAP"
    ORACLE = "ORACLE", "Oracle"


class SyncEntityType(models.TextChoices):
    SKU = "SKU", "SKU"
    INVENTORY = "INVENTORY", "Inventory"
    ORDER = "ORDER", "Order"
    PURCHASE_ORDER = "PURCHASE_ORDER", "Purchase Order"
    SUPPLIER = "SUPPLIER", "Supplier"
    CUSTOMER = "CUSTOMER", "Customer"


class SyncStatus(models.TextChoices):
    PENDING = "PENDING", "Pending"
    RUNNING = "RUNNING", "Running"
    COMPLETED = "COMPLETED", "Completed"
    FAILED = "FAILED", "Failed"
