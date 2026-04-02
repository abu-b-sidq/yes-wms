from __future__ import annotations

from app.core.exceptions import AppError


class ConnectorTransportError(AppError):
    code = "CONNECTOR_TRANSPORT_ERROR"
    status_code = 502
