import io
import json
import logging

from app.core.logging_utils import JsonLogFormatter, redact_sensitive


def test_redact_sensitive_masks_nested_secret_keys():
    payload = {
        "headers": {
            "Authorization": "Bearer token-value",
            "X-API-Key": "legacy-secret",
        },
        "body": {
            "sku": "SKU-1",
            "client_secret": "secret-value",
            "nested": {
                "password": "secret-password",
                "quantity": 1,
            },
        },
    }

    redacted = redact_sensitive(payload)

    assert redacted["headers"]["Authorization"] == "***REDACTED***"
    assert redacted["headers"]["X-API-Key"] == "***REDACTED***"
    assert redacted["body"]["client_secret"] == "***REDACTED***"
    assert redacted["body"]["nested"]["password"] == "***REDACTED***"
    assert redacted["body"]["nested"]["quantity"] == 1


def test_json_log_formatter_outputs_json_and_redacts_sensitive_values():
    stream = io.StringIO()
    handler = logging.StreamHandler(stream)
    handler.setFormatter(JsonLogFormatter(service="test-service", environment="test"))

    logger = logging.getLogger("tests.logging")
    logger.handlers = [handler]
    logger.setLevel(logging.INFO)
    logger.propagate = False

    logger.info(
        "api.request.completed",
        extra={
            "event_name": "api.request.completed",
            "event_data": {
                "request_payload": {
                    "headers": {"Authorization": "Bearer test-token"},
                    "body": {"client_secret": "top-secret", "sku": "SKU-1"},
                }
            },
        },
    )

    line = stream.getvalue().strip()
    payload = json.loads(line)

    assert payload["event"] == "api.request.completed"
    assert payload["service"] == "test-service"
    assert payload["environment"] == "test"
    assert payload["request_payload"]["headers"]["Authorization"] == "***REDACTED***"
    assert payload["request_payload"]["body"]["client_secret"] == "***REDACTED***"
    assert payload["request_payload"]["body"]["sku"] == "SKU-1"
