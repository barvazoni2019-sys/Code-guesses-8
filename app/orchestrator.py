from __future__ import annotations

from datetime import datetime, timedelta

from .engine import RevenueLeakEngine
from .models import ActionTask, Channel, CloserInsight, Lead, LeadStatus, ReactivationCandidate


class RevenueOrchestrator:
    """Coordinates leak detection, action queues, reactivation, and sales insights."""

    def __init__(self, engine: RevenueLeakEngine | None = None):
        self.engine = engine or RevenueLeakEngine()

    def build_action_queue(self, leads: list[Lead], now: datetime | None = None) -> list[ActionTask]:
        now = now or datetime.utcnow()
        findings = self.engine.analyze(leads, now)

        tasks: list[ActionTask] = []
        severity_to_priority = {"high": "p1", "medium": "p2", "low": "p3"}
        default_delay = {"p1": 10, "p2": 60, "p3": 180}
        lead_by_id = {lead.lead_id: lead for lead in leads}

        for finding in findings:
            lead = lead_by_id.get(finding.lead_id)
            if not lead:
                continue
            priority = severity_to_priority[finding.severity]
            tasks.append(
                ActionTask(
                    lead_id=lead.lead_id,
                    customer_name=lead.customer_name,
                    priority=priority,
                    action=f"followup:{finding.leak_type.value}",
                    scheduled_for=now + timedelta(minutes=default_delay[priority]),
                    draft_message=finding.recommended_message,
                )
            )

        tasks.sort(key=lambda task: (task.priority, task.scheduled_for))
        return tasks

    def reactivation_candidates(self, leads: list[Lead], now: datetime | None = None) -> list[ReactivationCandidate]:
        now = now or datetime.utcnow()
        candidates: list[ReactivationCandidate] = []

        for lead in leads:
            if lead.status == LeadStatus.won:
                continue
            dormant_days = (now - (lead.last_response_at or lead.created_at)).days
            if dormant_days < 14:
                continue

            score = min(0.99, 0.35 + (lead.quote_value_ils / 20000) + (dormant_days / 365))
            reason = f"Dormant {dormant_days}d, previous value ₪{lead.quote_value_ils:,.0f}"
            campaign_message = (
                f"היי {lead.customer_name}, פתחנו חלון קצר ללקוחות קודמים עם תנאים מועדפים לשבוע הקרוב. "
                "רוצה שאשריין לך שיחה קצרה?"
            )
            candidates.append(
                ReactivationCandidate(
                    lead_id=lead.lead_id,
                    customer_name=lead.customer_name,
                    score=round(score, 2),
                    reason=reason,
                    campaign_message=campaign_message,
                )
            )

        return sorted(candidates, key=lambda c: c.score, reverse=True)

    def closer_shadow_insights(self, leads: list[Lead], now: datetime | None = None) -> list[CloserInsight]:
        now = now or datetime.utcnow()
        insights: list[CloserInsight] = []

        for lead in leads:
            if lead.status not in {LeadStatus.contacted, LeadStatus.quoted}:
                continue

            hours_silent = int((now - (lead.last_response_at or lead.created_at)).total_seconds() // 3600)
            has_price_tag = lead.quote_value_ils > 0

            close_probability = 0.35
            if lead.status == LeadStatus.quoted:
                close_probability += 0.25
            if "urgent" in lead.tags:
                close_probability += 0.2
            if hours_silent < 24:
                close_probability += 0.1

            likely_objection = "מחיר" if has_price_tag else "תזמון"
            best_next_line = (
                f"{lead.customer_name}, כדי לעזור לך להחליט מהר — רוצה שאשלח השוואה קצרה של 2 מסלולים ונבחר יחד?"
            )
            best_send_window = "09:00-11:00" if lead.channel in {Channel.whatsapp, Channel.phone} else "15:00-17:00"
            suggest_discount = has_price_tag and lead.status == LeadStatus.quoted and hours_silent > 72

            insights.append(
                CloserInsight(
                    lead_id=lead.lead_id,
                    close_probability=round(min(close_probability, 0.95), 2),
                    likely_objection=likely_objection,
                    best_next_line=best_next_line,
                    best_send_window=best_send_window,
                    suggest_discount=suggest_discount,
                )
            )

        return sorted(insights, key=lambda i: i.close_probability, reverse=True)
