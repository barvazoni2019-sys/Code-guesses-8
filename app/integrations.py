from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from .models import Channel, Lead, LeadStatus


@dataclass(slots=True)
class InboundEvent:
    source: str
    external_id: str
    customer_name: str
    timestamp: datetime
    text: str
    estimated_value_ils: float = 0.0


def source_to_channel(source: str) -> Channel:
    normalized = source.lower().strip()
    mapping = {
        "whatsapp": Channel.whatsapp,
        "instagram": Channel.instagram,
        "email": Channel.email,
        "form": Channel.website_form,
        "website_form": Channel.website_form,
        "phone": Channel.phone,
    }
    return mapping.get(normalized, Channel.website_form)


def event_to_lead(event: InboundEvent) -> Lead:
    """Convert inbound events from channels to canonical Lead model."""
    return Lead(
        lead_id=f"{event.source}-{event.external_id}",
        customer_name=event.customer_name,
        channel=source_to_channel(event.source),
        created_at=event.timestamp,
        last_response_at=None,
        status=LeadStatus.new,
        quote_value_ils=event.estimated_value_ils,
        tags=["from_webhook"],
    )
