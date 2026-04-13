from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from .config import Settings


class OutboundConnector(Protocol):
    def send_message(self, destination: str, text: str) -> dict: ...


@dataclass(slots=True)
class WhatsAppConnector:
    settings: Settings

    def send_message(self, destination: str, text: str) -> dict:
        if not (self.settings.whatsapp_access_token and self.settings.whatsapp_phone_number_id):
            return {
                "ok": False,
                "provider": "whatsapp",
                "reason": "missing_credentials",
                "todo": "Set WHATSAPP_ACCESS_TOKEN and WHATSAPP_PHONE_NUMBER_ID",
            }

        # TODO(user): implement actual Meta WhatsApp Cloud API call here.
        return {
            "ok": False,
            "provider": "whatsapp",
            "reason": "not_implemented",
            "todo": "Replace stub with POST https://graph.facebook.com/vXX.X/{phone-number-id}/messages",
            "destination": destination,
            "preview": text[:80],
        }


@dataclass(slots=True)
class InstagramConnector:
    settings: Settings

    def send_message(self, destination: str, text: str) -> dict:
        if not (self.settings.instagram_access_token and self.settings.instagram_ig_user_id):
            return {
                "ok": False,
                "provider": "instagram",
                "reason": "missing_credentials",
                "todo": "Set INSTAGRAM_ACCESS_TOKEN and INSTAGRAM_IG_USER_ID",
            }

        # TODO(user): implement actual Instagram Messaging API call here.
        return {
            "ok": False,
            "provider": "instagram",
            "reason": "not_implemented",
            "todo": "Replace stub with Meta messaging endpoint",
            "destination": destination,
            "preview": text[:80],
        }


@dataclass(slots=True)
class EmailConnector:
    settings: Settings

    def send_message(self, destination: str, text: str) -> dict:
        if not (self.settings.smtp_host and self.settings.smtp_user and self.settings.smtp_password):
            return {
                "ok": False,
                "provider": "email",
                "reason": "missing_credentials",
                "todo": "Set SMTP_HOST, SMTP_USER, SMTP_PASSWORD",
            }

        # TODO(user): implement actual SMTP/email provider sending here.
        return {
            "ok": False,
            "provider": "email",
            "reason": "not_implemented",
            "todo": "Replace stub with SMTP send",
            "destination": destination,
            "preview": text[:80],
        }
