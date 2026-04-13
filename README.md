# Ghost Revenue — Revenue OS MVP+

A working backend prototype for your concept: **"AI שמוצא כסף אבוד ומחזיר אותו"**.

## Implemented modules

1. **Leak Hunter Engine**
   - Detects lost-revenue patterns:
     - no response in SLA
     - cold leads after interest
     - stuck quotes
     - canceled meetings without follow-up
     - upsell opportunities

2. **Action Queue (Sales Tasks)**
   - Builds prioritized tasks (`p1`, `p2`, `p3`)
   - Generates next-action + draft message per lead

3. **Re-Activation Machine**
   - Scores dormant leads likely to return
   - Generates campaign message suggestions

4. **Closer Shadow (Rule-based v1)**
   - Estimates close probability for contacted/quoted leads
   - Suggests likely objection, next line, best send window, and discount recommendation

5. **Data Persistence**
   - JSON repository (`data/leads.json`) for quick local persistence

6. **Integration Placeholders (ready for your final API wiring)**
   - Settings loader for all external providers (WhatsApp, Instagram, CRM, Email, LLM)
   - Connector stubs with TODO points where you can plug exact API requests

## HTTP API

### Health & data
- `GET /health`
- `GET /integration-status`
- `GET /leads`
- `GET /audit/recent`
- `POST /leads/import`
- `POST /seed-sample`
- `POST /webhook/ingest`

### Core intelligence
- `POST /analyze`
- `POST /dashboard`
- `POST /action-queue`
- `POST /reactivation`
- `POST /closer-shadow`
- `POST /run-automation`

### Connector preview (stubs)
- `POST /send-preview`
  - payload example:
    ```json
    {
      "provider": "whatsapp",
      "destination": "9725XXXXXXX",
      "text": "הודעת בדיקה"
    }
    ```

### Notes
- `POST /webhook/ingest` now validates required fields and returns `400` on missing payload keys.
- Webhook ingestion is idempotent by `lead_id` (derived from `source-external_id`) to avoid duplicates on retries.

## Observability (enabled now)

- Every response includes `X-Request-ID`
- Audit log file: `data/audit.log` (JSONL)
- `GET /audit/recent` returns the latest audit rows for debugging

## Security (enabled now)

## Tenant Scoping (enabled now)

- API keys can map to tenants via `API_KEY_TENANTS`
- Example: `API_KEY_TENANTS=admin-key:clinic-a,viewer-key:clinic-b`
- Data endpoints (`/leads`, `/analyze`, `/dashboard`, etc.) now operate on the caller tenant scope.

## RBAC (enabled now)

- API keys can map to roles via `API_KEY_ROLES`
- Supported roles: `admin`, `agent`, `viewer`
- Example: `API_KEY_ROLES=admin-key:admin,viewer-key:viewer`
- Current policy:
  - `admin`: full access
  - `agent`: all except `GET /audit/recent` and `POST /seed-sample`
  - `viewer`: read-only (`GET /health`, `GET /integration-status`, `GET /leads`)

- Optional API key enforcement (`REQUIRE_API_KEY=true`)
- Header: `X-API-Key: <your-key>`
- Basic in-memory rate limiting (`RATE_LIMIT_PER_MINUTE`, default `60`)

## Environment variables (fill these when you connect real APIs)

```bash
APP_ENV=dev
APP_PORT=8000

WHATSAPP_ACCESS_TOKEN=
WHATSAPP_PHONE_NUMBER_ID=

INSTAGRAM_ACCESS_TOKEN=
INSTAGRAM_IG_USER_ID=

CRM_BASE_URL=
CRM_API_KEY=

SMTP_HOST=
SMTP_USER=
SMTP_PASSWORD=

OPENAI_API_KEY=

REQUIRE_API_KEY=false
API_KEYS=
API_KEY_ROLES=
API_KEY_TENANTS=
RATE_LIMIT_PER_MINUTE=60
```

## Run locally

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m app.main
```

## Quick demo flow

1. `POST /seed-sample`
2. `GET /integration-status`
3. `GET /leads`
4. `POST /dashboard`
5. `POST /action-queue`
6. `POST /reactivation`
7. `POST /closer-shadow`
8. `POST /run-automation`
9. `POST /send-preview`

## Current architecture

- `app/models.py` — domain entities
- `app/engine.py` — leak detection + dashboard math
- `app/orchestrator.py` — action queue, reactivation, closer insights
- `app/storage.py` — JSON repository
- `app/main.py` — HTTP server and routes
- `app/integrations.py` — webhook event normalization
- `app/automation.py` — outbound automation runner + outbox
- `app/config.py` — env settings and integration readiness checks
- `app/connectors.py` — provider connector stubs + TODO hooks
- `tests/` — engine, orchestrator, storage, integrations, automation, config/connector tests

## What is still needed for production

- Real integrations: WhatsApp Cloud API, Instagram, CRM, Email, Calendar
- Authentication and multi-tenant security
- Async job runner for outbound actions and retries
- Audit logs + observability
- LLM-powered message personalization (with guardrails)
- Billing + usage tracking
