import json
import subprocess
import time
import urllib.error
import urllib.request


def _request(path: str, payload: dict | None = None, method: str = "POST") -> tuple[int, dict]:
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(
        f"http://127.0.0.1:8000{path}",
        data=data,
        headers={"Content-Type": "application/json"},
        method=method,
    )
    try:
        with urllib.request.urlopen(req, timeout=3) as resp:
            body = json.loads(resp.read().decode())
            return resp.status, body
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode())


def test_webhook_missing_fields_returns_400() -> None:
    proc = subprocess.Popen(["python", "-m", "app.main"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        time.sleep(1)
        code, body = _request("/webhook/ingest", payload={"source": "whatsapp"})
        assert code == 400
        assert body["error"] == "missing_fields"
    finally:
        proc.terminate()
        proc.wait(timeout=3)


def test_webhook_is_idempotent_by_lead_id() -> None:
    proc = subprocess.Popen(["python", "-m", "app.main"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        time.sleep(1)
        payload = {
            "source": "whatsapp",
            "external_id": "id-1",
            "customer_name": "A",
            "timestamp": "2026-04-13T10:00:00",
        }
        code1, body1 = _request("/webhook/ingest", payload=payload)
        code2, body2 = _request("/webhook/ingest", payload=payload)
        assert code1 == 200
        assert code2 == 200
        assert body2["leads_count"] == body1["leads_count"]
    finally:
        proc.terminate()
        proc.wait(timeout=3)
