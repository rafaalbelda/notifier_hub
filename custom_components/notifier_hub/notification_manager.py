from __future__ import annotations

from datetime import datetime
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er

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

    def _notify_entity_id(self, raw: str, service: str) -> str | None:
        entity_id = raw.strip().lower()
        if not entity_id.startswith("notify."):
            return None
        if self.hass.services.has_service("notify", service):
            return None
        if self.hass.states.get(entity_id) is not None:
            return entity_id
        return entity_id if er.async_get(self.hass).async_get(entity_id) else None

    def _is_mobile_notify_target(self, service: str, notify_entity_id: str | None = None) -> bool:
        if "mobile" in service:
            return True
        if not notify_entity_id:
            return False
        entity_entry = er.async_get(self.hass).async_get(notify_entity_id)
        return entity_entry is not None and entity_entry.platform == "mobile_app"

    def _mobile_app_service_for_entity(self, service: str, notify_entity_id: str) -> str | None:
        notify_services = self.hass.services.async_services().get("notify", {})
        candidates = [
            service,
            f"mobile_app_{service}",
        ]

        entity_registry = er.async_get(self.hass)
        entity_entry = entity_registry.async_get(notify_entity_id)
        if entity_entry is not None:
            for name in (entity_entry.name, entity_entry.original_name):
                if name:
                    candidates.append(f"mobile_app_{h.service_name(name)}")
            if entity_entry.device_id:
                device_entry = dr.async_get(self.hass).async_get(entity_entry.device_id)
                if device_entry is not None:
                    for name in (device_entry.name_by_user, device_entry.name):
                        if name:
                            candidates.append(f"mobile_app_{h.service_name(name)}")

        for candidate in candidates:
            if candidate in notify_services:
                return candidate
        return None

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
        actions = data.get("actions", [])
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
            notify_entity_id = self._notify_entity_id(raw, service)
            payload: dict[str, Any] = {}
            prepared_message, prepared_title = self._prepare_text(html, message, title)

            if notify_entity_id:
                if link:
                    prepared_message = f"{prepared_message} {link}".strip()
                is_mobile_notify = self._is_mobile_notify_target(service, notify_entity_id)
                entity_data = {"message": prepared_message}
                if prepared_title:
                    entity_data["title"] = prepared_title
                if is_mobile_notify:
                    payload = dict(mobile) if isinstance(mobile, dict) else {}
                    if actions:
                        payload.setdefault("actions", actions)
                    if image:
                        payload["image"] = image.replace("config/www", "local")
                    if payload:
                        mobile_service = self._mobile_app_service_for_entity(service, notify_entity_id)
                        if mobile_service:
                            await self.hass.services.async_call(
                                "notify",
                                mobile_service,
                                {
                                    "message": prepared_message,
                                    "title": prepared_title,
                                    "data": payload,
                                },
                                blocking=False,
                            )
                            continue
                        self.hub.set_debug(
                            "mobile notify data ignored",
                            {
                                "notify_entity": notify_entity_id,
                                "reason": "notify.send_message does not accept data and no notify.mobile_app_* service was found",
                            },
                        )
                await self.hass.services.async_call(
                    "notify",
                    "send_message",
                    entity_data,
                    target={"entity_id": notify_entity_id},
                    blocking=False,
                )
                continue

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

            elif self._is_mobile_notify_target(service):
                prepared_title = f"[{self.hub.config.get('personal_assistant', 'Assistant')} - {datetime.now().strftime('%H:%M:%S')}] {title}"
                payload = dict(mobile) if isinstance(mobile, dict) else {}
                if actions:
                    payload.setdefault("actions", actions)
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
