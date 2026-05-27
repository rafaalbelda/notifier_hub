from __future__ import annotations

from typing import Any
from urllib.parse import quote

from homeassistant.core import HomeAssistant

from . import helpers as h

SUB_TTS = [(r"[\*\-\[\]_\(\)\{\~\|\}\s]+", r" ")]
LANG_TO_VOICE = {
    "it-IT": "it-IT-Standard-A",
    "en-GB": "en-GB-Standard-A",
    "en-US": "en-US-Standard-A",
    "fr-FR": "fr-FR-Standard-A",
    "de-DE": "de-DE-Standard-A",
    "es-ES": "es-ES-Standard-A",
}


class PhoneManager:
    def __init__(self, hass: HomeAssistant, hub) -> None:
        self.hass = hass
        self.hub = hub

    async def send_voice_call(self, data: dict[str, Any]) -> None:
        message = h.replace_regular(data.get("message", ""), SUB_TTS)
        called_number = str(data.get("called_number") or self.hub.config.get("called_number", ""))
        if not called_number:
            return
        phone_name = str(data.get("phone_notify") or self.hub.config.get("phone_notify", "")).lower().replace(" ", "_")
        sip_server = self.hub.config.get("sip_server_name", "fritz.box:5060")
        if "voip_call" in phone_name:
            await self.hass.services.async_call(
                "hassio",
                "addon_stdin",
                {
                    "addon": "89275b70_dss_voip",
                    "input": {"call_sip_uri": f"sip:{called_number}@{sip_server}", "message_tts": message},
                },
                blocking=False,
            )
        else:
            lang = LANG_TO_VOICE.get(self.hub.config.get("default_language", "es-ES"), "es-ES-Standard-A")
            url = f"http://api.callmebot.com/start.php?source=HA&user={called_number}&text={quote(message)}&lang={lang}"
            await self.hass.services.async_call("shell_command", "telegram_call", {"url": url}, blocking=False)
