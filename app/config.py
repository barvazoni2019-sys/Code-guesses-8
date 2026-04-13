from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(slots=True)
class Settings:
    app_env: str = os.getenv("APP_ENV", "dev")
    app_port: int = int(os.getenv("APP_PORT", "8000"))

    # Integration placeholders (to be filled by user later)
    whatsapp_access_token: str | None = os.getenv("WHATSAPP_ACCESS_TOKEN")
    whatsapp_phone_number_id: str | None = os.getenv("WHATSAPP_PHONE_NUMBER_ID")

    instagram_access_token: str | None = os.getenv("INSTAGRAM_ACCESS_TOKEN")
    instagram_ig_user_id: str | None = os.getenv("INSTAGRAM_IG_USER_ID")

    crm_base_url: str | None = os.getenv("CRM_BASE_URL")
    crm_api_key: str | None = os.getenv("CRM_API_KEY")

    smtp_host: str | None = os.getenv("SMTP_HOST")
    smtp_user: str | None = os.getenv("SMTP_USER")
    smtp_password: str | None = os.getenv("SMTP_PASSWORD")

    openai_api_key: str | None = os.getenv("OPENAI_API_KEY")

    require_api_key: bool = os.getenv("REQUIRE_API_KEY", "false").lower() == "true"
    api_keys_raw: str = os.getenv("API_KEYS", "")
    api_key_roles_raw: str = os.getenv("API_KEY_ROLES", "")  # format: key1:admin,key2:agent
    rate_limit_per_minute: int = int(os.getenv("RATE_LIMIT_PER_MINUTE", "60"))

    def integration_status(self) -> dict[str, bool]:
        return {
            "whatsapp": bool(self.whatsapp_access_token and self.whatsapp_phone_number_id),
            "instagram": bool(self.instagram_access_token and self.instagram_ig_user_id),
            "crm": bool(self.crm_base_url and self.crm_api_key),
            "email": bool(self.smtp_host and self.smtp_user and self.smtp_password),
            "llm": bool(self.openai_api_key),
        }

    def api_keys(self) -> set[str]:
        if not self.api_keys_raw.strip():
            return set()
        return {key.strip() for key in self.api_keys_raw.split(",") if key.strip()}

    def api_key_roles(self) -> dict[str, str]:
        if not self.api_key_roles_raw.strip():
            return {}

        result: dict[str, str] = {}
        for pair in self.api_key_roles_raw.split(","):
            pair = pair.strip()
            if not pair or ":" not in pair:
                continue
            key, role = pair.split(":", 1)
            key = key.strip()
            role = role.strip().lower()
            if key and role:
                result[key] = role
        return result
