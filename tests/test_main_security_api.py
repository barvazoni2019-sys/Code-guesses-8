import json
import os
import subprocess
import time
import urllib.error
import urllib.request


def _post(path: str, payload: dict, headers: dict[str, str] | None = None) -> tuple[int, dict]:
    req = urllib.request.Request(
        f"http://127.0.0.1:8000{path}",
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json", **(headers or {})},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=3) as resp:
            return resp.status, json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode())


def test_requires_api_key_when_enabled() -> None:
    env = {**os.environ, "REQUIRE_API_KEY": "true", "API_KEYS": "secret-1", "RATE_LIMIT_PER_MINUTE": "100"}
    proc = subprocess.Popen(["python", "-m", "app.main"], env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        time.sleep(1)
        code_no_key, body_no_key = _post("/analyze", {"leads": []})
        assert code_no_key == 401
        assert body_no_key["error"] == "unauthorized"

        code_ok, _ = _post("/analyze", {"leads": []}, headers={"X-API-Key": "secret-1"})
        assert code_ok == 200
    finally:
        proc.terminate()
        proc.wait(timeout=3)


def test_rate_limit_blocks_after_threshold() -> None:
    env = {**os.environ, "REQUIRE_API_KEY": "false", "RATE_LIMIT_PER_MINUTE": "1"}
    proc = subprocess.Popen(["python", "-m", "app.main"], env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        time.sleep(1)
        code1, _ = _post("/analyze", {"leads": []})
        code2, body2 = _post("/analyze", {"leads": []})
        assert code1 == 200
        assert code2 == 429
        assert body2["error"] == "rate_limited"
    finally:
        proc.terminate()
        proc.wait(timeout=3)
