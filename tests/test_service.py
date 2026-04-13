import unittest

from app.main import RevenueCopilotService
from app.models import LeadCreate, LeadEvent, LeadStatus
from app.storage import DATA_FILE


class ServiceFlowTests(unittest.TestCase):
    def setUp(self):
        if DATA_FILE.exists():
            DATA_FILE.unlink()
        self.service = RevenueCopilotService()

    def tearDown(self):
        if DATA_FILE.exists():
            DATA_FILE.unlink()

    def test_health(self):
        self.assertEqual(self.service.health()["status"], "ok")

    def test_create_score_followup_flow(self):
        lead = self.service.create_lead(
            LeadCreate(
                name="Dana",
                business_type="clinic",
                monthly_budget_usd=1200,
                urgency=8,
                pain="Manual lead follow up is slow and urgent",
                channel="whatsapp",
            )
        )

        scored = self.service.score_lead(lead.id)
        self.assertGreaterEqual(scored.heat_score, 0)
        self.assertLessEqual(scored.heat_score, 100)

        followup = self.service.followup_lead(lead.id)
        self.assertIn("15 דקות", followup.follow_up_text)

        updated = self.service.add_event(lead.id, LeadEvent(type="message", note="sent first outreach"))
        self.assertEqual(updated.status, LeadStatus.CONTACTED)
        self.assertEqual(len(updated.events), 1)


if __name__ == "__main__":
    unittest.main()
