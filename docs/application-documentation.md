# Rozana WMS Application Documentation

## 1. Purpose and Scope

Rozana WMS is a standalone Django + Django Ninja application for warehouse management.

This documentation covers the current architecture implemented in this repository:

- the application package is `app`
- the only public API base path is `/api/v1`
- business domains are `masters`, `operations`, and `inventory`
- auth and tenancy are enforced by middleware and per-route tenant resolution

This guide intentionally excludes legacy routing, compatibility aliases, and proxy flows.

## 2. High-Level Architecture

### 2.1 Runtime Components

- `wms_middleware/`: Django project settings and URL entrypoint
- `app/api.py`: Ninja API instance and route registration
- `app/auth/`: dual-auth middleware and token/API-key verification
- `app/core/`: middleware, config, OpenAPI enrichment, response envelope, exceptions, logging
- `app/masters/`: org/facility/sku/zone/location and facility mapping overrides
- `app/operations/`: transactions, picks, drops, state transitions, convenience operations
- `app/inventory/`: balances and ledger persistence/query services

### 2.2 URL Wiring

All endpoints are mounted under `/api/v1/`:

- `wms_middleware/urls.py` mounts `path("api/v1/", api.urls)`
- no other public API prefixes are wired

### 2.3 Middleware Order (Request Pipeline)

Defined in `wms_middleware/settings.py`:

1. `SecurityMiddleware`
2. `CORSMiddleware`
3. `CommonMiddleware`
4. `RequestIDMiddleware`
5. `RequestLoggingMiddleware`
6. `DualAuthMiddleware`
7. `TenantContextMiddleware`

Practical effect:

- every API request gets a request ID
- request/response logging wraps auth and tenant checks
- protected routes require valid auth and `warehouse`
- tenant resolver then enforces org/facility requirements at route level

## 3. API Surface

### 3.1 Public Endpoints

- `GET /api/v1/health`
- `GET /api/v1/swagger`
- `GET /api/v1/openapi.json`

### 3.2 Masters Endpoints

Base path: `/api/v1/masters`

Organization (org header not required):

- `POST /organizations`
- `GET /organizations`
- `GET /organizations/{org_id}`
- `PATCH /organizations/{org_id}`

Facility:

- `POST /facilities`
- `GET /facilities`
- `GET /facilities/{code}`
- `PATCH /facilities/{code}`

Facility mapping overrides:

- `GET /facilities/{code}/skus`
- `PATCH /facilities/{code}/skus/{sku_code}`
- `GET /facilities/{code}/zones`
- `PATCH /facilities/{code}/zones/{zone_code}`
- `GET /facilities/{code}/locations`
- `PATCH /facilities/{code}/locations/{location_code}`

SKU:

- `POST /skus`
- `GET /skus`
- `GET /skus/{code}`
- `PATCH /skus/{code}`

Zone:

- `POST /zones`
- `GET /zones`
- `GET /zones/{code}`
- `PATCH /zones/{code}`

Location:

- `POST /locations`
- `GET /locations`
- `GET /locations/{code}`
- `PATCH /locations/{code}`

### 3.3 Operations Endpoints

Base path: `/api/v1/operations`

Transactions:

- `POST /transactions` (facility required)
- `GET /transactions` (facility optional filter)
- `GET /transactions/{txn_id}`
- `POST /transactions/{txn_id}/execute`
- `POST /transactions/{txn_id}/cancel`

Convenience operations (all facility required):

- `POST /move`
- `POST /grn`
- `POST /putaway`
- `POST /order-pick`

### 3.4 Inventory Endpoints

Base path: `/api/v1/inventory`

- `GET /balances` (facility optional filter)
- `GET /balances/by-location/{code}` (facility required)
- `GET /balances/by-sku/{code}` (facility required)
- `GET /ledger` (facility optional filter)
- `GET /ledger/by-transaction/{txn_id}` (facility optional)

## 4. Authentication and Tenant Contract

### 4.1 Authentication

Protected routes accept either:

- `Authorization: Bearer <firebase-id-token>` (or raw token string)
- `X-API-Key: <legacy-api-key>` when `AUTH_FALLBACK_ENABLED=true`

