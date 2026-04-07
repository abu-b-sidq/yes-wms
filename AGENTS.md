# AGENTS.md

This repository is the full YES WMS workspace. The system of record is still the
Django + Django Ninja backend rooted in `app/`, but the repo also includes the
React assistant, Angular ops dashboard, Expo mobile client, connector sync
workers, MCP server, and realtime notifications. Use this file as the working
guide for changes that need to stay aligned with the current architecture.

## Mission

- Keep warehouse business logic rooted in `app/`
- Keep the only public HTTP API family under `/api/v1/`
- Preserve the warehouse core in `masters`, `operations`, and `inventory`
- Preserve existing supporting surfaces: `/api/v1/mobile`, `/api/v1/ai`,
  `/api/v1/connectors`, `/mcp`, `/.well-known`, and `/ws/tasks/`
- Prefer small explicit changes over new abstractions
- If a requested design looks brittle or overengineered, propose a simpler
  alternative before building it
- Do not import inside functions

## Architecture Snapshot

- `wms_middleware/asgi.py` multiplexes Django HTTP, Starlette MCP, and WebSocket
  traffic
- `app/api.py` mounts the `masters`, `operations`, `inventory`, `mobile`, `ai`,
  and `connectors` routers
- `app/auth/` and `app/core/` enforce Firebase-first auth, legacy API-key
  fallback, tenant headers, logging, OpenAPI, and the standard response envelope
- `app/operations/` handles transactions, pick/drop task flows, state machines,
  and worker gamification
- `app/inventory/` owns balances, ledger writes, and inventory queries
- `app/documents/` renders transaction HTML documents and can upload them to
  Firebase Storage
- `app/connectors/` manages external sync through Celery, Redis, `SyncLog`, and
  provider mappers
- `app/ai/` stores conversations/messages/embeddings, streams SSE chat, and
  executes tool calls
- `app/notifications/` provides device-token storage and realtime task
  notifications
- `app/mcp/` exposes warehouse tools over MCP
- `web/` is the React assistant client, `ops-dashboard/` is the Angular
  operations UI, and `mobile/` is the Expo worker app
- `knowledge/` is retrieval content for the AI assistant

## Important Paths

- `app/auth/`: Firebase verification, API-key fallback, authorization helpers
- `app/core/`: middleware, config, tenant context, logging, OpenAPI, responses
- `app/masters/`: organizations, facilities, SKUs, zones, locations, users,
  roles
- `app/operations/`: transactions, picks, drops, mobile task flows, state
  machines
- `app/inventory/`: balances, ledger, inventory queries and mutations
- `app/documents/`: transaction document config, templates, generation
- `app/connectors/`: connector config, StockOne sync, Celery tasks, sync logs
- `app/ai/`: chat routes, providers, embeddings, tool execution
- `app/notifications/`: device tokens and realtime task notifications
- `app/mcp/`: MCP auth, tool definitions, analytics helpers
- `wms_middleware/`: Django settings, URL wiring, ASGI/WSGI, Celery bootstrap
- `web/`: React + Vite assistant UI
- `ops-dashboard/`: Angular ops dashboard
- `mobile/`: Expo React Native worker app
- `tests/domain/`: service, inventory, and state-machine tests
- `tests/`: API, middleware, AI, connector, logging, schema, and admin tests
- `docs/`: architecture and application docs
- `knowledge/`: markdown SOP/reference corpus used by RAG
- `postman/YES_WMS.postman_collection.json`: shared API collection
- `nginx/`: local reverse proxy for `/web`, `/opsdashboard`, `/mobile`, and
  `/api`
- `k8s/uat/`: deployment manifests
- `.github/workflows/`: image and deployment automation
- `.env.example`: canonical runtime template

## Working Rules

- Do not create `v1`, `v2`, or compatibility package namespaces inside the
  backend
- Do not add a second HTTP API base path or proxy-style legacy routes
- Keep business HTTP routes mounted under the existing `/api/v1` routers instead
  of inventing new top-level prefixes
- Do not break the separate MCP and WebSocket surfaces already wired in
  `wms_middleware/asgi.py`
- Keep the protected-route contract aligned to `warehouse`, auth, `X-Org-Id`,
  and `X-Facility-Id` exactly as route scope requires
- Treat Firebase auth as primary; keep `X-API-Key` fallback limited to the
  business routes that already allow it
