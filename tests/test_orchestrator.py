from datetime import datetime, timedelta

from app.models import Channel, Lead, LeadStatus
from app.orchestrator import RevenueOrchestrator


NOW = datetime(2026, 4, 13, 12, 0, 0)


def _fixture_leads() -> list[Lead]:
    return [
        Lead(
            lead_id="A1",
            customer_name="Shay",
            channel=Channel.whatsapp,
            created_at=NOW - timedelta(hours=4),
            status=LeadStatus.new,
            quote_value_ils=5000,
        ),
        Lead(
            lead_id="A2",
            customer_name="Lior",
            channel=Channel.email,
            created_at=NOW - timedelta(days=30),
            last_response_at=NOW - timedelta(days=24),
            status=LeadStatus.contacted,
            quote_value_ils=8000,
        ),
        Lead(
            lead_id="A3",
            customer_name="Gil",
            channel=Channel.phone,
            created_at=NOW - timedelta(days=10),
            last_response_at=NOW - timedelta(days=5),
            status=LeadStatus.quoted,
            quote_value_ils=15000,
            tags=["urgent"],
        ),
    ]


def test_action_queue_returns_prioritized_tasks() -> None:
    orchestrator = RevenueOrchestrator()
    tasks = orchestrator.build_action_queue(_fixture_leads(), now=NOW)

    assert len(tasks) >= 2
    assert tasks[0].priority == "p1"


def test_reactivation_scores_dormant_non_won_leads() -> None:
    orchestrator = RevenueOrchestrator()
    candidates = orchestrator.reactivation_candidates(_fixture_leads(), now=NOW)

    assert len(candidates) >= 1
    assert candidates[0].score >= 0.35


def test_closer_shadow_returns_insights_for_contacted_and_quoted() -> None:
    orchestrator = RevenueOrchestrator()
    insights = orchestrator.closer_shadow_insights(_fixture_leads(), now=NOW)

    assert len(insights) == 2
    assert insights[0].close_probability >= insights[1].close_probability
