import subprocess
import time
import urllib.request


def test_health_includes_request_id_header() -> None:
    proc = subprocess.Popen(["python", "-m", "app.main"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        time.sleep(1)
        resp = urllib.request.urlopen("http://127.0.0.1:8000/health", timeout=3)
        request_id = resp.headers.get("X-Request-ID")
        assert request_id is not None
        assert len(request_id) >= 8
    finally:
        proc.terminate()
        proc.wait(timeout=3)
