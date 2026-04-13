from datetime import datetime

from app.integrations import InboundEvent, event_to_lead, source_to_channel
from app.models import Channel


def test_source_to_channel_mapping() -> None:
    assert source_to_channel("whatsapp") == Channel.whatsapp
    assert source_to_channel("instagram") == Channel.instagram
    assert source_to_channel("unknown") == Channel.website_form


def test_event_to_lead_conversion() -> None:
    event = InboundEvent(
        source="email",
        external_id="99",
        customer_name="Maya",
        timestamp=datetime(2026, 4, 13, 10, 0, 0),
        text="Interested",
        estimated_value_ils=6500,
    )
    lead = event_to_lead(event)

    assert lead.lead_id == "email-99"
    assert lead.channel == Channel.email
    assert lead.quote_value_ils == 6500
