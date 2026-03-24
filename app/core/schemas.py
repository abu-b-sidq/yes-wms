from __future__ import annotations

from typing import Any

from ninja import Schema


class PaginationParams(Schema):
    page: int = 1
    page_size: int = 50


class APIResponse(Schema):
    success: bool
    data: Any = None
    error: Any = None
    meta: dict[str, Any] | None = None


def api_success(data: Any, meta: dict[str, Any] | None = None) -> dict[str, Any]:
    return {
        "success": True,
        "data": data,
        "error": None,
        "meta": meta,
    }


def api_error(
    code: str,
    message: str,
    details: Any | None = None,
) -> dict[str, Any]:
    return {
        "success": False,
        "data": None,
        "error": {
            "code": code,
            "message": message,
            "details": details,
        },
    }


def paginated_response(
    items: list[Any],
    total: int,
    page: int,
    page_size: int,
) -> dict[str, Any]:
    return api_success(
        data=items,
        meta={
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size if page_size > 0 else 0,
        },
    )
