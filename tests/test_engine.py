from datetime import datetime, timedelta

from app.engine import RevenueLeakEngine
from app.models import Channel, Lead, LeadStatus


NOW = datetime(2026, 4, 13, 12, 0, 0)


def test_engine_detects_multiple_leaks() -> None:
    engine = RevenueLeakEngine(response_sla_hours=2, quote_sla_days=3)
    leads = [
        Lead(
            lead_id="L1",
            customer_name="Dana",
            channel=Channel.whatsapp,
            created_at=NOW - timedelta(hours=5),
            last_response_at=None,
            status=LeadStatus.new,
            quote_value_ils=3500,
        ),
        Lead(
            lead_id="L2",
            customer_name="Omri",
            channel=Channel.email,
            created_at=NOW - timedelta(days=5),
            last_response_at=NOW - timedelta(days=4),
            status=LeadStatus.quoted,
            quote_value_ils=9000,
        ),
        Lead(
            lead_id="L3",
            customer_name="Yael",
            channel=Channel.phone,
            created_at=NOW - timedelta(days=2),
            last_response_at=NOW - timedelta(hours=30),
            status=LeadStatus.contacted,
            meeting_canceled=True,
            quote_value_ils=4500,
        ),
    ]

    findings = engine.analyze(leads, now=NOW)
    leak_types = {f.leak_type.value for f in findings}

    assert "no_response" in leak_types
    assert "quote_stuck" in leak_types
    assert "canceled_meeting_no_followup" in leak_types


def test_dashboard_rollup() -> None:
    engine = RevenueLeakEngine()
    leads = [
        Lead(
            lead_id="W1",
            customer_name="Roi",
            channel=Channel.instagram,
            created_at=NOW - timedelta(days=3),
            last_response_at=NOW - timedelta(days=1),
            status=LeadStatus.won,
            quote_value_ils=12000,
            tags=["basic"],
        ),
    ]

    summary = engine.dashboard(leads, now=NOW)
    assert summary.weekly_revenue_ils == 12000
    assert len(summary.top_10_to_contact) >= 1
