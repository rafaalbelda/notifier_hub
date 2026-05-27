from __future__ import annotations

from typing import Any

from homeassistant.core import HomeAssistant

from . import helpers as h
from .const import DEFAULT_HA_SIP_ADDON

SUB_TTS = [(r"[\*\-\[\]_\(\)\{\~\|\}\s]+", r" ")]


class PhoneManager:
    def __init__(self, hass: HomeAssistant, hub) -> None:
        self.hass = hass
        self.hub = hub

    async def send_voice_call(self, data: dict[str, Any]) -> None:
        message = h.replace_regular(data.get("message", ""), SUB_TTS)
        called_number = str(data.get("called_number") or self.hub.config.get("called_number", ""))
        if not called_number:
            return
        sip_server = self.hub.config.get("sip_server_name", "fritz.box:5060")
        await self.hass.services.async_call(
            "hassio",
            "addon_stdin",
            {
                "addon": DEFAULT_HA_SIP_ADDON,
                "input": {
                    "command": "dial",
                    "number": f"sip:{called_number}@{sip_server}",
                    "menu": {
                        "message": message,
                        "language": self.hub.config.get("default_language", "es-ES"),
                        "post_action": "hangup",
                    },
                },
            },
            blocking=False,
        )
