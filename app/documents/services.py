from __future__ import annotations

import logging
from datetime import datetime, timezone

from django.db import models
from django.template.loader import render_to_string

from app.core.config import get_runtime_settings

logger = logging.getLogger("app.documents")

# Default template per transaction type
_DEFAULT_TEMPLATES: dict[str, str] = {
    "GRN": "documents/grn.html",
    "PUTAWAY": "documents/putaway.html",
    "MOVE": "documents/move.html",
    "ORDER_PICK": "documents/order_pick.html",
}
_FALLBACK_TEMPLATE = "documents/default.html"


def get_document_config(org, facility, transaction_type: str) -> tuple[bool, str]:
    """
    Resolve whether document generation is enabled and which template to use.

    Resolution order (later overrides earlier):
      1. Global env flag (DOCUMENT_GENERATION_ENABLED)
      2. Org-level config (org=X, facility=None, transaction_type=None)
      3. Facility-level config (org=X, facility=Y, transaction_type=None)
      4. Type-level config for this org (org=X, facility=None, transaction_type=T)
      5. Type-level config for this facility (org=X, facility=Y, transaction_type=T)

    Returns:
        (is_enabled, template_name)
    """
    from app.documents.models import TransactionDocumentConfig

    settings = get_runtime_settings()
    is_enabled: bool = settings.document_generation_enabled
    template_name: str = _DEFAULT_TEMPLATES.get(transaction_type, _FALLBACK_TEMPLATE)

    # Fetch all matching configs in one query
    configs = list(
        TransactionDocumentConfig.objects.filter(
            models.Q(org=None, facility=None, transaction_type=None)
            | models.Q(org=org, facility=None, transaction_type=None)
            | models.Q(org=org, facility=facility, transaction_type=None)
            | models.Q(org=org, facility=None, transaction_type=transaction_type)
            | models.Q(org=org, facility=facility, transaction_type=transaction_type)
        )
    )

    # Apply configs from least to most specific
    specificity_order = [
        (False, False, False),  # global
        (True, False, False),   # org-level
        (True, True, False),    # facility-level
        (True, False, True),    # type-level (org)
        (True, True, True),     # type-level (facility) — most specific
    ]

    def _specificity_key(cfg: TransactionDocumentConfig) -> int:
        org_match = cfg.org_id is not None and cfg.org_id == org.pk
        fac_match = cfg.facility_id is not None and str(cfg.facility_id) == str(facility.pk)
        type_match = cfg.transaction_type == transaction_type

        for i, (om, fm, tm) in enumerate(specificity_order):
            if (
                (org_match if om else cfg.org_id is None)
                and (fac_match if fm else cfg.facility_id is None)
                and (type_match if tm else cfg.transaction_type is None)
            ):
                return i
        return -1

    for cfg in sorted(configs, key=_specificity_key):
        is_enabled = cfg.is_enabled
        if cfg.template_name:
            template_name = cfg.template_name

    return is_enabled, template_name


def render_document(transaction, template_name: str) -> str:
    """Render the transaction as an HTML string."""
    context = {
        "transaction": transaction,
        "org": transaction.org,
        "facility": transaction.facility,
        "generated_at": datetime.now(tz=timezone.utc),
    }
    return render_to_string(template_name, context)


def upload_to_firebase(html_content: str, path: str) -> str:
    """Upload HTML content to Firebase Storage and return the public URL."""
    import firebase_admin
    from firebase_admin import storage

    settings = get_runtime_settings()
    bucket = storage.bucket(
        app=firebase_admin.get_app(),
        name=settings.firebase_storage_bucket,
    )
    blob = bucket.blob(path)
    blob.upload_from_string(
        html_content.encode("utf-8"),
        content_type="text/html; charset=utf-8",
    )
    blob.make_public()
    return blob.public_url


def generate_and_store_document(transaction) -> str | None:
    """
    Orchestrate: check config → render → upload → return URL.
    Returns None if document generation is disabled or skipped.
    Does NOT raise — failures are logged and swallowed so the transaction is unaffected.
    """
    try:
        is_enabled, template_name = get_document_config(
            transaction.org,
            transaction.facility,
            transaction.transaction_type,
        )
        if not is_enabled:
            return None

        html = render_document(transaction, template_name)

        path = (
            f"documents/{transaction.org_id}/"
            f"{transaction.facility.code}/"
            f"{transaction.id}.html"
        )
        url = upload_to_firebase(html, path)
        logger.info(
            "Document generated for transaction %s: %s",
            transaction.id,
            url,
        )
        return url
    except Exception:
        logger.exception(
            "Document generation failed for transaction %s (non-fatal)",
            transaction.id,
        )
        return None
