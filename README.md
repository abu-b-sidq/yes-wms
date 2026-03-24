# Rozana WMS

Rozana WMS is a standalone Django + Django Ninja warehouse operations application rooted
in `app/` and exposed only through `/api/v1/`.

## Overview

The service owns:

- master data for organizations, facilities, zones, locations, and SKUs
- inventory balances and ledger visibility
- warehouse operations such as GRN, putaway, move, and order pick

Legacy proxy endpoints and secondary API version paths are not part of this application.

## Full Application Documentation

For complete technical documentation (architecture, route catalog, auth/tenant header
matrix, domain model, configuration, and operations), see:

- [`docs/application-documentation.md`](docs/application-documentation.md)

## Repository Layout

- `app/auth/`: authentication middleware and API-key helpers
- `app/core/`: shared middleware, logging, OpenAPI, tenant resolution, and responses
- `app/masters/`: master data models, services, routes, and migrations
- `app/operations/`: transaction models, services, routes, and migrations
- `app/inventory/`: inventory models, services, routes, and migrations
- `wms_middleware/`: Django settings, URL routing, ASGI, and WSGI entrypoints
- `tests/`: API, middleware, logging, schema, and domain tests
- `postman/`: shared Postman collections
- `k8s/uat/`: deployment manifests

## Public API

Public endpoints:

- `GET /api/v1/health`
- `GET /api/v1/swagger`
- `GET /api/v1/openapi.json`

Protected route groups:

- `/api/v1/masters/*`
- `/api/v1/operations/*`
- `/api/v1/inventory/*`

Representative endpoints:

- `POST /api/v1/masters/organizations`
- `GET /api/v1/masters/facilities`
- `PATCH /api/v1/masters/skus/{code}`
- `POST /api/v1/operations/grn`
- `POST /api/v1/operations/putaway`
- `POST /api/v1/operations/move`
- `POST /api/v1/operations/order-pick`
- `GET /api/v1/operations/transactions`
- `GET /api/v1/inventory/balances`
- `GET /api/v1/inventory/balances/by-location/{code}`
- `GET /api/v1/inventory/balances/by-sku/{code}`
- `GET /api/v1/inventory/ledger`

## Request Contract

Public routes such as health and docs do not require authentication.

Protected business routes use this contract:

- `warehouse`: required on every protected request
- `Authorization`: Firebase ID token, typically `Bearer <token>`
- `X-API-Key`: optional fallback when transitional auth fallback is enabled
- `X-Org-Id`: required for org-scoped business routes
- `X-Facility-Id`: required only for facility-scoped operations and queries

Example headers:

```http
warehouse: TEST_WH9
Authorization: Bearer <firebase-id-token>
X-Org-Id: testorg
X-Facility-Id: FAC-001
```

## Quick Start

1. Create and activate a virtual environment.
2. Install dependencies:

```bash
python3 -m pip install -r requirements.txt
```

3. Copy the environment template:

```bash
cp .env.example .env
```

4. Update `.env` with values for:

- `SECRET_KEY`
- `DEBUG`
- `DB_ENGINE`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`
- `FIREBASE_SERVICE_ACCOUNT_JSON` or `FIREBASE_SERVICE_ACCOUNT_PATH`
- `FIREBASE_PROJECT_ID`
- `AUTH_FALLBACK_ENABLED`
- `LEGACY_API_KEYS`
- `WAREHOUSE_CONFIG`
- `LOG_DESTINATION`

5. Apply the schema:

```bash
python3 manage.py migrate
```

6. Run the server:

```bash
python3 manage.py runserver 0.0.0.0:8000
```

7. Open the app locally:

- health: [http://localhost:8000/api/v1/health](http://localhost:8000/api/v1/health)
- swagger: [http://localhost:8000/api/v1/swagger](http://localhost:8000/api/v1/swagger)

## Docker

The repo includes `docker-compose.yml` for local startup:

```bash
docker compose up --build
```

Default local endpoints:

- [http://localhost:8010/api/v1/health](http://localhost:8010/api/v1/health)
- [http://localhost:8010/api/v1/swagger](http://localhost:8010/api/v1/swagger)

## Example Requests

Health:

```bash
curl -X GET "http://localhost:8010/api/v1/health"
```

Create an organization:

```bash
curl -X POST "http://localhost:8010/api/v1/masters/organizations" \
  -H "warehouse: TEST_WH9" \
  -H "X-API-Key: legacy-secret" \
  -H "Content-Type: application/json" \
  --data-raw '{
    "id": "testorg",
    "name": "Test Org"
  }'
```

Get balances:

```bash
curl -X GET "http://localhost:8010/api/v1/inventory/balances?sku_code=SKU-001" \
  -H "warehouse: TEST_WH9" \
  -H "X-Org-Id: testorg" \
  -H "X-Facility-Id: FAC-001" \
  -H "Authorization: Bearer <firebase-id-token>"
```

Move inventory:

```bash
curl -X POST "http://localhost:8010/api/v1/operations/move" \
  -H "warehouse: TEST_WH9" \
  -H "X-Org-Id: testorg" \
  -H "X-Facility-Id: FAC-001" \
  -H "Authorization: Bearer <firebase-id-token>" \
  -H "Content-Type: application/json" \
  --data-raw '{
    "sku_code": "SKU-001",
    "source_entity_code": "LOC-001",
    "dest_entity_code": "LOC-002",
    "quantity": 1
  }'
```

## Database

The standalone cutover uses a fresh schema bootstrap:

- Django app labels are `app_masters`, `app_operations`, and `app_inventory`
- database tables are named with the `app_*` prefix
- old `v2_*` migration continuity is intentionally not preserved

Treat new environments as clean bootstrap targets and recreate schema state through the
current initial migrations.

## Tests

Run the full suite with:

```bash
python3 -m pytest
```

Focused runs:

```bash
python3 -m pytest tests/domain
python3 -m pytest tests/test_api_routes.py tests/test_middleware_auth.py tests/test_openapi.py
```

## Logging

Structured logging is built into the standalone app.

- `LOG_DESTINATION=firehose` sends structured events to Firehose when configured
- `LOG_DESTINATION=file` writes logs to `LOG_FILE_PATH`
- `LOG_INCLUDE_PAYLOADS=true` enables payload capture with redaction
- `LOG_REDACT_KEYS` controls sensitive key redaction

Common event families:

- `api.request.completed`
- `api.request.exception`
- `api.error.response`

## Tooling

- The shared Postman collection lives at `postman/Rozana_WMS.postman_collection.json`
- Kubernetes probes should continue targeting `/api/v1/health`
- Future changes should extend the standalone `app/` package rather than reintroducing
  versioned packages or proxy flows
