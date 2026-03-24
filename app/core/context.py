from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class AuthContext:
    is_authenticated: bool = False
    auth_source: str | None = None
    uid: str | None = None
    client_name: str | None = None
    claims: dict[str, Any] = field(default_factory=dict)


@dataclass
class TenantContext:
    warehouse_key: str | None = None
    org_id: str | None = None
    facility_id: str | None = None
    warehouse_meta: dict[str, Any] = field(default_factory=dict)


def get_auth_context(request: Any) -> AuthContext:
    context = getattr(request, "auth_context", None)
    if context is None:
        return AuthContext()
    return context


def get_tenant_context(request: Any) -> TenantContext:
    context = getattr(request, "tenant_context", None)
    if context is None:
        return TenantContext()
    return context
