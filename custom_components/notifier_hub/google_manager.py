from __future__ import annotations

import asyncio
import logging
from typing import Any

from homeassistant.core import HomeAssistant

from . import helpers as h
from .const import (
    CONF_DEFAULT_LANGUAGE,
    CONF_GOOGLE_NOTIFY_SERVICE,
    CONF_GOOGLE_PLAYERS,
    CONF_GOOGLE_TTS_SERVICE,
    CONF_TTS_WAIT_TIME,
    DEFAULT_GOOGLE_NOTIFY_SERVICE,
    DEFAULT_GOOGLE_TTS_SERVICE,
)

_LOGGER = logging.getLogger(__name__)

GOOGLE_TRANSLATE_TLD_BY_LANGUAGE = {
    "en-us": "com",
    "en-gb": "co.uk",
    "en-uk": "co.uk",
    "en-au": "com.au",
    "en-ca": "ca",
    "en-in": "co.in",
    "en-ie": "ie",
    "en-za": "co.za",
    "fr-ca": "ca",
    "fr-fr": "fr",
    "pt": "pt",
    "pt-br": "com.br",
    "pt-pt": "pt",
    "es-es": "es",
    "es-us": "com",
}

SUB_VOICE = [
    (r"[\U00010000-\U0010ffff]", r""),
    (r"[\?\.\!,]+(?=[\?\.\!,])", r""),
    (r"(\s+\.|\s+\.\s+|[\.])(?! )(?![^{]*})(?![^\d.]*\d)", r". "),
    (r"<.*?>", r""),
    (r"&", r" and "),
    (r"[\n\*]", r" "),
    (r" +", r" "),
]


