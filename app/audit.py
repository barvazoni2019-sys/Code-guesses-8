from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any


@dataclass(slots=True)
class AuditLogger:
    path: str = "data/audit.log"
    _path: Path = field(init=False)

    def __post_init__(self) -> None:
        self._path = Path(self.path)
        self._path.parent.mkdir(parents=True, exist_ok=True)

    def log(self, event: dict[str, Any]) -> None:
        row = {"ts": datetime.utcnow().isoformat(), **event}
        with self._path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(row, ensure_ascii=False, default=str) + "\n")

    def tail(self, n: int = 50) -> list[dict[str, Any]]:
        if not self._path.exists():
            return []
        lines = self._path.read_text(encoding="utf-8").strip().splitlines()
        result: list[dict[str, Any]] = []
        for line in lines[-n:]:
            if not line.strip():
                continue
            result.append(json.loads(line))
        return result