Behavior notes:

- if Firebase token is valid, request is authenticated as `firebase`
- if Firebase is missing/invalid and fallback is enabled, API key is attempted
- missing or invalid credentials return `401`

### 4.2 Warehouse Header

Protected routes require:

- `warehouse: <warehouse_key>`

When `WAREHOUSE_CONFIG` is populated, unknown warehouse keys are rejected with `TENANT_UNKNOWN_WAREHOUSE`.

### 4.3 Org/Facility Headers

Route-level tenant resolution rules:

- orgless protected routes: no `X-Org-Id` required (organization CRUD endpoints)
- org-scoped routes: `X-Org-Id` required
- facility-scoped routes: `X-Facility-Id` additionally required

### 4.4 Header Matrix

| Route scope | Required headers |
|---|---|
| Public (`/health`, `/swagger`, `/openapi.json`) | none |
| Protected orgless (organization endpoints) | `warehouse` + (`Authorization` or `X-API-Key`) |
| Protected org-scoped | `warehouse` + `X-Org-Id` + (`Authorization` or `X-API-Key`) |
| Protected facility-scoped | `warehouse` + `X-Org-Id` + `X-Facility-Id` + (`Authorization` or `X-API-Key`) |

## 5. Domain Model Summary

### 5.1 Masters Domain

Core entities:

- `Organization` (`app_organization`)
- `Facility` (`app_facility`)
- `SKU` (`app_sku`)
- `Zone` (`app_zone`)
- `Location` (`app_location`)

Facility mapping tables:

- `FacilitySKU` (`app_facility_sku`)
- `FacilityZone` (`app_facility_zone`)
- `FacilityLocation` (`app_facility_location`)

Important constraints:

- org+code uniqueness for facility/sku/zone/location
- mapping uniqueness per `(facility, mapped_entity)`

### 5.2 Operations Domain

Primary records:

- `Transaction` (`app_transaction`)
- `Pick` (`app_pick`)
- `Drop` (`app_drop`)

Supported transaction types include:

- `MOVE`, `ORDER_PICK`, `GRN`, `PUTAWAY`, `RETURN`, `CYCLE_COUNT`, `ADJUSTMENT`

Common statuses:

- `PENDING`, `IN_PROGRESS`, `COMPLETED`, `FAILED`, `CANCELLED`, `PARTIALLY_COMPLETED`

State machine highlights:

- execution transitions transaction from `PENDING` -> `IN_PROGRESS` -> `COMPLETED`
- invalid status transitions raise `INVALID_TRANSITION`

### 5.3 Inventory Domain

Primary records:

- `InventoryBalance` (`app_inventory_balance`)
- `InventoryLedger` (`app_inventory_ledger`)

Balance behavior:

- picks debit `quantity_on_hand` and `quantity_available`
- drops credit `quantity_on_hand` and `quantity_available`
- insufficient available quantity raises `INSUFFICIENT_INVENTORY`

Ledger behavior:

- each debit/credit writes a ledger entry (`PICK` or `DROP`)
- entries store `balance_after` and transaction linkage

## 6. Request/Response Conventions

### 6.1 Success Envelope

All successful API responses return:

```json
{
  "success": true,
  "data": {},
  "error": null,
  "meta": {
    "request_id": "...",
    "warehouse_key": "TEST_WH9",
    "org_id": "testorg",
    "facility_id": "FAC-001",
    "auth_source": "firebase"
  }
}
```

`meta` may additionally include `uid` (firebase) or `client_name` (API key fallback).

### 6.2 Error Envelope

All handled errors return:

```json
{
  "success": false,
  "data": null,
  "error": {
    "code": "TENANT_RESOLUTION_ERROR",
    "message": "Missing required `X-Org-Id` header.",
    "details": null
  },
  "meta": {
    "request_id": "..."
  }
}
```

Common error codes:

- `AUTH_MISSING_CREDENTIAL`
- `AUTH_FIREBASE_INVALID_TOKEN`
- `AUTH_FIREBASE_VERIFICATION_FAILED`
- `AUTH_API_KEY_INVALID`
- `TENANT_MISSING_WAREHOUSE`
- `TENANT_UNKNOWN_WAREHOUSE`
- `TENANT_RESOLUTION_ERROR`
- `ENTITY_NOT_FOUND`
- `VALIDATION_ERROR`
- `INSUFFICIENT_INVENTORY`
- `INVALID_TRANSITION`

