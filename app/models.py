from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Literal


class Channel(str, Enum):
    whatsapp = "whatsapp"
    instagram = "instagram"
    email = "email"
    website_form = "website_form"
    phone = "phone"


class LeadStatus(str, Enum):
    new = "new"
    contacted = "contacted"
    quoted = "quoted"
    won = "won"
    lost = "lost"


@dataclass(slots=True)
class Lead:
    lead_id: str
    customer_name: str
    channel: Channel
    created_at: datetime
    last_response_at: datetime | None = None
    status: LeadStatus = LeadStatus.new
    quote_value_ils: float = 0
    meeting_booked: bool = False
    meeting_canceled: bool = False
    tags: list[str] = field(default_factory=list)


class LeakType(str, Enum):
    no_response = "no_response"
    disappeared_after_interest = "disappeared_after_interest"
    quote_stuck = "quote_stuck"
    canceled_meeting_no_followup = "canceled_meeting_no_followup"
    upsell_opportunity = "upsell_opportunity"


@dataclass(slots=True)
class LeakFinding:
    lead_id: str
    leak_type: LeakType
    severity: Literal["low", "medium", "high"]
    reason: str
    recommended_message: str


@dataclass(slots=True)
class DashboardSummary:
    weekly_revenue_ils: float
    almost_lost_revenue_ils: float
    top_10_to_contact: list[LeakFinding]
    generated_at: datetime


@dataclass(slots=True)
class ActionTask:
    lead_id: str
    customer_name: str
    priority: Literal["p1", "p2", "p3"]
    action: str
    scheduled_for: datetime
    draft_message: str


@dataclass(slots=True)
class ReactivationCandidate:
    lead_id: str
    customer_name: str
    score: float
    reason: str
    campaign_message: str


@dataclass(slots=True)
class CloserInsight:
    lead_id: str
    close_probability: float
    likely_objection: str
    best_next_line: str
    best_send_window: str
    suggest_discount: bool
