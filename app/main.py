from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from .models import FollowUpResponse, Lead, LeadCreate, LeadEvent, LeadStatus, ScoreResponse
from .scoring import compute_heat_score, generate_follow_up_text
from .storage import load_leads, save_leads


class RevenueCopilotService:
    def health(self) -> dict:
        return {"status": "ok"}

    def create_lead(self, payload: LeadCreate) -> Lead:
        leads = load_leads()
        lead = Lead(id=str(uuid4()), **payload.__dict__)
        leads[lead.id] = lead
        save_leads(leads)
        return lead

    def list_leads(self, status: LeadStatus | None = None) -> list[Lead]:
        leads = load_leads()
        rows = list(leads.values())
        if status is not None:
            rows = [lead for lead in rows if lead.status == status]
        return sorted(rows, key=lambda l: l.created_at, reverse=True)

    def score_lead(self, lead_id: str) -> ScoreResponse:
        leads = load_leads()
        lead = leads.get(lead_id)
        if not lead:
            raise KeyError("Lead not found")

        lead.heat_score = compute_heat_score(lead)
        lead.updated_at = datetime.utcnow()
        leads[lead.id] = lead
        save_leads(leads)
        return ScoreResponse(lead_id=lead.id, heat_score=lead.heat_score)

    def followup_lead(self, lead_id: str) -> FollowUpResponse:
        leads = load_leads()
        lead = leads.get(lead_id)
        if not lead:
            raise KeyError("Lead not found")

        if lead.heat_score is None:
            lead.heat_score = compute_heat_score(lead)

        lead.follow_up_text = generate_follow_up_text(lead)
        lead.updated_at = datetime.utcnow()
        leads[lead.id] = lead
        save_leads(leads)
        return FollowUpResponse(lead_id=lead.id, follow_up_text=lead.follow_up_text)

    def add_event(self, lead_id: str, event: LeadEvent) -> Lead:
        leads = load_leads()
        lead = leads.get(lead_id)
        if not lead:
            raise KeyError("Lead not found")

        lead.events.append(event)
        lead.status = LeadStatus.CONTACTED
        lead.updated_at = datetime.utcnow()
        leads[lead.id] = lead
        save_leads(leads)
        return lead
