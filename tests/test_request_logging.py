import json
import logging

from django.http import JsonResponse
from django.test import RequestFactory

from app.core.middleware import RequestLoggingMiddleware
from app.core.response import error_response


def _records_with_event(caplog, logger_name: str, event_name: str):
    return [
        record
        for record in caplog.records
        if record.name == logger_name and getattr(record, "event_name", None) == event_name
    ]


def _enable_caplog_for_app_loggers(monkeypatch) -> None:
    app_logger = logging.getLogger("app")
    app_request_logger = logging.getLogger("app.request")
    app_response_logger = logging.getLogger("app.response")

    monkeypatch.setattr(app_logger, "handlers", [])
    monkeypatch.setattr(app_logger, "propagate", True)
    monkeypatch.setattr(app_request_logger, "handlers", [])
    monkeypatch.setattr(app_request_logger, "propagate", True)
    monkeypatch.setattr(app_response_logger, "handlers", [])
    monkeypatch.setattr(app_response_logger, "propagate", True)


def test_request_logging_emits_completed_event_for_success(caplog, monkeypatch):
    _enable_caplog_for_app_loggers(monkeypatch)
    caplog.set_level(logging.INFO, logger="app.request")

    request = RequestFactory().get("/api/v1/health")
    request.request_id = "req-123"

    def get_response(_request):
        return JsonResponse({"success": True, "data": {"status": "ok"}})

    middleware = RequestLoggingMiddleware(get_response)
    response = middleware(request)

    assert response.status_code == 200

    completed = _records_with_event(caplog, "app.request", "api.request.completed")
    assert completed
    event_data = completed[-1].event_data

    assert event_data["request_id"] == "req-123"
    assert event_data["http"]["method"] == "GET"
    assert event_data["http"]["path"] == "/api/v1/health"
    assert event_data["http"]["status_code"] == 200

    response_body = event_data["response_payload"]["body"]
    assert response_body["success"] is True
    assert response_body["data"]["status"] == "ok"


def test_request_logging_and_error_response_event_for_unauthorized(caplog, monkeypatch):
    _enable_caplog_for_app_loggers(monkeypatch)
    caplog.set_level(logging.INFO, logger="app.request")
    caplog.set_level(logging.WARNING, logger="app.response")

    request = RequestFactory().get("/api/v1/inventory/balances")
    request.request_id = "req-401"

    def get_response(req):
        return error_response(
            req,
            code="AUTH_MISSING_CREDENTIAL",
            message="Missing Authorization header or valid fallback X-API-Key.",
            status_code=401,
        )

    middleware = RequestLoggingMiddleware(get_response)
    response = middleware(request)

    assert response.status_code == 401
    body = json.loads(response.content.decode("utf-8"))
    assert body["error"]["code"] == "AUTH_MISSING_CREDENTIAL"

    completed = _records_with_event(caplog, "app.request", "api.request.completed")
    assert completed
    assert completed[-1].event_data["http"]["status_code"] == 401

    errors = _records_with_event(caplog, "app.response", "api.error.response")
    assert errors
    assert errors[-1].event_data["error"]["code"] == "AUTH_MISSING_CREDENTIAL"


def test_request_logging_ignores_non_api_paths(caplog, monkeypatch):
    _enable_caplog_for_app_loggers(monkeypatch)
    caplog.set_level(logging.INFO, logger="app.request")

    request = RequestFactory().get("/health")
    request.request_id = "req-non-api"

    middleware = RequestLoggingMiddleware(lambda _request: JsonResponse({"success": True}))
    response = middleware(request)

    assert response.status_code == 200
    completed = _records_with_event(caplog, "app.request", "api.request.completed")
    assert completed == []
