from __future__ import annotations

from datetime import datetime, timedelta

from .models import DashboardSummary, LeakFinding, LeakType, Lead, LeadStatus


class RevenueLeakEngine:
    """MVP engine for identifying lost-revenue opportunities."""

    def __init__(self, response_sla_hours: int = 2, quote_sla_days: int = 3):
        self.response_sla_hours = response_sla_hours
        self.quote_sla_days = quote_sla_days

    def analyze(self, leads: list[Lead], now: datetime | None = None) -> list[LeakFinding]:
        now = now or datetime.utcnow()
        findings: list[LeakFinding] = []

        for lead in leads:
            # 1) No response in SLA
            if lead.last_response_at is None and now - lead.created_at > timedelta(hours=self.response_sla_hours):
                findings.append(
                    LeakFinding(
                        lead_id=lead.lead_id,
                        leak_type=LeakType.no_response,
                        severity="high",
                        reason=f"No response for {int((now - lead.created_at).total_seconds() // 3600)}h",
                        recommended_message=(
                            f"היי {lead.customer_name}, ראיתי שהשארת פנייה ורציתי לעזור לך להתקדם כבר היום."
                        ),
                    )
                )

            # 2) Interested but disappeared
            if lead.status == LeadStatus.contacted and lead.last_response_at:
                if now - lead.last_response_at > timedelta(days=2):
                    findings.append(
                        LeakFinding(
                            lead_id=lead.lead_id,
                            leak_type=LeakType.disappeared_after_interest,
                            severity="medium",
                            reason="Lead went cold after initial contact",
                            recommended_message=(
                                f"היי {lead.customer_name}, רק בודק אם זה עדיין רלוונטי לך. אפשר לסגור לך מקום השבוע."
                            ),
                        )
                    )

            # 3) Quote stuck
            if lead.status == LeadStatus.quoted and lead.last_response_at:
                if now - lead.last_response_at > timedelta(days=self.quote_sla_days):
                    findings.append(
                        LeakFinding(
                            lead_id=lead.lead_id,
                            leak_type=LeakType.quote_stuck,
                            severity="high",
                            reason=f"Quote not closed for {self.quote_sla_days}+ days",
                            recommended_message=(
                                f"היי {lead.customer_name}, רציתי לעזור לך להשלים את ההצעה. האם תרצה/י שאשלח סיכום קצר לפני סגירה?"
                            ),
                        )
                    )

            # 4) Meeting canceled no follow-up
            if lead.meeting_canceled and lead.last_response_at:
                if now - lead.last_response_at > timedelta(hours=24):
                    findings.append(
                        LeakFinding(
                            lead_id=lead.lead_id,
                            leak_type=LeakType.canceled_meeting_no_followup,
                            severity="high",
                            reason="Canceled meeting without follow-up",
                            recommended_message=(
                                f"היי {lead.customer_name}, ראיתי שהפגישה התבטלה. רוצה שנקבע חלון קצר שנוח לך השבוע?"
                            ),
                        )
                    )

            # 5) Upsell opportunity for won clients
            if lead.status == LeadStatus.won and "premium" not in lead.tags:
                findings.append(
                    LeakFinding(
                        lead_id=lead.lead_id,
                        leak_type=LeakType.upsell_opportunity,
                        severity="low",
                        reason="Won customer with potential upsell",
                        recommended_message=(
                            f"היי {lead.customer_name}, יש לנו מסלול מתקדם שיכול לחסוך לך עוד זמן וכסף. לשלוח פרטים?"
                        ),
                    )
                )

        return findings

    def dashboard(self, leads: list[Lead], now: datetime | None = None) -> DashboardSummary:
        now = now or datetime.utcnow()
        findings = self.analyze(leads, now=now)
        by_severity_score = {"high": 3, "medium": 2, "low": 1}
        top_10 = sorted(findings, key=lambda f: by_severity_score[f.severity], reverse=True)[:10]

        weekly_revenue = sum(
            lead.quote_value_ils for lead in leads if lead.status == LeadStatus.won and now - lead.created_at <= timedelta(days=7)
        )

        almost_lost = sum(
            next((lead.quote_value_ils for lead in leads if lead.lead_id == f.lead_id), 0)
            for f in findings
            if f.severity in {"high", "medium"}
        )

        return DashboardSummary(
            weekly_revenue_ils=weekly_revenue,
            almost_lost_revenue_ils=almost_lost,
            top_10_to_contact=top_10,
            generated_at=now,
        )
