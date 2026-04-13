from datetime import datetime, timedelta

from app.automation import AutomationRunner, Outbox
from app.models import ActionTask


def test_automation_runner_sends_due_tasks(tmp_path) -> None:
    outbox = Outbox(path=str(tmp_path / "outbox.log"))
    runner = AutomationRunner(outbox=outbox)
    now = datetime(2026, 4, 13, 12, 0, 0)

    tasks = [
        ActionTask(
            lead_id="L1",
            customer_name="A",
            priority="p1",
            action="followup:no_response",
            scheduled_for=now - timedelta(minutes=1),
            draft_message="msg",
        ),
        ActionTask(
            lead_id="L2",
            customer_name="B",
            priority="p2",
            action="followup:quote_stuck",
            scheduled_for=now + timedelta(minutes=20),
            draft_message="msg",
        ),
    ]

    result = runner.run(tasks, now=now)

    assert result["sent"] == 1
    assert result["queued"] == 1
    assert (tmp_path / "outbox.log").exists()
