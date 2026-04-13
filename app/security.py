from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta


@dataclass(slots=True)
class ApiKeyAuth:
    allowed_keys: set[str] = field(default_factory=set)

    def is_authorized(self, key: str | None) -> bool:
        if not self.allowed_keys:
            return True
        return bool(key and key in self.allowed_keys)


@dataclass(slots=True)
class RoleAuthorizer:
    key_roles: dict[str, str] = field(default_factory=dict)

    def role_for_key(self, api_key: str | None) -> str:
        if not api_key:
            return "agent"
        return self.key_roles.get(api_key, "agent")

    def is_allowed(self, role: str, method: str, path: str) -> bool:
        # admin can access everything
        if role == "admin":
            return True

        # agent: allow core operations, deny audit visibility and seed mutations
        if role == "agent":
            denied = {("GET", "/audit/recent"), ("POST", "/seed-sample")}
            return (method, path) not in denied

        # viewer: read-only analytics/status
        if role == "viewer":
            return method == "GET" and path in {"/health", "/integration-status", "/leads"}

        return False


@dataclass(slots=True)
class RateLimiter:
    max_requests: int = 60
    window_seconds: int = 60
    _events: dict[str, deque[datetime]] = field(default_factory=lambda: defaultdict(deque))

    def allow(self, identity: str, now: datetime | None = None) -> bool:
        now = now or datetime.utcnow()
        cutoff = now - timedelta(seconds=self.window_seconds)
        queue = self._events[identity]

        while queue and queue[0] < cutoff:
            queue.popleft()

        if len(queue) >= self.max_requests:
            return False

        queue.append(now)
        return True
