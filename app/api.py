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
    title="Rozana WMS",
    version="2.0.0",
    urls_namespace="api",
    description=(
        "Standalone warehouse operations application with master data, inventory "
        "visibility, and transaction execution. Protected business APIs require "
        "`warehouse` plus either `Authorization` or `X-API-Key`; org-scoped routes "
        "use `X-Org-Id`, and facility-scoped routes use `X-Facility-Id`."
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
            "service": "rozana-wms",
            "version": "2.0.0",
        },
    )


api.add_router("/masters", masters_router)
api.add_router("/operations", operations_router)
api.add_router("/inventory", inventory_router)
