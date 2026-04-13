from __future__ import annotations

import json
import uuid
from dataclasses import asdict
from datetime import datetime, timedelta
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any

from .audit import AuditLogger
from .automation import AutomationRunner
from .config import Settings
from .connectors import EmailConnector, InstagramConnector, WhatsAppConnector
from .engine import RevenueLeakEngine
from .integrations import InboundEvent, event_to_lead
from .models import Channel, Lead, LeadStatus
from .orchestrator import RevenueOrchestrator
from .storage import JsonLeadRepository
from .security import ApiKeyAuth, RateLimiter, RoleAuthorizer, TenantAuthorizer

engine = RevenueLeakEngine()
orchestrator = RevenueOrchestrator(engine)
repo = JsonLeadRepository()
automation_runner = AutomationRunner()
settings = Settings()
wa_connector = WhatsAppConnector(settings)
ig_connector = InstagramConnector(settings)
email_connector = EmailConnector(settings)
auth = ApiKeyAuth(settings.api_keys())
role_authorizer = RoleAuthorizer(settings.api_key_roles())
tenant_authorizer = TenantAuthorizer(settings.api_key_tenants())
rate_limiter = RateLimiter(max_requests=settings.rate_limit_per_minute, window_seconds=60)
audit_logger = AuditLogger()


REQUIRED_WEBHOOK_FIELDS = {"source", "external_id", "customer_name", "timestamp"}


def _parse_lead(item: dict[str, Any]) -> Lead:
    return Lead(
        lead_id=item["lead_id"],
        customer_name=item["customer_name"],
        channel=Channel(item["channel"]),
        created_at=datetime.fromisoformat(item["created_at"]),
        tenant_id=item.get("tenant_id", "default"),
        last_response_at=datetime.fromisoformat(item["last_response_at"]) if item.get("last_response_at") else None,
        status=LeadStatus(item.get("status", "new")),
        quote_value_ils=float(item.get("quote_value_ils", 0)),
        meeting_booked=bool(item.get("meeting_booked", False)),
        meeting_canceled=bool(item.get("meeting_canceled", False)),
        tags=item.get("tags", []),
    )


def _parse_leads(items: list[dict[str, Any]]) -> list[Lead]:
    return [_parse_lead(item) for item in items]


def _upsert_lead(existing: list[Lead], incoming: Lead) -> list[Lead]:
    by_id = {(lead.tenant_id, lead.lead_id): lead for lead in existing}
    by_id[(incoming.tenant_id, incoming.lead_id)] = incoming
    return list(by_id.values())


