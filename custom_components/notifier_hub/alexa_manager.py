from __future__ import annotations

import asyncio
import re
from typing import Any

from homeassistant.core import HomeAssistant

from . import helpers as h

ALEXA_SERVICE = "alexa_media"
SUPPORTED_LANGUAGES = {
    "it-IT", "en-US", "en-CA", "en-AU", "en-GB", "en-IN", "fr-CA", "fr-FR",
    "de-DE", "hi-IN", "ja-JP", "pt-BR", "es-US", "es-ES", "es-MX",
}
VOICE_NAMES = {
    "Carla", "Giorgio", "Bianca", "Ivy", "Joanna", "Joey", "Justin", "Kendra",
    "Kimberly", "Matthew", "Salli", "Nicole", "Russell", "Amy", "Brian", "Emma",
    "Aditi", "Raveena", "Chantal", "Celine", "Lea", "Mathieu", "Hans", "Marlene",
    "Vicki", "Mizuki", "Takumi", "Vitoria", "Camila", "Ricardo", "Penelope",
    "Lupe", "Miguel", "Conchita", "Enrique", "Lucia", "Mia",
}
SPEECHCON_IT = ("ciao", "bravo", "auguri", "buongiorno", "buonasera", "buonanotte", "wow", "evviva")
SUB_VOICE = [
    (r"[\U00010000-\U0010ffff]", r""),
    (r"[\?\.\!,]+(?=[\?\.\!,])", r""),
    (r"(\s+\.|\s+\.\s+|[\.])(?! )(?![^{<]*[}>])(?![^\d.]*\d)", r". "),
    (r"&", r" and "),
    (r"[\n\*]", r" "),
    (r" +", r" "),
]


