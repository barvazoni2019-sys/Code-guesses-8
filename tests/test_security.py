from datetime import datetime, timedelta

from app.security import ApiKeyAuth, RateLimiter, RoleAuthorizer, TenantAuthorizer


def test_api_key_auth() -> None:
    auth = ApiKeyAuth({"k1", "k2"})
    assert auth.is_authorized("k1") is True
    assert auth.is_authorized("bad") is False


def test_role_authorizer() -> None:
    roles = RoleAuthorizer({"a1": "admin", "v1": "viewer", "g1": "agent"})
    assert roles.role_for_key("a1") == "admin"
    assert roles.role_for_key("missing") == "agent"

    assert roles.is_allowed("admin", "POST", "/seed-sample") is True
    assert roles.is_allowed("viewer", "POST", "/analyze") is False
    assert roles.is_allowed("agent", "GET", "/audit/recent") is False


def test_rate_limiter_window() -> None:
    limiter = RateLimiter(max_requests=2, window_seconds=60)
    now = datetime(2026, 1, 1, 10, 0, 0)

    assert limiter.allow("id", now=now) is True
    assert limiter.allow("id", now=now + timedelta(seconds=1)) is True
    assert limiter.allow("id", now=now + timedelta(seconds=2)) is False
    assert limiter.allow("id", now=now + timedelta(seconds=61)) is True


def test_tenant_authorizer() -> None:
    tenants = TenantAuthorizer({"k1": "clinic-a"})
    assert tenants.tenant_for_key("k1") == "clinic-a"
    assert tenants.tenant_for_key("missing") == "default"
    assert tenants.within_scope("clinic-a", "clinic-a") is True
    assert tenants.within_scope("clinic-a", "clinic-b") is False
