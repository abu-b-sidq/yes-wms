from decimal import Decimal

from app.core.enums import EntityType, TransactionType
from app.core.exceptions import ValidationError


def validate_transaction_shape(transaction_type: str, picks: list, drops: list) -> None:
    """Validate that pick/drop shape matches the transaction type pattern."""
    if transaction_type == TransactionType.MOVE:
        if len(picks) < 1:
            raise ValidationError("MOVE transaction requires at least 1 pick.")
        if len(drops) < 1:
            raise ValidationError("MOVE transaction requires at least 1 drop.")
        if len(picks) != len(drops):
            raise ValidationError("MOVE transaction requires matching pick and drop counts.")

    elif transaction_type == TransactionType.ORDER_PICK:
        if len(picks) < 1:
            raise ValidationError("ORDER_PICK transaction requires at least 1 pick.")
        if len(drops) < 1:
            raise ValidationError("ORDER_PICK transaction requires at least 1 drop.")
        if len(picks) != len(drops):
            raise ValidationError("ORDER_PICK transaction requires matching pick and drop counts.")

    elif transaction_type == TransactionType.GRN:
        if len(drops) < 1:
            raise ValidationError("GRN transaction requires at least 1 drop.")

    elif transaction_type == TransactionType.PUTAWAY:
        if len(picks) < 1:
            raise ValidationError("PUTAWAY transaction requires at least 1 pick.")
        if len(drops) < 1:
            raise ValidationError("PUTAWAY transaction requires at least 1 drop.")
        if len(picks) != len(drops):
            raise ValidationError("PUTAWAY transaction requires matching pick and drop counts.")


def validate_pick_data(pick_data: dict) -> None:
    if Decimal(str(pick_data.get("quantity", 0))) <= 0:
        raise ValidationError("Pick quantity must be positive.")
    if not pick_data.get("source_entity_type"):
        raise ValidationError("Pick source_entity_type is required.")
    if not pick_data.get("source_entity_code"):
        raise ValidationError("Pick source_entity_code is required.")
    if pick_data["source_entity_type"] not in EntityType.values:
        raise ValidationError(
            f"Invalid source_entity_type: {pick_data['source_entity_type']}"
        )


def validate_drop_data(drop_data: dict) -> None:
    if Decimal(str(drop_data.get("quantity", 0))) <= 0:
        raise ValidationError("Drop quantity must be positive.")
    if not drop_data.get("dest_entity_type"):
        raise ValidationError("Drop dest_entity_type is required.")
    if not drop_data.get("dest_entity_code"):
        raise ValidationError("Drop dest_entity_code is required.")
    if drop_data["dest_entity_type"] not in EntityType.values:
        raise ValidationError(
            f"Invalid dest_entity_type: {drop_data['dest_entity_type']}"
        )
