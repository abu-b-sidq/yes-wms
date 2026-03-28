from ninja import NinjaAPI

from app.core.exceptions import AppError
from app.core.openapi import inject_security_schemes
from app.core.response import error_response, success_response
from app.inventory.routes import router as inventory_router
from app.masters.routes import router as masters_router
from app.operations.routes import router as operations_router


class StandaloneWMSAPI(NinjaAPI):
    def get_openapi_schema(self, *args, **kwargs):
        schema = super().get_openapi_schema(*args, **kwargs)
        return inject_security_schemes(schema)


api = StandaloneWMSAPI(
    title="YES WMS",
    version="2.0.0",
    urls_namespace="api",
    description=(
        "Standalone warehouse management system with master data, inventory visibility, "
        "and transaction execution.\n\n"
        "## Authentication\n\n"
        "All protected endpoints require the `warehouse` header. "
        "For org- and facility-scoped routes, this value must match a warehouse key stored on a facility record. "
        "Provide one of:\n"
        "- `Authorization: Bearer <firebase-id-token>` — primary auth\n"
        "- `X-API-Key: <key>` — legacy fallback for existing business routes (when enabled)\n\n"
        "Org-scoped routes require `X-Org-Id`. Facility-scoped routes also require `X-Facility-Id`.\n\n"
        "User-management routes under `/masters/me` and `/masters/users*` require Firebase auth and "
        "use application-side roles and org/facility memberships.\n\n"
        "## Response envelope\n\n"
        "All endpoints wrap their payload in a standard envelope:\n"
        "```json\n"
        "{\n"
        '  "success": true,\n'
        '  "data": { ... },\n'
        '  "error": null,\n'
        '  "meta": {\n'
        '    "request_id": "...",\n'
        '    "warehouse_key": "...",\n'
        '    "org_id": "...",\n'
        '    "facility_id": "...",\n'
        '    "auth_source": "firebase | api_key | none"\n'
        "  }\n"
        "}\n"
        "```\n\n"
        "## Document generation\n\n"
        "When configured (`TransactionDocumentConfig`), executing a transaction generates an HTML "
        "document and uploads it to Firebase Storage. The download URL is returned in "
        "`data.document_url` and persisted on the transaction."
    ),
    docs_url="/swagger",
    openapi_url="/openapi.json",
)


@api.exception_handler(AppError)
def app_error_handler(request, exc: AppError):
    return error_response(
        request,
        code=exc.code,
        message=exc.message,
        status_code=exc.status_code,
        details=exc.details,
    )


@api.get(
    "/health",
    tags=["system"],
    summary="Health check",
    description="Public liveness endpoint for the standalone warehouse application.",
)
def health(request):
    return success_response(
        request,
        data={
            "status": "ok",
            "service": "yes-wms",
            "version": "2.0.0",
        },
    )


api.add_router("/masters", masters_router)
api.add_router("/operations", operations_router)
api.add_router("/inventory", inventory_router)
