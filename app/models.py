from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional


class LeadStatus(str, Enum):
    NEW = "new"
    CONTACTED = "contacted"
    WON = "won"
    LOST = "lost"


@dataclass
class LeadCreate:
    name: str
    business_type: str
    monthly_budget_usd: float
    urgency: int
    pain: str
    channel: str = "whatsapp"


@dataclass
class LeadEvent:
    type: str
    note: str
    happened_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class Lead:
    id: str
    name: str
    business_type: str
    monthly_budget_usd: float
    urgency: int
    pain: str
    channel: str = "whatsapp"

    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    status: LeadStatus = LeadStatus.NEW

    heat_score: Optional[int] = None
    follow_up_text: Optional[str] = None
    events: list[LeadEvent] = field(default_factory=list)


@dataclass
class FollowUpResponse:
    lead_id: str
    follow_up_text: str


@dataclass
class ScoreResponse:
    lead_id: str
    heat_score: int
