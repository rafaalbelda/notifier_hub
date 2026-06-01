from __future__ import annotations

from datetime import datetime
from typing import Any

from homeassistant.core import HomeAssistant

from . import helpers as h

SUB_NOWRAP = [(r"\s+", r" "), (r" +", r" ")]
SUB_WRAP = [(r" +", r" "), (r"\s\s+", r"\n")]


class NotificationManager:
    def __init__(self, hass: HomeAssistant, hub) -> None:
        self.hass = hass
        self.hub = hub
        self.buffer = ""

    def _prepare_text(self, html: bool, message: str, title: str) -> tuple[str, str]:
        timestamp = datetime.now().strftime("%H:%M:%S")
        assistant = self.hub.config.get("personal_assistant", "Assistant")
        if html:
            prepared_title = f"<b>[{assistant} - {timestamp}] {title}</b>"
        else:
            prepared_title = f"*[{assistant} - {timestamp}] {title}*"
        substitutions = SUB_WRAP if self.hub.config.get("wrap_text", False) else SUB_NOWRAP
        return h.replace_regular(message, substitutions), prepared_title

    async def send_persistent(self, data: dict[str, Any]) -> None:
        timestamp = datetime.now().strftime("%H:%M:%S")
        message = h.replace_regular(data.get("message", ""), SUB_WRAP if self.hub.config.get("wrap_text") else SUB_NOWRAP)
        line = f"{timestamp} - {message}"
        self.buffer = f"{self.buffer}\n{line}" if len(self.buffer) < 2500 else line
        await self.hass.services.async_call(
            "persistent_notification",
            "create",
            {
                "notification_id": "notifier_hub_info_messages",
                "title": self.hub.config.get("personal_assistant", "Notifier Hub"),
                "message": self.buffer,
            },
            blocking=False,
        )

    async def send_notify(self, data: dict[str, Any], notify_services: list[str]) -> None:
        message = str(data.get("message", ""))
        title = str(data.get("title", ""))
        html = h.check_bool(data.get("html", False))
        image = str(data.get("image", ""))
        link = str(data.get("link", ""))
        target = data.get("target", "")
        caption = str(data.get("caption", ""))
        priority = data.get("priority", "")
        mobile = data.get("mobile", "")
        telegram = data.get("telegram", "")
        pushover = data.get("pushover", "")
        discord = data.get("discord", "")

        self.hub.set_last_message(message[:245])

        for raw in notify_services:
            service = h.service_name(raw)
            if service in ["false", "off", "no", "0"]:
                continue
            payload: dict[str, Any] = {}
            prepared_message, prepared_title = self._prepare_text(html, message, title)

            if "telegram" in service:
                payload = dict(telegram) if isinstance(telegram, dict) else {}
                if link and image:
                    prepared_message = f"{prepared_message} {link}"
                if image:
                    key = "url" if image.startswith("http") else "file"
                    payload["photo"] = {key: image, "caption": caption or f"{prepared_title}\n{prepared_message}", "timeout": 90}
                    await self.hass.services.async_call("notify", service, {"message": "", "data": payload}, blocking=False)
                    continue
                if html:
                    payload["parse_mode"] = "html"
                elif prepared_message:
                    prepared_message = prepared_message.replace("_", r"\_")

            elif "pushover" in service:
                prepared_title = prepared_title.replace("*", "")
                payload = dict(pushover) if isinstance(pushover, dict) else {}
                if image:
                    payload["url" if image.startswith("http") else "attachment"] = image
                if priority != "":
                    payload["priority"] = priority

            elif "discord" in service:
                payload = dict(discord) if isinstance(discord, dict) else {}
                if "embed" in payload:
                    payload.update({"title": prepared_title.replace("*", ""), "description": prepared_message})
                    if link:
                        payload["url"] = link
                    if image:
                        payload["images"] = image.replace("config/www", "local")
                    prepared_message = ""

            elif "mobile" in service:
                prepared_title = f"[{self.hub.config.get('personal_assistant', 'Assistant')} - {datetime.now().strftime('%H:%M:%S')}] {title}"
                payload = dict(mobile) if isinstance(mobile, dict) else {}
                if payload.pop("tts", False):
                    payload["tts_text"] = f"{title} {message}".strip()
                    prepared_message = "TTS"
                if image:
                    payload["image"] = image.replace("config/www", "local")

            else:
                prepared_title = f"[{self.hub.config.get('personal_assistant', 'Assistant')} - {datetime.now().strftime('%H:%M:%S')}] {title}" if title else self.hub.config.get("personal_assistant", "Assistant")
                prepared_message = message

            if link:
                prepared_message = f"{prepared_message} {link}".strip()

            service_data: dict[str, Any] = {"message": prepared_message, "title": prepared_title}
            if payload:
                service_data["data"] = payload
            if target:
                service_data["target"] = h.return_list(target) if not isinstance(target, list) else target
            await self.hass.services.async_call("notify", service, service_data, blocking=False)
