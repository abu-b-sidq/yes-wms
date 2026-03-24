from django.db import models


class TransactionType(models.TextChoices):
    MOVE = "MOVE", "Move"
    ORDER_PICK = "ORDER_PICK", "Order Pick"
    GRN = "GRN", "Goods Received Note"
    PUTAWAY = "PUTAWAY", "Putaway"
    RETURN = "RETURN", "Return"
    CYCLE_COUNT = "CYCLE_COUNT", "Cycle Count"
    ADJUSTMENT = "ADJUSTMENT", "Adjustment"


class TransactionStatus(models.TextChoices):
    PENDING = "PENDING", "Pending"
    IN_PROGRESS = "IN_PROGRESS", "In Progress"
    COMPLETED = "COMPLETED", "Completed"
    FAILED = "FAILED", "Failed"
    CANCELLED = "CANCELLED", "Cancelled"
    PARTIALLY_COMPLETED = "PARTIALLY_COMPLETED", "Partially Completed"


class EntityType(models.TextChoices):
    LOCATION = "LOCATION", "Location"
    ZONE = "ZONE", "Zone"
    INVOICE = "INVOICE", "Invoice"
    VIRTUAL_BUCKET = "VIRTUAL_BUCKET", "Virtual Bucket"
    SUPPLIER = "SUPPLIER", "Supplier"
    CUSTOMER = "CUSTOMER", "Customer"


class LedgerEntryType(models.TextChoices):
    PICK = "PICK", "Pick"
    DROP = "DROP", "Drop"
