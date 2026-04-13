from __future__ import annotations

from .models import Lead


def compute_heat_score(lead: Lead) -> int:
    budget_points = min(int(lead.monthly_budget_usd // 100), 40)
    urgency_points = lead.urgency * 5

    pain_keywords = ["urgent", "lost", "slow", "manual", "no-shows", "late"]
    pain_points = 0
    lowered_pain = lead.pain.lower()
    for keyword in pain_keywords:
        if keyword in lowered_pain:
            pain_points += 6

    channel_bonus = 10 if lead.channel.lower() in {"whatsapp", "phone"} else 4

    score = budget_points + urgency_points + pain_points + channel_bonus
    return max(0, min(score, 100))


def generate_follow_up_text(lead: Lead) -> str:
    score = lead.heat_score if lead.heat_score is not None else compute_heat_score(lead)
    tone = "ישיר ומהיר" if score >= 70 else "ידידותי ומסביר"

    return (
        f"היי {lead.name}, ראיתי שהאתגר המרכזי שלך הוא: '{lead.pain}'. "
        f"אפשר להראות לך כבר השבוע תהליך קצר שחוסך זמן ומגדיל פניות. "
        f"אם מתאים, נקבע שיחה של 15 דקות? (טון: {tone})"
    )