class GoogleManager:
    """Google/Cast TTS manager for the Notifier Hub native integration."""

    def __init__(self, hass: HomeAssistant, hub) -> None:
        self.hass = hass
        self.hub = hub
        self.queue: asyncio.Queue[dict[str, Any] | None] = asyncio.Queue()
        self.worker_task = hass.loop.create_task(self._worker())

    async def async_stop(self) -> None:
        await self.queue.put(None)
        self.worker_task.cancel()
        try:
            await self.worker_task
        except asyncio.CancelledError:
            pass

    def _as_google_dict(self, google: Any) -> dict[str, Any] | None:
        if google is True or str(google).lower() in h.TRUE_VALUES:
            return {}
        if not h.check_notify(google):
            return None
        if isinstance(google, dict):
            return dict(google)
        return {}

    def _players(self, value: Any) -> list[str]:
        players = h.return_list(value) or h.return_list(self.hub.config.get(CONF_GOOGLE_PLAYERS, []))
        resolved: list[str] = []
        for player in players:
            if player == "all" or player.startswith("media_player."):
                resolved.append(player)
            elif player.startswith("group."):
                state = self.hass.states.get(player)
                if state:
                    entities = state.attributes.get("entity_id", [])
                    resolved.extend([e for e in entities if str(e).startswith("media_player.")])
            else:
                match = self._entity_from_friendly_name(player)
                if match:
                    resolved.append(match)
        return sorted(set(resolved))

    def _entity_from_friendly_name(self, name: str) -> str | None:
        target = str(name).lower()
        for state in self.hass.states.async_all("media_player"):
            if str(state.attributes.get("friendly_name", "")).lower() == target:
                return state.entity_id
        return None

    async def speak(self, google: Any, parent_data: dict[str, Any]) -> None:
        google_data = self._as_google_dict(google)
        if google_data is None:
            return

        message = str(google_data.get("message", parent_data.get("message", "")))
        players = self._players(google_data.get("media_player", google_data.get("player", "")))
        notify_service = str(
            google_data.get(
                "notify_service",
                self.hub.config.get(CONF_GOOGLE_NOTIFY_SERVICE, DEFAULT_GOOGLE_NOTIFY_SERVICE),
            )
        )

        # Google Assistant notify mode, equivalent to the old GH "google assistant" mode.
        mode = str(google_data.get("mode", google_data.get("type", "tts"))).lower()
        if mode in {"google assistant", "assistant", "notify"}:
            await self._call_notify(notify_service, message)
            return

        media_content_id = str(google_data.get("media_content_id", ""))
        if media_content_id:
            if not players:
                self.hub.set_debug("Google Manager - players not found", {"google_error": "No media_player configured"})
                return
            await self.hass.services.async_call(
                "media_player",
                "play_media",
                {
                    "entity_id": players if len(players) > 1 else players[0],
                    "media_content_id": media_content_id,
                    "media_content_type": google_data.get("media_content_type", "music"),
                },
                blocking=False,
            )
            return

        if not message:
            return
        if not players:
            self.hub.set_debug("Google Manager - players not found", {"google_error": "No media_player configured"})
            return

        await self.queue.put(
            {
                "message": h.replace_regular(message, SUB_VOICE),
                "players": players,
                "volume": float(google_data.get("volume", self.hub.current_tts_volume())),
                "wait_time": float(google_data.get("wait_time", self.hub.config.get(CONF_TTS_WAIT_TIME, 3.0))),
                "language": str(google_data.get("language", self.hub.config.get(CONF_DEFAULT_LANGUAGE, "es-ES"))),
                "tts_entity": str(google_data.get("tts_entity", google_data.get("engine_id", ""))),
                "tts_service": str(
                    google_data.get(
                        "tts_service",
                        google_data.get(
                            "service",
                            self.hub.config.get(CONF_GOOGLE_TTS_SERVICE, DEFAULT_GOOGLE_TTS_SERVICE),
                        ),
                    )
                ),
            }
        )

    async def _call_notify(self, service: str, message: str) -> None:
        service = service.replace("notify.", "", 1)
        await self.hass.services.async_call("notify", service, {"message": message}, blocking=False)

    async def _worker(self) -> None:
        while True:
            data = await self.queue.get()
            if data is None:
                self.queue.task_done()
                return
            self.hub.set_google_speak(True, data)
            saved_volumes: dict[str, Any] = {}
            try:
                players = data["players"]
                for player in players:
                    state = self.hass.states.get(player)
                    if state is not None:
                        saved_volumes[player] = state.attributes.get("volume_level")
                await self.hass.services.async_call(
                    "media_player",
                    "volume_set",
                    {"entity_id": players, "volume_level": data["volume"]},
                    blocking=False,
                )

                await self._call_tts(data)

                await asyncio.sleep(h.estimate_speech_duration(data["message"], float(data["wait_time"])))
            except Exception as err:  # noqa: BLE001
                _LOGGER.exception("Google Manager error")
                self.hub.set_debug("Google Manager - Worker Error", {"google_error": str(err)})
            finally:
                for player, volume in saved_volumes.items():
                    if volume is not None:
                        await self.hass.services.async_call(
                            "media_player",
                            "volume_set",
                            {"entity_id": player, "volume_level": volume},
                            blocking=False,
                        )
                self.hub.set_google_speak(False, {})
                self.queue.task_done()

    def _split_service(self, service_name: str) -> tuple[str, str]:
        if "." in service_name:
            domain, service = service_name.split(".", 1)
            return domain, service
        return "tts", service_name

    async def _call_tts(self, data: dict[str, Any]) -> None:
        players = data["players"]
        language = str(data.get("language", ""))
        tts_entity = self._resolve_tts_entity(data.get("tts_service", ""), data.get("tts_entity", ""), language)
        if tts_entity:
            service_data: dict[str, Any] = {
                "media_player_entity_id": players if len(players) > 1 else players[0],
                "message": data["message"],
            }
            if language:
                service_data["language"] = language
            await self.hass.services.async_call(
                "tts",
                "speak",
                service_data,
                blocking=False,
                target={"entity_id": tts_entity},
            )
            return

        domain, service = self._split_service(str(data.get("tts_service", DEFAULT_GOOGLE_TTS_SERVICE)))
        service_data = {
            "entity_id": players if len(players) > 1 else players[0],
            "message": data["message"],
        }
        # Legacy tts.*_say services expect short language codes in many installations.
        if language:
            service_data["language"] = language[:2]
        await self.hass.services.async_call(domain, service, service_data, blocking=False)

    def _resolve_tts_entity(self, service_name: Any, explicit_entity: Any, language: str) -> str | None:
        entity_id = str(explicit_entity or "").strip()
        if entity_id and self._is_tts_entity(entity_id):
            return entity_id

        service = str(service_name or "").strip()
        if self._is_tts_entity(service):
            return service

        if service.replace("tts.", "", 1) in {"google_translate_say", "google_say"}:
            for candidate in self._google_translate_entity_candidates(language):
                if self._is_tts_entity(candidate):
                    return candidate

        return None

    def _is_tts_entity(self, entity_id: str) -> bool:
        return entity_id.startswith("tts.") and self.hass.states.get(entity_id) is not None

    def _google_translate_entity_candidates(self, language: str) -> list[str]:
        normalized = (language or "es-ES").lower().replace("_", "-")
        lang = normalized.split("-", 1)[0]
        tld = GOOGLE_TRANSLATE_TLD_BY_LANGUAGE.get(normalized)
        if tld is None and "-" in normalized:
            tld = normalized.split("-", 1)[1]
        if tld is None:
            tld = "com"

        suffix = f"{lang}_{tld.replace('.', '_').replace('-', '_')}"
        return [
            f"tts.google_{suffix}",
            f"tts.google_translate_{suffix}",
        ]
