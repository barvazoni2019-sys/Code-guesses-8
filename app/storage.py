from __future__ import annotations

import json
from dataclasses import asdict
from datetime import datetime
from pathlib import Path

from .models import Channel, Lead, LeadStatus


class JsonLeadRepository:
    def __init__(self, path: str = "data/leads.json"):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def load(self) -> list[Lead]:
        if not self.path.exists():
            return []
        payload = json.loads(self.path.read_text(encoding="utf-8"))
        leads: list[Lead] = []
        for item in payload:
            leads.append(
                Lead(
                    lead_id=item["lead_id"],
                    customer_name=item["customer_name"],
                    channel=Channel(item["channel"]),
                    created_at=datetime.fromisoformat(item["created_at"]),
                    tenant_id=item.get("tenant_id", "default"),
                    last_response_at=datetime.fromisoformat(item["last_response_at"])
                    if item.get("last_response_at")
                    else None,
                    status=LeadStatus(item.get("status", "new")),
                    quote_value_ils=float(item.get("quote_value_ils", 0)),
                    meeting_booked=bool(item.get("meeting_booked", False)),
                    meeting_canceled=bool(item.get("meeting_canceled", False)),
                    tags=item.get("tags", []),
                )
            )
        return leads

    def save(self, leads: list[Lead]) -> None:
        rows = []
        for lead in leads:
            row = asdict(lead)
            row["channel"] = lead.channel.value
            row["status"] = lead.status.value
            row["created_at"] = lead.created_at.isoformat()
            row["last_response_at"] = lead.last_response_at.isoformat() if lead.last_response_at else None
            rows.append(row)
        self.path.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
