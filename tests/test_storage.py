from datetime import datetime

from app.models import Channel, Lead, LeadStatus
from app.storage import JsonLeadRepository


def test_storage_round_trip(tmp_path) -> None:
    repo = JsonLeadRepository(path=str(tmp_path / "leads.json"))
    leads = [
        Lead(
            lead_id="R1",
            customer_name="Tomer",
            channel=Channel.whatsapp,
            created_at=datetime(2026, 4, 1, 10, 0, 0),
            status=LeadStatus.new,
            quote_value_ils=1234,
        )
    ]

    repo.save(leads)
    loaded = repo.load()

    assert len(loaded) == 1
    assert loaded[0].lead_id == "R1"
    assert loaded[0].channel == Channel.whatsapp
