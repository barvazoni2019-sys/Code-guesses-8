from app.config import Settings
from app.connectors import EmailConnector, InstagramConnector, WhatsAppConnector


def test_integration_status_defaults_false() -> None:
    s = Settings(
        whatsapp_access_token=None,
        whatsapp_phone_number_id=None,
        instagram_access_token=None,
        instagram_ig_user_id=None,
        crm_base_url=None,
        crm_api_key=None,
        smtp_host=None,
        smtp_user=None,
        smtp_password=None,
        openai_api_key=None,
    )
    status = s.integration_status()
    assert status == {
        "whatsapp": False,
        "instagram": False,
        "crm": False,
        "email": False,
        "llm": False,
    }


def test_connectors_return_missing_credentials_when_not_configured() -> None:
    s = Settings(
        whatsapp_access_token=None,
        whatsapp_phone_number_id=None,
        instagram_access_token=None,
        instagram_ig_user_id=None,
        smtp_host=None,
        smtp_user=None,
        smtp_password=None,
    )

    assert WhatsAppConnector(s).send_message("x", "hello")["reason"] == "missing_credentials"
    assert InstagramConnector(s).send_message("x", "hello")["reason"] == "missing_credentials"
    assert EmailConnector(s).send_message("x", "hello")["reason"] == "missing_credentials"