## 7. Configuration Reference (`.env`)

### 7.1 Core Runtime

- `DEBUG`
- `SECRET_KEY`
- `ALLOWED_HOSTS`

### 7.2 CORS

- `CORS_ALLOWED_ORIGINS`
- `CORS_ALLOWED_ORIGIN_PATTERNS`
- `CORS_ALLOW_HEADERS`
- `CORS_PREFLIGHT_MAX_AGE`

### 7.3 Auth and Tenancy

- `FIREBASE_SERVICE_ACCOUNT_JSON` or `FIREBASE_SERVICE_ACCOUNT_PATH`
- `FIREBASE_PROJECT_ID`
- `AUTH_FALLBACK_ENABLED`
- `LEGACY_API_KEYS`
- `WAREHOUSE_CONFIG`

`LEGACY_API_KEYS` format:

```json
{"client_name":"api_key_value"}
```

### 7.4 Database

- `DB_ENGINE`
- `DB_NAME`
- `DB_USER`
- `DB_PASSWORD`
- `DB_HOST`
- `DB_PORT`

### 7.5 Logging

- `LOG_LEVEL`
- `LOG_DESTINATION` (`file` or `firehose`)
- `LOG_FORMAT` (`json` or `text`)
- `LOG_INCLUDE_PAYLOADS`
- `LOG_REDACT_KEYS`
- `LOG_FILE_PATH`
- `LOG_FILE_MAX_BYTES`
- `LOG_FILE_BACKUP_COUNT`

Firehose-specific:

- `FIREHOSE_DELIVERY_STREAM_NAME`
- `FIREHOSE_AWS_REGION`
- `FIREHOSE_BATCH_SIZE`
- `FIREHOSE_FLUSH_INTERVAL_SECONDS`
- `FIREHOSE_AWS_ACCESS_KEY_ID`
- `FIREHOSE_AWS_SECRET_ACCESS_KEY`

## 8. Local Development

### 8.1 Setup

```bash
python3 -m pip install -r requirements.txt
cp .env.example .env
python3 manage.py migrate
python3 manage.py runserver 0.0.0.0:8000
```

### 8.2 Key URLs

- Health: `http://localhost:8000/api/v1/health`
- Swagger: `http://localhost:8000/api/v1/swagger`
- OpenAPI JSON: `http://localhost:8000/api/v1/openapi.json`

### 8.3 Docker

```bash
docker compose up --build
```

Default mapped service URLs:

- `http://localhost:8010/api/v1/health`
- `http://localhost:8010/api/v1/swagger`

## 9. Testing

Run all tests:

```bash
python3 -m pytest
```

Focused test suites:

```bash
python3 -m pytest tests/test_api_routes.py tests/test_middleware_auth.py tests/test_openapi.py
python3 -m pytest tests/domain
```

What these validate:

- routing remains under `/api/v1`
- dual-auth behavior and public endpoint bypasses
- tenant and header requirements per route scope
- OpenAPI security/header contract
- domain behavior for masters/operations/inventory
- schema bootstrap tables use `app_*` naming

## 10. Operational Notes

- Health probes should target `/api/v1/health`
- OpenAPI docs are publicly readable at `/api/v1/openapi.json`
- Structured request/response events are emitted as `api.request.completed`, `api.request.exception`, and `api.error.response`
- New work should extend the existing standalone modules instead of introducing versioned API packages

## 11. Repository References

- Runtime entrypoint: `wms_middleware/urls.py`
- API assembly: `app/api.py`
- Auth middleware: `app/auth/middleware.py`
- Tenant middleware: `app/core/middleware.py`
- Tenant resolver: `app/core/tenant.py`
- Domain routes: `app/masters/routes.py`, `app/operations/routes.py`, `app/inventory/routes.py`
- Postman collection: `postman/Rozana_WMS.postman_collection.json`
- Agent guardrails: `AGENTS.md`
