# AI Revenue Copilot (MVP)

A local Python MVP for a small-business "Revenue Copilot" that:
- stores incoming leads,
- scores lead heat,
- suggests follow-up messages,
- tracks follow-up actions.

## Quick start

```bash
python -m unittest -v
```

## Service methods (`RevenueCopilotService`)

- `create_lead(...)`
- `list_leads(status=None)`
- `score_lead(lead_id)`
- `followup_lead(lead_id)`
- `add_event(lead_id, event)`
- `health()`

## Notes

This is intentionally lightweight and local-file backed (`data/leads.json`) so it's easy to iterate quickly before adding APIs/integrations.
