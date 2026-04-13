from __future__ import annotations

import json
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import Dict

from .models import Lead, LeadEvent, LeadStatus

DATA_FILE = Path("data/leads.json")


def _lead_from_dict(payload: dict) -> Lead:
    events = [
        LeadEvent(
            type=e["type"],
            note=e["note"],
            happened_at=datetime.fromisoformat(e["happened_at"]),
        )
        for e in payload.get("events", [])
    ]
    return Lead(
        id=payload["id"],
        name=payload["name"],
        business_type=payload["business_type"],
        monthly_budget_usd=payload["monthly_budget_usd"],
        urgency=payload["urgency"],
        pain=payload["pain"],
        channel=payload.get("channel", "whatsapp"),
        created_at=datetime.fromisoformat(payload["created_at"]),
        updated_at=datetime.fromisoformat(payload["updated_at"]),
        status=LeadStatus(payload["status"]),
        heat_score=payload.get("heat_score"),
        follow_up_text=payload.get("follow_up_text"),
        events=events,
    )


def _lead_to_dict(lead: Lead) -> dict:
    payload = asdict(lead)
    payload["created_at"] = lead.created_at.isoformat()
    payload["updated_at"] = lead.updated_at.isoformat()
    payload["status"] = lead.status.value
    payload["events"] = [
        {"type": e.type, "note": e.note, "happened_at": e.happened_at.isoformat()}
        for e in lead.events
    ]
    return payload


def load_leads() -> Dict[str, Lead]:
    if not DATA_FILE.exists():
        return {}
    raw = json.loads(DATA_FILE.read_text())
    return {lid: _lead_from_dict(payload) for lid, payload in raw.items()}


def save_leads(leads: Dict[str, Lead]) -> None:
    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    serializable = {lid: _lead_to_dict(lead) for lid, lead in leads.items()}
    DATA_FILE.write_text(json.dumps(serializable, indent=2))