class Handler(BaseHTTPRequestHandler):
    def _json_response(self, payload: dict | list, code: int = 200, request_id: str | None = None) -> None:
        body = json.dumps(payload, ensure_ascii=False, default=str).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        if request_id:
            self.send_header("X-Request-ID", request_id)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

        audit_logger.log(
            {
                "request_id": request_id,
                "method": self.command,
                "path": self.path,
                "status_code": code,
                "client": self.client_address[0] if self.client_address else None,
            }
        )

    def _read_payload(self) -> dict[str, Any]:
        content_length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(content_length)
        if not raw:
            return {}
        try:
            return json.loads(raw.decode("utf-8"))
        except json.JSONDecodeError:
            raise ValueError("invalid_json")

    def _enforce_security(self, method: str, path: str) -> tuple[bool, dict | None, int | None, str, str]:
        api_key = self.headers.get("X-API-Key")

        if settings.require_api_key and not auth.is_authorized(api_key):
            return False, {"error": "unauthorized"}, 401, "anonymous", "default"

        role = role_authorizer.role_for_key(api_key)
        tenant = tenant_authorizer.tenant_for_key(api_key)
        if not role_authorizer.is_allowed(role, method, path):
            return False, {"error": "forbidden", "role": role}, 403, role, tenant

        identity = api_key or self.client_address[0]
        if not rate_limiter.allow(identity):
            return False, {"error": "rate_limited"}, 429, role, tenant

        return True, None, None, role, tenant

    def do_GET(self) -> None:  # noqa: N802
        request_id = uuid.uuid4().hex
        ok, sec_body, sec_code, role, tenant = self._enforce_security("GET", self.path)
        if not ok and self.path != "/health":
            return self._json_response(sec_body or {"error": "security"}, sec_code or 400, request_id=request_id)

        if self.path == "/health":
            return self._json_response({"status": "ok"}, request_id=request_id)

        if self.path == "/integration-status":
            return self._json_response({"env": settings.app_env, "integrations": settings.integration_status(), "security": {"require_api_key": settings.require_api_key, "rate_limit_per_minute": settings.rate_limit_per_minute, "role": role, "tenant": tenant}}, request_id=request_id)

        if self.path == "/leads":
            leads = [asdict(lead) for lead in repo.load() if lead.tenant_id == tenant]
            return self._json_response(leads, request_id=request_id)

        if self.path == "/audit/recent":
            return self._json_response(audit_logger.tail(50), request_id=request_id)

        self._json_response({"error": "not found"}, 404, request_id=request_id)

    def do_POST(self) -> None:  # noqa: N802
        request_id = uuid.uuid4().hex
        try:
            payload = self._read_payload()
        except ValueError:
            return self._json_response({"error": "invalid_json"}, 400, request_id=request_id)

        ok, sec_body, sec_code, role, tenant = self._enforce_security("POST", self.path)
        if not ok:
            return self._json_response(sec_body or {"error": "security"}, sec_code or 400, request_id=request_id)

        try:
            if self.path == "/webhook/ingest":
                missing = [field for field in REQUIRED_WEBHOOK_FIELDS if field not in payload]
                if missing:
                    return self._json_response({"error": "missing_fields", "fields": missing}, 400, request_id=request_id)

                event = InboundEvent(
                    source=payload["source"],
                    external_id=payload["external_id"],
                    customer_name=payload["customer_name"],
                    timestamp=datetime.fromisoformat(payload["timestamp"]),
                    text=payload.get("text", ""),
                    estimated_value_ils=float(payload.get("estimated_value_ils", 0)),
                )
                current = repo.load()
                merged = _upsert_lead(current, event_to_lead(event, tenant_id=tenant))
                repo.save(merged)
                return self._json_response({"status": "ingested", "leads_count": len(merged)}, request_id=request_id)

            if self.path == "/seed-sample":
                sample = _sample_leads()
                repo.save(sample)
                return self._json_response({"status": "seeded", "count": len(sample)}, request_id=request_id)

            if self.path == "/leads/import":
                leads = _parse_leads(payload.get("leads", []))
                for lead in leads:
                    lead.tenant_id = tenant
                repo.save(leads)
                return self._json_response({"status": "saved", "count": len(leads)}, request_id=request_id)

            leads_payload = payload.get("leads")
            if leads_payload:
                leads = _parse_leads(leads_payload)
                for lead in leads:
                    lead.tenant_id = tenant
            else:
                leads = [lead for lead in repo.load() if lead.tenant_id == tenant]
            now = datetime.fromisoformat(payload["now"]) if payload.get("now") else None

            if self.path == "/send-preview":
                provider = payload.get("provider", "whatsapp")
                destination = payload.get("destination", "demo-user")
                text = payload.get("text", "שלום! זו הודעת בדיקה ממערכת Ghost Revenue")

                if provider == "whatsapp":
                    return self._json_response(wa_connector.send_message(destination, text), request_id=request_id)
                if provider == "instagram":
                    return self._json_response(ig_connector.send_message(destination, text), request_id=request_id)
                if provider == "email":
                    return self._json_response(email_connector.send_message(destination, text), request_id=request_id)

                return self._json_response({"ok": False, "reason": "unsupported_provider"}, 400, request_id=request_id)

            if self.path == "/analyze":
                findings = [asdict(f) for f in engine.analyze(leads, now=now)]
                return self._json_response(findings, request_id=request_id)

            if self.path == "/dashboard":
                summary = asdict(engine.dashboard(leads, now=now))
                return self._json_response(summary, request_id=request_id)

            if self.path == "/action-queue":
                tasks = [asdict(t) for t in orchestrator.build_action_queue(leads, now=now)]
                return self._json_response(tasks, request_id=request_id)

            if self.path == "/reactivation":
                candidates = [asdict(c) for c in orchestrator.reactivation_candidates(leads, now=now)]
                return self._json_response(candidates, request_id=request_id)

            if self.path == "/run-automation":
                tasks = orchestrator.build_action_queue(leads, now=now)
                result = automation_runner.run(tasks, now=now)
                return self._json_response(result, request_id=request_id)

            if self.path == "/closer-shadow":
                insights = [asdict(i) for i in orchestrator.closer_shadow_insights(leads, now=now)]
                return self._json_response(insights, request_id=request_id)

            self._json_response({"error": "not found"}, 404, request_id=request_id)
        except (KeyError, ValueError) as exc:
            return self._json_response({"error": "bad_request", "detail": str(exc)}, 400, request_id=request_id)


def _sample_leads() -> list[Lead]:
    now = datetime.utcnow()
    return [
        Lead(
            lead_id="S-1001",
            customer_name="Noa",
            channel=Channel.whatsapp,
            created_at=now - timedelta(hours=6),
            status=LeadStatus.new,
            quote_value_ils=4800,
            tags=["new"],
        ),
        Lead(
            lead_id="S-1002",
            customer_name="Eden",
            channel=Channel.email,
            created_at=now - timedelta(days=6),
            last_response_at=now - timedelta(days=4),
            status=LeadStatus.quoted,
            quote_value_ils=11200,
        ),
        Lead(
            lead_id="S-1003",
            customer_name="Yoni",
            channel=Channel.instagram,
            created_at=now - timedelta(days=20),
            last_response_at=now - timedelta(days=16),
            status=LeadStatus.contacted,
            quote_value_ils=7600,
            tags=["urgent"],
        ),
    ]


def run(host: str = "0.0.0.0", port: int | None = None) -> None:
    port = port or settings.app_port
    server = HTTPServer((host, port), Handler)
    print(f"Ghost Revenue MVP running on http://{host}:{port}")
    server.serve_forever()


if __name__ == "__main__":
    run()
