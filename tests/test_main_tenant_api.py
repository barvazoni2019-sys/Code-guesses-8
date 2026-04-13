import json
import os
import subprocess
import time
import urllib.error
import urllib.request


def _request(method: str, path: str, payload: dict | None = None, headers: dict[str, str] | None = None) -> tuple[int, dict | list]:
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(
        f"http://127.0.0.1:8000{path}",
        data=data,
        headers={"Content-Type": "application/json", **(headers or {})},
        method=method,
    )
    try:
        with urllib.request.urlopen(req, timeout=3) as resp:
            return resp.status, json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode())


def test_tenant_scoped_leads_visibility() -> None:
    env = {
        **os.environ,
        "REQUIRE_API_KEY": "true",
        "API_KEYS": "t1-key,t2-key",
        "API_KEY_ROLES": "t1-key:admin,t2-key:admin",
        "API_KEY_TENANTS": "t1-key:tenant-1,t2-key:tenant-2",
        "RATE_LIMIT_PER_MINUTE": "100",
    }
    proc = subprocess.Popen(["python", "-m", "app.main"], env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        time.sleep(1)
        payload = {
            "source": "whatsapp",
            "external_id": "same-id",
            "customer_name": "Customer",
            "timestamp": "2026-04-13T10:00:00",
        }
        _request("POST", "/webhook/ingest", payload, headers={"X-API-Key": "t1-key"})
        _request("POST", "/webhook/ingest", payload, headers={"X-API-Key": "t2-key"})

        _, leads_t1 = _request("GET", "/leads", headers={"X-API-Key": "t1-key"})
        _, leads_t2 = _request("GET", "/leads", headers={"X-API-Key": "t2-key"})

        assert len(leads_t1) == 1
        assert len(leads_t2) == 1
        assert leads_t1[0]["tenant_id"] == "tenant-1"
        assert leads_t2[0]["tenant_id"] == "tenant-2"
    finally:
        proc.terminate()
        proc.wait(timeout=3)