- `masters/me`, `masters/users*`, `ai/*`, and mobile session bootstrap are
  Firebase-only flows
- Prefer service-layer changes over putting business logic directly in route
  files
- When changing transaction execution, preserve inventory ledger writes, task
  state transitions, document generation, and user-facing notifications
- When changing mobile task flows, preserve lock handling, paired pick/drop
  behavior, points/streak bookkeeping, and WebSocket/push hooks
- When changing connectors, preserve Celery orchestration, `SyncLog`
  bookkeeping, mapping hashes, and provider-specific mappers
- When changing AI chat, preserve SSE streaming, tool confirmation for
  mutations, conversation persistence, and embedding/RAG behavior
- Avoid hand-editing generated output such as `ops-dashboard/dist/` or
  `staticfiles/` unless the task is explicitly about generated artifacts
- Do not overengineer. Prefer direct, readable code over new abstractions,
  indirection layers, or generic frameworks

## Run Everything in Docker

- Prefer Docker Compose over host-installed commands
- Start the full stack with `docker compose up --build`
- Backend shell: `docker compose exec wms-middleware sh`
- Migrations: `docker compose exec wms-middleware python manage.py migrate`
- Backend tests: `docker compose exec wms-middleware python -m pytest`
- Targeted backend tests: `docker compose exec wms-middleware python -m pytest tests/test_ai_routes.py -q`
- Celery logs: `docker compose logs -f celery-worker celery-beat`
- Web build: `docker compose exec web npm run build`
- Ops dashboard build: `docker compose exec ops-dashboard npm run build`
- Mobile service: `docker compose up mobile`
- Mobile logs: `docker compose logs -f mobile`
- If a service is not already running, use `docker compose run --rm <service> ...`
  instead of falling back to host tooling
- Local API is available at `http://localhost:8010/api/v1`
- Nginx serves the clients at `http://localhost/`, with `/web/`,
  `/opsdashboard/`, and `/mobile/`

## Testing Expectations

- For backend domain changes, run the closest `tests/domain/*` file plus the
  relevant API tests
- For auth, tenant, routing, or OpenAPI changes, run the middleware and route
  tests before considering the change done
- For connectors or Celery changes, run connector tests and verify worker/beat
  assumptions
- For AI or MCP changes, run AI route/service tests and confirm SSE or MCP auth
  assumptions
- For web, ops-dashboard, or mobile changes, at minimum run the relevant
  Dockerized build even if no dedicated test suite exists
- If docs or Postman collections change, keep examples consistent with the
  running routes, headers, and env vars

## Documentation Expectations

- `README.md` should describe the current full stack while keeping the HTTP API
  story centered on `/api/v1`
- Public API docs, examples, and Postman collections should refer to `/api/v1`
  only for HTTP business endpoints
- Mention `/mcp` or `/ws/tasks/` only when the change actually concerns MCP or
  realtime clients
- Examples should use real repo artifacts such as `.env.example`,
  `docker-compose.yml`, `manage.py`, `pytest.ini`, `web/`, `ops-dashboard/`,
  and `mobile/`
- Keep `AGENTS.md` as the canonical repo instruction file and update it when the
  architecture shifts

## Decision Log

- The backend application package is `app`
- The only public HTTP API family is `/api/v1`
- Existing non-HTTP-API ASGI surfaces are `/mcp`, `/.well-known`, and
  `/ws/tasks/`
- Auth is Firebase-first with optional legacy API-key fallback for approved
  business routes
- `warehouse` remains mandatory on protected HTTP business routes except
  explicit bootstrap and docs exemptions
- Org and facility scope are enforced with `X-Org-Id` and `X-Facility-Id`
- Transactions, inventory, and worker task flows are coupled by design and
  should be changed together
- Connector sync runs through Celery + Redis and should not be rewritten as
  inline request/response work
- AI chat persists conversations and messages and streams responses over SSE
- The repo ships three client apps: React assistant, Angular ops dashboard, and
  Expo mobile worker app

## Working Notes

- Default to the smallest change that keeps masters, operations, inventory,
  auth, and client flows consistent
- If you touch routing, middleware, auth, or shared schemas, inspect both the
  backend tests and the client consumers that depend on them
- If you touch facility or session behavior, check `web/`, `ops-dashboard/`,
  and `mobile/` for header/bootstrap assumptions
- If a proposed change feels bad, say so and suggest a better path before
  implementing it
