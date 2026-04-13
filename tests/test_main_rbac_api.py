import json
import os
import subprocess
import time
import urllib.error
import urllib.request


def _request(method: str, path: str, payload: dict | None = None, headers: dict[str, str] | None = None) -> tuple[int, dict]:
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(
        f"http://127.0.0.1:8000{path}",
        data=data,
        headers={"Content-Type": "application/json", **(headers or {})},
        method=method,
    )
    try:
        with urllib.request.urlopen(req, timeout=3) as resp:
            return resp.status, json.loads(resp.read().decode()) if resp.readable() else {}
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode())


def test_viewer_forbidden_for_post_analyze() -> None:
    env = {
        **os.environ,
        "REQUIRE_API_KEY": "true",
        "API_KEYS": "viewer-key,admin-key",
        "API_KEY_ROLES": "viewer-key:viewer,admin-key:admin",
        "RATE_LIMIT_PER_MINUTE": "100",
    }
    proc = subprocess.Popen(["python", "-m", "app.main"], env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        time.sleep(1)
        code_viewer, body_viewer = _request("POST", "/analyze", {"leads": []}, headers={"X-API-Key": "viewer-key"})
        assert code_viewer == 403
        assert body_viewer["error"] == "forbidden"

        code_admin, _ = _request("POST", "/analyze", {"leads": []}, headers={"X-API-Key": "admin-key"})
        assert code_admin == 200
    finally:
        proc.terminate()
        proc.wait(timeout=3)


def test_agent_forbidden_for_audit_recent() -> None:
    env = {
        **os.environ,
        "REQUIRE_API_KEY": "true",
        "API_KEYS": "agent-key",
        "API_KEY_ROLES": "agent-key:agent",
        "RATE_LIMIT_PER_MINUTE": "100",
    }
    proc = subprocess.Popen(["python", "-m", "app.main"], env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        time.sleep(1)
        code, body = _request("GET", "/audit/recent", headers={"X-API-Key": "agent-key"})
        assert code == 403
        assert body["error"] == "forbidden"
    finally:
        proc.terminate()
        proc.wait(timeout=3)