class AlexaManager:
    def __init__(self, hass: HomeAssistant, hub) -> None:
        self.hass = hass
        self.hub = hub
        self.queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue()
        self.volumes_saved: dict[str, float] = {}
        self.worker_task = hass.loop.create_task(self._worker())

    async def async_stop(self) -> None:
        self.worker_task.cancel()

    def _entity_exists(self, entity_id: str) -> bool:
        return self.hass.states.get(entity_id) is not None

    def _friendly_name_map(self) -> dict[str, str]:
        return {
            (state.attributes.get("friendly_name") or "").lower(): state.entity_id
            for state in self.hass.states.async_all()
            if state.attributes.get("friendly_name")
        }

    def _auto_alexa_players(self) -> list[str]:
        return [s.entity_id for s in self.hass.states.async_all("media_player") if "alexa" in s.entity_id.lower()]

    def _alexa_players_from_notify_services(self) -> list[str]:
        # La API pública de HA no lista servicios aquí de forma estable en todas las versiones.
        # Se usa la lista configurada y, si está vacía, todos los media_player con integración Alexa conocidos por nombre.
        configured = h.return_list(self.hub.config.get("alexa_players", []))
        if configured:
            resolved = self._resolve_players(configured, fallback=False)
            if resolved:
                return resolved
        return self._auto_alexa_players()

    def _resolve_players(self, raw_players: Any, fallback: bool = True) -> list[str]:
        players = h.return_list(raw_players)
        if not players or players == ["all"]:
            return self._alexa_players_from_notify_services() if fallback else self._auto_alexa_players()
        name2entity = self._friendly_name_map()
        resolved: list[str] = []
        for player in players:
            p = player.lower()
            if p == "test":
                resolved.extend(self._alexa_players_from_notify_services())
            elif p.startswith("group.") and self._entity_exists(p):
                resolved.extend(h.return_list(self.hass.states.get(p).attributes.get("entity_id", [])))
            elif p.startswith("sensor.") and self._entity_exists(p):
                resolved.extend(h.return_list(self.hass.states.get(p).state))
            elif p.startswith("media_player.") and self._entity_exists(p):
                resolved.append(p)
            elif p in name2entity:
                resolved.append(name2entity[p])
        if not resolved and fallback:
            resolved = self._alexa_players_from_notify_services()
        return sorted(set(resolved))

    @staticmethod
    def _in_between(minv: float, value: float, maxv: float) -> float:
        return sorted([minv, value, maxv])[1]

    def _language_tags(self, text: str, lang: str) -> str:
        return f"<lang xml:lang='{lang}'>{text}</lang>" if lang in SUPPORTED_LANGUAGES else text

    def _voice_tags(self, text: str, voice: str) -> str:
        return f"<voice name='{voice}'>{text}</voice>" if voice in VOICE_NAMES else text

    def _prosody_tags(self, text: str, rate: float, pitch: float, volume: float) -> str:
        if rate == 100.0 and pitch == 0.0 and volume == 0.0:
            return text
        r = f"{self._in_between(20, rate, 200)}%"
        p = f"{self._in_between(-33.3, pitch, 50):+g}%"
        v = f"{self._in_between(-50, volume, 4.08):+g}dB"
        return f"<prosody rate='{r}' pitch='{p}' volume='{v}'> {text} </prosody>"

    def _speechcon_tags(self, text: str) -> str:
        regex = re.compile(r"\b" + r"\b|\b".join(map(re.escape, sorted(SPEECHCON_IT, key=len, reverse=True))), re.I)
        return regex.sub(lambda m: f"<say-as interpret-as='interjection'>{m.group()}</say-as>", text)

    def _build_ssml(self, msg: str, data: dict[str, Any]) -> str:
        if not h.check_bool(data.get("ssml", False)) or "<speak>" in msg:
            return msg
        voice = str(data.get("voice", "Alexa")).capitalize()
        if voice == "Alexa" and not h.check_bool(data.get("whisper", False)):
            msg = self._speechcon_tags(msg)
        msg = self._language_tags(msg, str(data.get("language", self.hub.config.get("default_language", "es-ES"))))
        if voice != "Alexa":
            msg = self._voice_tags(msg, voice)
        if audio := data.get("audio"):
            msg = (audio if "<audio src=" in str(audio) else f"<audio src='{audio}'/>") + msg
        msg = self._prosody_tags(msg, float(data.get("rate", 100.0)), float(data.get("pitch", 0.0)), float(data.get("ssml_volume", 0.0)))
        if h.check_bool(data.get("whisper", False)):
            msg = f"<amazon:effect name='whispered'>{msg}</amazon:effect>"
        if data.get("type", "tts") == "tts" and "</" in msg:
            msg = f"<speak>{msg}</speak>"
        return msg

    async def speak(self, alexa: Any, base_data: dict[str, Any]) -> None:
        if alexa is True or str(alexa).lower() in {"true", "on", "yes", "1"}:
            alexa = {}
        if not isinstance(alexa, dict):
            return
        default_volume = float(self.hub.current_tts_volume())
        volume = float(alexa.get("volume", default_volume))
        auto_volumes = h.check_bool(alexa.get("auto_volumes", False))
        if volume == 0.0 and not auto_volumes:
            self.hub.set_debug("Alexa volume muted", {})
            return
        message = str(alexa.get("message_tts", alexa.get("message", base_data.get("message", ""))))
        media_player = self._resolve_players(alexa.get("media_player", self.hub.config.get("alexa_players", [])))
        if not media_player:
            self.hub.set_debug("Alexa media_player not found", {"alexa_error": "Configure alexa_players"})
            return

        if h.check_bool(alexa.get("push", False)) or str(alexa.get("type", "")).lower() in {"push", "dropin", "dropin_notification"}:
            await self.hass.services.async_call(
                "notify",
                ALEXA_SERVICE,
                {
                    "target": media_player[0],
                    "title": str(alexa.get("title", base_data.get("title", ""))),
                    "message": h.remove_tags(message),
                    "data": {"type": "push" if h.check_bool(alexa.get("push", False)) else alexa.get("type")},
                },
                blocking=False,
            )
            return

        if media_content_id := alexa.get("media_content_id"):
            await self._save_and_set_volume(media_player, volume, default_volume)
            await self.hass.services.async_call(
                "media_player",
                "play_media",
                {
                    "entity_id": media_player,
                    "media_content_id": media_content_id,
                    "media_content_type": alexa.get("media_content_type"),
                    "extra": {"timer": alexa.get("extra", 0)},
                },
                blocking=False,
            )
            return

        if message:
            await self.queue.put({**alexa, "message": message, "media_player": media_player, "volume": volume, "default_volume": default_volume})

    async def _save_and_set_volume(self, players: list[str], volume: float, default_volume: float) -> None:
        self.volumes_saved = {}
        for player in players:
            state = self.hass.states.get(player)
            old = state.attributes.get("volume_level") if state else None
            if old != volume:
                self.volumes_saved[player] = default_volume if old is None else float(old)
        if players:
            await self.hass.services.async_call("media_player", "volume_set", {"entity_id": players, "volume_level": volume}, blocking=False)

    async def _restore_volume(self) -> None:
        for player, volume in self.volumes_saved.items():
            await self.hass.services.async_call("media_player", "volume_set", {"entity_id": player, "volume_level": volume}, blocking=False)
            await asyncio.sleep(1)
        self.volumes_saved = {}

    async def _worker(self) -> None:
        while True:
            data = await self.queue.get()
            try:
                self.hub.set_alexa_speak(True, data)
                players = data["media_player"]
                volume = float(data["volume"])
                if h.check_bool(data.get("auto_volumes", False)):
                    await self.hass.services.async_call("media_player", "volume_set", {"entity_id": players, "volume_level": volume}, blocking=False)
                    continue
                await self._save_and_set_volume(players, volume, float(data["default_volume"]))
                msg = h.replace_regular(data.get("message", ""), SUB_VOICE)
                msg = self._build_ssml(msg, data)
                data_type = str(data.get("type", "tts")).lower().replace("dropin", "dropin_notification")
                alexa_data = {"type": data_type, "method": data.get("method", "all")} if data_type == "announce" else {"type": "tts"}
                await self.hass.services.async_call(
                    "notify",
                    str(data.get("notifier", ALEXA_SERVICE)),
                    {"message": msg.strip(), "target": players, "data": alexa_data},
                    blocking=False,
                )
                await asyncio.sleep(h.estimate_speech_duration(msg, float(data.get("wait_time", self.hub.config.get("tts_wait_time", 3.0)))))
                await self._restore_volume()
                self.hub.set_debug("OK", {})
            except Exception as err:  # noqa: BLE001
                self.hub.set_debug("Alexa Manager - Worker Error", {"alexa_error": str(err)})
            finally:
                self.hub.set_alexa_speak(False, {})
                self.queue.task_done()
