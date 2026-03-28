# AGENTS.md

This repository now targets a single standalone YES WMS application.
Use this file as the working guide for future cutover-safe changes.

## Mission

- Keep the application rooted in `app/`
- Expose only `/api/v1/`
- Preserve the warehouse operations domain in `masters`, `operations`, and `inventory`
- Avoid reintroducing version-toggle wiring, proxy flows, or parallel public API versions

## Important Paths

- `app/auth/`: auth middleware and helpers
- `app/core/`: shared middleware, logging, tenant resolution, OpenAPI, and responses
- `app/masters/`: master-data domain
- `app/operations/`: transaction domain
- `app/inventory/`: inventory domain
- `wms_middleware/`: Django settings and URL wiring
- `tests/domain/`: domain service and model behavior tests
- `tests/`: API, middleware, logging, and schema tests
- `postman/YES_WMS.postman_collection.json`: shared API collection
- `.env.example`: local runtime template

## Working Rules

- Do not create new package namespaces such as `v1` or `v2`
- Do not add a second public API base path or compatibility alias
- Do not add proxy-style routes for legacy upstream systems
- Keep protected routes aligned to `warehouse`, auth, `X-Org-Id`, and optional
  `X-Facility-Id` depending on route scope
- Prefer neutral internal names unless a release version is intentionally user-facing

## Preferred Commands

Install dependencies:

```bash
python3 -m pip install -r requirements.txt
```

Run migrations:

```bash
python3 manage.py migrate
```

Run the app:

```bash
python3 manage.py runserver 0.0.0.0:8000
```

Run tests:

```bash
python3 -m pytest
```

Run Docker locally:

```bash
docker compose up --build
```

## Documentation Expectations

- `README.md` should describe the current standalone app, not historical mixed routing
- Public docs and examples should reference `/api/v1` only
- Examples should use real repo artifacts such as `.env.example`, `manage.py`,
  `docker-compose.yml`, and `pytest.ini`
- Keep `AGENTS.md` as the canonical agent instructions file for this repo

## Decision Log

- The standalone application package is `app`
- The only public API base path is `/api/v1`
- `Authorization` and `X-API-Key` remain the supported protected-route auth mechanisms
- `warehouse` remains mandatory on protected routes
- `X-Org-Id` is required for org-scoped business routes
- `X-Facility-Id` is required only where a facility-scoped route needs it
- The schema reset is intentional: tables and app labels now use the `app_*` prefix
- Existing `v2_*` migration continuity is not preserved

## Working Notes

- Keep the repo moving toward simpler standalone behavior rather than transitional shims
- When you touch routing, middleware, or docs, make sure they stay aligned with the
  single-app architecture
