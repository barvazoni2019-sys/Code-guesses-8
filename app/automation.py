from __future__ import annotations

import json
from dataclasses import asdict
from datetime import datetime
from pathlib import Path

from .models import ActionTask


class Outbox:
    def __init__(self, path: str = "data/outbox.log"):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def append(self, row: dict) -> None:
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(row, ensure_ascii=False, default=str) + "\n")


class AutomationRunner:
    """MVP runner that simulates sending queued follow-up actions."""

    def __init__(self, outbox: Outbox | None = None):
        self.outbox = outbox or Outbox()

    def run(self, tasks: list[ActionTask], now: datetime | None = None) -> dict:
        now = now or datetime.utcnow()
        sent = 0
        queued = 0

        for task in tasks:
            if task.scheduled_for <= now:
                payload = asdict(task)
                payload["sent_at"] = now.isoformat()
                payload["status"] = "sent"
                self.outbox.append(payload)
                sent += 1
            else:
                queued += 1

        return {"sent": sent, "queued": queued, "total": len(tasks)}
