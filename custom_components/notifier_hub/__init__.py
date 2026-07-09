from __future__ import annotations

import asyncio
import logging
import math
from pathlib import Path
import shutil
from datetime import time as dt_time, timedelta
from typing import Any
from uuid import uuid4

import voluptuous as vol
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_NAME, Platform
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.event import async_call_later, async_track_state_change_event, async_track_time_interval
from homeassistant.helpers.typing import ConfigType
from homeassistant.util import dt as dt_util

from . import helpers as h
from .alexa_manager import AlexaManager
from .google_manager import GoogleManager
from .const import (
    CONF_ALEXA_PLAYERS,
    CONF_GOOGLE_NOTIFY_SERVICE,
    CONF_GOOGLE_PLAYERS,
    CONF_GOOGLE_TTS_SERVICE,
    CONF_DEBUG,
    CONF_DEFAULT_LANGUAGE,
    CONF_DEFAULT_VOLUME,
    CONF_NOTIFY_SERVICES,
    CONF_PERSONAL_ASSISTANT,
    CONF_PERSONS,
    CONF_ALEXA_NOTIFICATIONS,
    CONF_GOOGLE_NOTIFICATIONS,
    CONF_HA_EVENT_NOTIFICATIONS,
    CONF_HA_EVENT_NOTIFY_SERVICES,
    CONF_AUTO_VOLUME,
    CONF_AUTO_VOLUME_CONTROL_PLAYERS,
    CONF_AUTO_VOLUME_EXCLUDE_PLAYERS,
    CONF_NIGHT_DND,
    CONF_INSTALL_DASHBOARD,
    CONF_DND_ENTITY,
    CONF_DND_MODE,
    CONF_GUEST_MODE,
    CONF_GUEST_MODE_ENTITY,
    CONF_PHONE_NOTIFICATIONS,
    CONF_PRIORITY_MESSAGE,
    CONF_PRIORITY_MESSAGE_ENTITY,
    CONF_SCREEN_NOTIFICATIONS,
    CONF_SPEECH_HOME_ONLY,
    CONF_SPEECH_NOTIFICATIONS,
    CONF_TEXT_NOTIFICATIONS,
    CONF_SIP_SERVER_NAME,
    CONF_TTS_WAIT_TIME,
    DASHBOARD_INSTALL_STRINGS,
    HA_EVENT_STRINGS,
    resolve_dashboard_language,
    normalize_locale,
    DEFAULT_LANGUAGE,
    DEFAULT_PERSONAL_ASSISTANT,
    DEFAULT_SIP_SERVER_NAME,
    DEFAULT_TTS_WAIT_TIME,
    DEFAULT_VOLUME,
    DEFAULT_GOOGLE_NOTIFY_SERVICE,
    DEFAULT_GOOGLE_TTS_SERVICE,
    DOMAIN,
    EVENT_CONFIRMATION,
    EVENT_NOTIFIER,
    SERVICE_SEND,
    SERVICE_SET_CONFIG,
    AUTO_VOLUME_PERIODS,
    DEFAULT_DND_ENTITY,
    DEFAULT_GUEST_MODE_ENTITY,
    DEFAULT_PRIORITY_MESSAGE_ENTITY,
    NIGHT_DND_PERIOD_KEYS,
    STATE_DASHBOARD_MESSAGE,
)
from .notification_manager import NotificationManager
from .phone_manager import PhoneManager

_LOGGER = logging.getLogger(__name__)
PLATFORMS = [
    Platform.SENSOR,
    Platform.BINARY_SENSOR,
    Platform.SWITCH,
    Platform.NUMBER,
    Platform.TIME,
    Platform.TEXT,
    Platform.BUTTON,
]

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            {
                vol.Optional(CONF_PERSONAL_ASSISTANT, default=DEFAULT_PERSONAL_ASSISTANT): cv.string,
                vol.Optional(CONF_PERSONS, default=[]): cv.ensure_list,
                vol.Optional(CONF_NOTIFY_SERVICES, default=[]): cv.ensure_list,
                vol.Optional(CONF_ALEXA_PLAYERS, default=[]): cv.ensure_list,
                vol.Optional(CONF_GOOGLE_PLAYERS, default=[]): cv.ensure_list,
                vol.Optional(CONF_GOOGLE_TTS_SERVICE, default=DEFAULT_GOOGLE_TTS_SERVICE): cv.string,
                vol.Optional(CONF_GOOGLE_NOTIFY_SERVICE, default=DEFAULT_GOOGLE_NOTIFY_SERVICE): cv.string,
                vol.Optional(CONF_SIP_SERVER_NAME, default=DEFAULT_SIP_SERVER_NAME): cv.string,
                vol.Optional(CONF_DEFAULT_LANGUAGE, default=DEFAULT_LANGUAGE): cv.string,
                vol.Optional(CONF_DEFAULT_VOLUME, default=DEFAULT_VOLUME): vol.Coerce(float),
                vol.Optional(CONF_TTS_WAIT_TIME, default=DEFAULT_TTS_WAIT_TIME): vol.Coerce(float),
                vol.Optional(CONF_DEBUG, default=False): cv.boolean,
                vol.Optional(CONF_TEXT_NOTIFICATIONS, default=True): cv.boolean,
                vol.Optional(CONF_SCREEN_NOTIFICATIONS, default=True): cv.boolean,
                vol.Optional(CONF_SPEECH_NOTIFICATIONS, default=True): cv.boolean,
                vol.Optional(CONF_SPEECH_HOME_ONLY, default=False): cv.boolean,
                vol.Optional(CONF_ALEXA_NOTIFICATIONS, default=True): cv.boolean,
                vol.Optional(CONF_GOOGLE_NOTIFICATIONS, default=True): cv.boolean,
                vol.Optional(CONF_PHONE_NOTIFICATIONS, default=False): cv.boolean,
                vol.Optional(CONF_HA_EVENT_NOTIFICATIONS, default=True): cv.boolean,
                vol.Optional(CONF_HA_EVENT_NOTIFY_SERVICES, default=[]): cv.ensure_list,
                vol.Optional(CONF_AUTO_VOLUME, default=False): cv.boolean,
                vol.Optional(CONF_AUTO_VOLUME_CONTROL_PLAYERS, default=True): cv.boolean,
                vol.Optional(CONF_AUTO_VOLUME_EXCLUDE_PLAYERS, default=[]): cv.ensure_list,
                vol.Optional(CONF_NIGHT_DND, default=False): cv.boolean,
                vol.Optional(CONF_INSTALL_DASHBOARD, default=True): cv.boolean,
                vol.Optional(CONF_DND_ENTITY, default=DEFAULT_DND_ENTITY): cv.string,
                vol.Optional(CONF_GUEST_MODE_ENTITY, default=DEFAULT_GUEST_MODE_ENTITY): cv.string,
                vol.Optional(CONF_PRIORITY_MESSAGE_ENTITY, default=DEFAULT_PRIORITY_MESSAGE_ENTITY): cv.string,
                vol.Optional("location_tracker", default=""): cv.string,
                vol.Optional("wrap_text", default=False): cv.boolean,
            },
            extra=vol.ALLOW_EXTRA,
        )
    },
    extra=vol.ALLOW_EXTRA,
)

SEND_SCHEMA = vol.Schema(
    {
        vol.Optional("title", default=""): cv.string,
        vol.Required("message"): cv.string,
        vol.Optional("notify", default=True): object,
        vol.Optional("no_show", default=False): object,
        vol.Optional("priority", default=False): object,
        vol.Optional("location", default=""): cv.string,
        vol.Optional("alexa", default=False): object,
        vol.Optional("google", default=False): object,
        vol.Optional("phone", default=False): object,
        vol.Optional("called_number", default=""): cv.string,
        vol.Optional("target", default=""): object,
        vol.Optional("image", default=""): cv.string,
        vol.Optional("actions", default=[]): [dict],
        vol.Optional("confirmation", default=False): object,
        vol.Optional("caption", default=""): cv.string,
        vol.Optional("link", default=""): cv.string,
        vol.Optional("html", default=False): object,
        vol.Optional("telegram", default=""): object,
        vol.Optional("pushover", default=""): object,
        vol.Optional("mobile", default=""): object,
        vol.Optional("discord", default=""): object,
    },
    extra=vol.ALLOW_EXTRA,
)

SET_CONFIG_SCHEMA = vol.Schema(
    {
        vol.Optional("config", default={}): dict,
        vol.Optional(CONF_AUTO_VOLUME): cv.boolean,
        vol.Optional(CONF_AUTO_VOLUME_CONTROL_PLAYERS): cv.boolean,
    },
    extra=vol.ALLOW_EXTRA,
)


def _copy_dashboard_if_changed(source: Path, target: Path, force: bool = False) -> bool:
    source_bytes = source.read_bytes()
    if not force and target.exists() and target.read_bytes() == source_bytes:
        return False
    shutil.copyfile(source, target)
    return True


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    if DOMAIN in config:
        hass.async_create_task(
            hass.config_entries.flow.async_init(DOMAIN, context={"source": "import"}, data=dict(config[DOMAIN]))
        )
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    hub = NotifierHub(hass, entry)
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = hub
    await hub.async_setup()
    entry.async_on_unload(entry.add_update_listener(async_update_entry))
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_update_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    hub: NotifierHub | None = hass.data.get(DOMAIN, {}).get(entry.entry_id)
    if hub is None:
        return
    await hub.async_update_config()


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    hub: NotifierHub = hass.data[DOMAIN].pop(entry.entry_id)
    await hub.async_unload()
    return unload_ok


class NotifierHub:
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.hass = hass
        self.entry = entry
        self.config: dict[str, Any] = self._merged_config()
        self.state: dict[str, Any] = {
            "debug": "off",
            "debug_attributes": {},
            "last_message": "",
            "confirmation": "idle",
            "confirmation_attributes": {},
            "pending_confirmations": 0,
            "pending_confirmation_attributes": {"confirmations": []},
            "alexa_speak": False,
            "alexa_attributes": {},
            "google_speak": False,
            "google_attributes": {},
            "day_period": "",
            "day_period_key": "",
            "day_period_volume": 0,
            "day_period_volume_level": 0.0,
            STATE_DASHBOARD_MESSAGE: "",
        }
        self.entities: list[Any] = []
        self.notification_manager = NotificationManager(hass, self)
        self.phone_manager = PhoneManager(hass, self)
        self.alexa_manager = AlexaManager(hass, self)
        self.google_manager = GoogleManager(hass, self)
        self._remove_listener = None
        self._remove_ha_event_listeners: list[Any] = []
        self._remove_auto_volume_listener = None
        self._remove_presence_listener = None
        self._remove_confirmation_listener = None
        self._confirmation_timeouts: dict[str, Any] = {}
        self._confirmations: dict[str, dict[str, Any]] = {}

    def _merged_config(self) -> dict[str, Any]:
        data = dict(self.entry.data)
        data.update(dict(self.entry.options))
        data.setdefault(CONF_PERSONAL_ASSISTANT, DEFAULT_PERSONAL_ASSISTANT)
        data.setdefault(CONF_PERSONS, [])
        data.setdefault(CONF_NOTIFY_SERVICES, [])
        data.setdefault(CONF_ALEXA_PLAYERS, [])
        data.setdefault(CONF_GOOGLE_PLAYERS, [])
        data.setdefault(CONF_GOOGLE_TTS_SERVICE, DEFAULT_GOOGLE_TTS_SERVICE)
        data.setdefault(CONF_GOOGLE_NOTIFY_SERVICE, DEFAULT_GOOGLE_NOTIFY_SERVICE)
        data.setdefault(CONF_SIP_SERVER_NAME, DEFAULT_SIP_SERVER_NAME)
        data.setdefault(CONF_DEFAULT_LANGUAGE, DEFAULT_LANGUAGE)
        data.setdefault(CONF_DEFAULT_VOLUME, DEFAULT_VOLUME)
        data.setdefault(CONF_TTS_WAIT_TIME, DEFAULT_TTS_WAIT_TIME)
        data.setdefault(CONF_TEXT_NOTIFICATIONS, True)
        data.setdefault(CONF_SCREEN_NOTIFICATIONS, True)
        data.setdefault(CONF_SPEECH_NOTIFICATIONS, True)
        data.setdefault(CONF_SPEECH_HOME_ONLY, False)
        data.setdefault(CONF_ALEXA_NOTIFICATIONS, True)
        data.setdefault(CONF_GOOGLE_NOTIFICATIONS, True)
        data.setdefault(CONF_PHONE_NOTIFICATIONS, False)
        data.setdefault(CONF_HA_EVENT_NOTIFICATIONS, True)
        data.setdefault(CONF_HA_EVENT_NOTIFY_SERVICES, [])
        data.setdefault(CONF_AUTO_VOLUME, False)
        data.setdefault(CONF_AUTO_VOLUME_CONTROL_PLAYERS, True)
        data.setdefault(CONF_AUTO_VOLUME_EXCLUDE_PLAYERS, [])
        data.setdefault(CONF_NIGHT_DND, False)
        data.setdefault(CONF_INSTALL_DASHBOARD, True)
        data.setdefault(CONF_DND_ENTITY, DEFAULT_DND_ENTITY)
        data.setdefault(CONF_GUEST_MODE_ENTITY, DEFAULT_GUEST_MODE_ENTITY)
        data.setdefault(CONF_PRIORITY_MESSAGE_ENTITY, DEFAULT_PRIORITY_MESSAGE_ENTITY)
        legacy_entities = {
            CONF_DND_ENTITY: ("input_boolean.notifier_dnd", DEFAULT_DND_ENTITY),
            CONF_GUEST_MODE_ENTITY: ("input_boolean.notifier_guest_mode", DEFAULT_GUEST_MODE_ENTITY),
            CONF_PRIORITY_MESSAGE_ENTITY: ("input_boolean.notifier_priority_message", DEFAULT_PRIORITY_MESSAGE_ENTITY),
        }
        for key, (legacy_entity, default_entity) in legacy_entities.items():
            if data.get(key) in ("", legacy_entity):
                data[key] = default_entity
        data.setdefault(CONF_DND_MODE, False)
        data.setdefault(CONF_GUEST_MODE, False)
        data.setdefault(CONF_PRIORITY_MESSAGE, False)
        for key, (_, default_time, default_volume) in AUTO_VOLUME_PERIODS.items():
            data.setdefault(f"auto_volume_{key}_time", default_time)
            data.setdefault(f"auto_volume_{key}_volume", default_volume)
        return data

    async def async_setup(self) -> None:
        self._update_auto_volume_state()
        await self.async_install_dashboard()
        self.hass.services.async_register(DOMAIN, SERVICE_SEND, self._handle_send, schema=SEND_SCHEMA)
        self.hass.services.async_register(DOMAIN, SERVICE_SET_CONFIG, self._handle_set_config, schema=SET_CONFIG_SCHEMA)
        self._remove_listener = self.hass.bus.async_listen(EVENT_NOTIFIER, self._handle_notifier_event)
        self._remove_confirmation_listener = self.hass.bus.async_listen(
            "mobile_app_notification_action",
            self._handle_confirmation_action,
        )
        self._remove_ha_event_listeners = [
            self.hass.bus.async_listen("homeassistant_started", self._handle_ha_started),
            self.hass.bus.async_listen("homeassistant_stop", self._handle_ha_stop),
            self.hass.bus.async_listen("homeassistant_final_write", self._handle_ha_final_write),
            self.hass.bus.async_listen("homeassistant_close", self._handle_ha_close),
            self.hass.bus.async_listen("call_service", self._handle_ha_call_service),
        ]
        self._remove_auto_volume_listener = async_track_time_interval(
            self.hass,
            self._handle_auto_volume_interval,
            timedelta(minutes=5),
        )
        self._async_update_presence_listener()
        self.set_debug("on", {})
        await self.async_apply_auto_volume()

    def _resolve_language(self, strings: dict[str, dict[str, str]]) -> dict[str, str]:
        # Use the same normalized locale matching as the dashboard resolver so
        # pt_BR / PT-br / pt-PT all resolve consistently instead of falling to en.
        normalized = normalize_locale(self.hass.config.language)
        for key in strings:
            if normalize_locale(key) == normalized:
                return strings[key]
        primary = normalized.split("-")[0]
        for key in strings:
            if normalize_locale(key).split("-")[0] == primary:
                return strings[key]
        return strings.get("en", {})

    async def async_install_dashboard(self, force: bool = False) -> None:
        if not self.config.get(CONF_INSTALL_DASHBOARD, True):
            return
        language = resolve_dashboard_language(self.hass.config.language)
        source = Path(__file__).with_name(f"notifier_hub_dashboard.{language}.yaml")
        if not source.exists():
            _LOGGER.warning("Notifier Hub dashboard source not found: %s", source)
            return
        target = Path(self.hass.config.path("notifier_hub_dashboard.yaml"))
        copied = await self.hass.async_add_executor_job(_copy_dashboard_if_changed, source, target, force)
        if not copied:
            return
        await self.hass.services.async_call(
            "persistent_notification",
            "create",
            {
                "notification_id": "notifier_hub_dashboard_install",
                "title": self._resolve_language(DASHBOARD_INSTALL_STRINGS).get("title", ""),
                "message": self._resolve_language(DASHBOARD_INSTALL_STRINGS).get("message", ""),
            },
            blocking=False,
        )

    async def async_unload(self) -> None:
        if self._remove_listener:
            self._remove_listener()
        for remove_listener in self._remove_ha_event_listeners:
            remove_listener()
        self._remove_ha_event_listeners = []
        if self._remove_auto_volume_listener:
            self._remove_auto_volume_listener()
            self._remove_auto_volume_listener = None
        if self._remove_presence_listener:
            self._remove_presence_listener()
            self._remove_presence_listener = None
        if self._remove_confirmation_listener:
            self._remove_confirmation_listener()
            self._remove_confirmation_listener = None
        for cancel_timeout in self._confirmation_timeouts.values():
            cancel_timeout()
        self._confirmation_timeouts.clear()
        if self.hass.services.has_service(DOMAIN, SERVICE_SEND):
            self.hass.services.async_remove(DOMAIN, SERVICE_SEND)
        if self.hass.services.has_service(DOMAIN, SERVICE_SET_CONFIG):
            self.hass.services.async_remove(DOMAIN, SERVICE_SET_CONFIG)
        await self.alexa_manager.async_stop()
        await self.google_manager.async_stop()

    def register_entities(self, entities: list[Any]) -> None:
        self.entities.extend(entities)

    def _refresh_entities(self) -> None:
        for entity in list(self.entities):
            if entity.hass is not None:
                entity.async_write_ha_state()

    def presence_summary(self) -> dict[str, Any]:
        persons = h.return_list(self.config.get(CONF_PERSONS, []))
        summary: dict[str, Any] = {
            "total_count": len(persons),
            "home_count": 0,
            "away_count": 0,
            "home_persons": [],
            "home_person_names": [],
            "home_person_details": [],
            "away_persons": [],
            "away_person_names": [],
            "away_person_details": [],
            "persons": [],
        }
        for entity_id in persons:
            state = self.hass.states.get(entity_id)
            value = state.state if state is not None else "unknown"
            name = state.name if state is not None else entity_id
            item = {
                "entity_id": entity_id,
                "name": name,
                "state": value,
            }
            summary["persons"].append(item)
            if value == "home":
                summary["home_count"] += 1
                summary["home_persons"].append(entity_id)
                summary["home_person_names"].append(name)
                summary["home_person_details"].append(item)
            else:
                summary["away_count"] += 1
                summary["away_persons"].append(entity_id)
                summary["away_person_names"].append(name)
                summary["away_person_details"].append(item)
        summary["is_home"] = summary["home_count"] > 0
        return summary

    def _async_update_presence_listener(self) -> None:
        if self._remove_presence_listener:
            self._remove_presence_listener()
            self._remove_presence_listener = None
        persons = h.return_list(self.config.get(CONF_PERSONS, []))
        if not persons:
            return
        self._remove_presence_listener = async_track_state_change_event(
            self.hass,
            persons,
            self._handle_presence_change,
        )

    async def _handle_presence_change(self, event) -> None:
        self._refresh_entities()

    def set_debug(self, state: str, attributes: dict[str, Any]) -> None:
        if self.hass.config.language.startswith("es"):
            state = {
                "config options updated": "opciones de configuracion actualizadas",
            }.get(state, state)
        self.state["debug"] = state
        self.state["debug_attributes"] = attributes
        self._refresh_entities()

    def set_last_message(self, message: str) -> None:
        self.state["last_message"] = message
        self._refresh_entities()

    def set_dashboard_message(self, message: str) -> None:
        self.state[STATE_DASHBOARD_MESSAGE] = message
        self._refresh_entities()

    async def async_send_dashboard_message(self) -> None:
        message = str(self.state.get(STATE_DASHBOARD_MESSAGE, "")).strip()
        if not message:
            self.set_debug("dashboard message empty", {})
            return
        await self.dispatch(
            {
                "title": "Dashboard",
                "message": message,
                "notify": True,
                "alexa": True,
                "google": True,
                "phone": True,
            }
        )

    def set_alexa_speak(self, is_on: bool, attributes: dict[str, Any]) -> None:
        self.state["alexa_speak"] = is_on
        self.state["alexa_attributes"] = attributes
        self._refresh_entities()

    def set_google_speak(self, is_on: bool, attributes: dict[str, Any]) -> None:
        self.state["google_speak"] = is_on
        self.state["google_attributes"] = attributes
        self._refresh_entities()

    def _parse_time(self, value: Any, fallback: str) -> dt_time:
        try:
            parts = [int(part) for part in str(value).split(":")[:3]]
            parts += [0] * (3 - len(parts))
            return dt_time(parts[0], parts[1], parts[2])
        except (TypeError, ValueError):
            hour, minute, second = [int(part) for part in fallback.split(":")]
            return dt_time(hour, minute, second)

    def _current_auto_volume(self) -> tuple[str, str, int, float]:
        now_time = dt_util.now().time()
        configured = []
        for key, (label, default_time, default_volume) in AUTO_VOLUME_PERIODS.items():
            start = self._parse_time(self.config.get(f"auto_volume_{key}_time"), default_time)
            volume = int(float(self.config.get(f"auto_volume_{key}_volume", default_volume)))
            configured.append((start, key, label, max(0, min(100, volume))))
        configured.sort(key=lambda item: item[0])
        current = configured[-1]
        for item in configured:
            if item[0] <= now_time:
                current = item
        _, key, label, volume = current
        return key, label, volume, volume / 100

    def _update_auto_volume_state(self) -> None:
        period_key, period, volume, volume_level = self._current_auto_volume()
        self.state["day_period_key"] = period_key
        self.state["day_period"] = period
        self.state["day_period_volume"] = volume
        self.state["day_period_volume_level"] = volume_level

    def _night_dnd_active(self) -> bool:
        if not self.config.get(CONF_NIGHT_DND, False):
            return False
        self._update_auto_volume_state()
        return self.state.get("day_period_key") in NIGHT_DND_PERIOD_KEYS

    def current_tts_volume(self) -> float:
        self._update_auto_volume_state()
        if self.config.get(CONF_AUTO_VOLUME, False):
            return float(self.state["day_period_volume_level"])
        return float(self.config.get(CONF_DEFAULT_VOLUME, DEFAULT_VOLUME))

    def auto_volume_players(self) -> list[str]:
        players = self.alexa_manager._resolve_players(self.config.get(CONF_ALEXA_PLAYERS, []))
        players.extend(self.google_manager._players(self.config.get(CONF_GOOGLE_PLAYERS, [])))
        excluded = set(h.return_list(self.config.get(CONF_AUTO_VOLUME_EXCLUDE_PLAYERS, [])))
        return sorted({player for player in players if player.startswith("media_player.") and player not in excluded})

    async def async_apply_auto_volume(self) -> None:
        self._update_auto_volume_state()
        self._refresh_entities()
        if not self.config.get(CONF_AUTO_VOLUME, False):
            return
        if not self.config.get(CONF_AUTO_VOLUME_CONTROL_PLAYERS, True):
            self.set_debug(
                "auto volume message only",
                {
                    "period": self.state["day_period"],
                    "volume": self.state["day_period_volume"],
                    "volume_level": self.state["day_period_volume_level"],
                },
            )
            return
        players = self.auto_volume_players()
        if not players:
            self.set_debug(
                "auto volume players not found",
                {
                    "period": self.state["day_period"],
                    "volume": self.state["day_period_volume"],
                    "alexa_players": h.return_list(self.config.get(CONF_ALEXA_PLAYERS, [])),
                    "google_players": h.return_list(self.config.get(CONF_GOOGLE_PLAYERS, [])),
                    "excluded_players": h.return_list(self.config.get(CONF_AUTO_VOLUME_EXCLUDE_PLAYERS, [])),
                },
            )
            return
        await self.hass.services.async_call(
            "media_player",
            "volume_set",
            {"entity_id": players, "volume_level": self.state["day_period_volume_level"]},
            blocking=False,
        )
        self.set_debug(
            "auto volume applied",
            {
                "period": self.state["day_period"],
                "volume": self.state["day_period_volume"],
                "volume_level": self.state["day_period_volume_level"],
                "players": players,
            },
        )

    async def _handle_auto_volume_interval(self, now) -> None:
        await self.async_apply_auto_volume()

    async def _handle_set_config(self, call: ServiceCall) -> None:
        updates = dict(call.data.get("config") or {})
        if CONF_AUTO_VOLUME in call.data:
            updates[CONF_AUTO_VOLUME] = call.data[CONF_AUTO_VOLUME]
        if CONF_AUTO_VOLUME_CONTROL_PLAYERS in call.data:
            updates[CONF_AUTO_VOLUME_CONTROL_PLAYERS] = call.data[CONF_AUTO_VOLUME_CONTROL_PLAYERS]
        self.config.update(updates)
        self._async_update_presence_listener()
        self._refresh_entities()
        await self.async_install_dashboard(force=True)
        await self.async_apply_auto_volume()
        self.set_debug("config updated", {"config_keys": sorted(updates.keys())})

    async def async_update_config(self) -> None:
        self.config = self._merged_config()
        self._async_update_presence_listener()
        self._refresh_entities()
        await self.async_install_dashboard(force=True)
        await self.async_apply_auto_volume()
        self.set_debug("config options updated", {"config_keys": sorted(self.config.keys())})

    async def _handle_notifier_event(self, event) -> None:
        data = dict(event.data or {})
        if isinstance(data.get("ad"), dict):
            # AppDaemon command compatibility. In a native integration no restart_app exists.
            self.set_debug("ad command ignored", {"command": data["ad"].get("command")})
            return
        await self.dispatch(data)

    def _confirmation_title(self) -> str:
        language = normalize_locale(self.hass.config.language).split("-")[0]
        return {
            "es": "Confirmar",
            "pt": "Confirmar",
        }.get(language, "Confirm")

    def _is_mobile_notify_service(self, raw: str) -> bool:
        service = h.service_name(raw)
        if "mobile" in service:
            return True
        entity_id = raw.strip().lower()
        if not entity_id.startswith("notify."):
            return False
        if self.hass.services.has_service("notify", service):
            return False
        entity_entry = er.async_get(self.hass).async_get(entity_id)
        return entity_entry is not None and entity_entry.platform == "mobile_app"

    def _set_confirmation_state(self, record: dict[str, Any]) -> None:
        self.state["confirmation"] = record["status"]
        self.state["confirmation_attributes"] = {
            key: value for key, value in record.items() if key != "status"
        }
        pending = [
            dict(confirmation)
            for confirmation in self._confirmations.values()
            if confirmation["status"] == "pending"
        ]
        self.state["pending_confirmations"] = len(pending)
        self.state["pending_confirmation_attributes"] = {
            "confirmations": pending,
        }
        self._refresh_entities()

    def _prepare_confirmation(self, data: dict[str, Any]) -> None:
        confirmation = data.get("confirmation", False)
        if not isinstance(confirmation, dict) and (
            confirmation in (None, "") or not h.check_notify(confirmation)
        ):
            return

        options = dict(confirmation) if isinstance(confirmation, dict) else {}
        confirmation_id = str(options.get("id") or uuid4().hex)
        if options.get("id") and h.check_bool(options.get("random_id", False)):
            confirmation_id = f"{confirmation_id}_{uuid4().hex[:8]}"
        action_id = str(options.get("action") or f"NOTIFIER_HUB_CONFIRM_{confirmation_id}")
        button_title = str(options.get("title") or self._confirmation_title())
        try:
            timeout = max(0.0, float(options.get("timeout", 300)))
        except (TypeError, ValueError):
            timeout = 300.0
        if not math.isfinite(timeout):
            timeout = 300.0

        action = {"action": action_id, "title": button_title}
        mobile = data.get("mobile")
        if isinstance(mobile, dict) and "actions" in mobile:
            mobile = dict(mobile)
            existing_actions = mobile.get("actions")
            if not isinstance(existing_actions, (list, tuple)):
                existing_actions = []
            mobile["actions"] = [*existing_actions, action]
            data["mobile"] = mobile
        else:
            data["actions"] = [*data.get("actions", []), action]

        created_at = dt_util.utcnow()
        record = {
            "status": "pending",
            "id": confirmation_id,
            "action": action_id,
            "button_title": button_title,
            "title": str(data.get("title", "")),
            "message": str(data.get("message", "")),
            "created_at": created_at.isoformat(),
            "expires_at": (created_at + timedelta(seconds=timeout)).isoformat() if timeout else None,
            "confirmed_at": None,
            "confirmed_by": None,
            "user_id": None,
            "device_id": None,
        }
        previous_timeout = self._confirmation_timeouts.pop(action_id, None)
        if previous_timeout:
            previous_timeout()
        if len(self._confirmations) >= 100:
            for old_action, old_record in list(self._confirmations.items()):
                if old_record["status"] != "pending":
                    self._confirmations.pop(old_action, None)
                if len(self._confirmations) < 100:
                    break
        self._confirmations[action_id] = record
        self._set_confirmation_state(record)
        if timeout:
            self._confirmation_timeouts[action_id] = async_call_later(
                self.hass,
                timeout,
                lambda _now: self.hass.async_create_task(self._expire_confirmation(action_id)),
            )

    async def _expire_confirmation(self, action_id: str) -> None:
        self._confirmation_timeouts.pop(action_id, None)
        record = self._confirmations.get(action_id)
        if record is None or record["status"] != "pending":
            return
        record["status"] = "expired"
        self._set_confirmation_state(record)
        self.hass.bus.async_fire(EVENT_CONFIRMATION, dict(record))

    async def _handle_confirmation_action(self, event) -> None:
        action_id = str((event.data or {}).get("action", ""))
        record = self._confirmations.get(action_id)
        if record is None or record["status"] != "pending":
            return

        cancel_timeout = self._confirmation_timeouts.pop(action_id, None)
        if cancel_timeout:
            cancel_timeout()
        user_id = event.context.user_id
        user = await self.hass.auth.async_get_user(user_id) if user_id else None
        device_id = (event.data or {}).get("device_id") or (event.data or {}).get("sourceDeviceID")
        record.update(
            {
                "status": "confirmed",
                "confirmed_at": dt_util.utcnow().isoformat(),
                "confirmed_by": user.name if user else device_id or user_id or "unknown",
                "user_id": user_id,
                "device_id": device_id,
            }
        )
        self._set_confirmation_state(record)
        self.hass.bus.async_fire(EVENT_CONFIRMATION, dict(record))

    def _ha_event_message(self, key: str) -> str:
        return self._resolve_language(HA_EVENT_STRINGS).get(key, "")

    async def _handle_ha_started(self, event) -> None:
        await self._send_ha_event_notification("HomeAssistant Start!", self._ha_event_message("started"))

    async def _handle_ha_stop(self, event) -> None:
        await self._send_ha_event_notification("HomeAssistant Stop!", self._ha_event_message("stop"))

    async def _handle_ha_final_write(self, event) -> None:
        await self._send_ha_event_notification("HomeAssistant Final Write!", self._ha_event_message("final_write"))

    async def _handle_ha_close(self, event) -> None:
        await self._send_ha_event_notification("HomeAssistant Close!", self._ha_event_message("close"))

    async def _handle_ha_call_service(self, event) -> None:
        data = event.data or {}
        if data.get("domain") != "homeassistant":
            return
        service = data.get("service", data.get("action", ""))
        if service == "restart":
            await self._send_ha_event_notification("HomeAssistant Restart!", self._ha_event_message("restart"))

    async def _send_ha_event_notification(self, title: str, message: str) -> None:
        if not self.config.get(CONF_HA_EVENT_NOTIFICATIONS, True):
            return
        notify_services = h.return_list(self.config.get(CONF_HA_EVENT_NOTIFY_SERVICES, []))
        if not notify_services:
            notify_services = h.return_list(self.config.get(CONF_NOTIFY_SERVICES, [])) or ["persistent_notification"]
        await self.notification_manager.send_notify(
            {
                "title": title,
                "message": message,
                "notify": notify_services,
                "priority": False,
                "html": False,
            },
            notify_services,
        )

    async def _handle_send(self, call: ServiceCall) -> None:
        await self.dispatch(dict(call.data))

    def _state_is_on(self, entity_id: str) -> bool:
        if not entity_id:
            return False
        state = self.hass.states.get(entity_id)
        return state is not None and state.state == "on"

    def _state_value(self, entity_id: str, default: str = "") -> str:
        if not entity_id:
            return default
        state = self.hass.states.get(entity_id)
        return state.state if state is not None else default

    def _check_location(self, requested: str) -> bool:
        if not requested:
            return True
        persons = h.return_list(self.config.get(CONF_PERSONS, []))
        if persons:
            requested_location = requested.lower()
            return any(self._state_value(person, "").lower() == requested_location for person in persons)
        tracker = self.config.get("location_tracker", "")
        if not tracker:
            return True
        return requested.lower() == self._state_value(tracker, "home").lower()

    async def dispatch(self, data: dict[str, Any]) -> None:
        data.setdefault("title", "")
        data.setdefault("message", "")
        data.setdefault("notify", True)
        data.setdefault("priority", False)
        data.setdefault("no_show", False)
        data.setdefault("alexa", False)
        data.setdefault("google", False)
        data.setdefault("phone", False)
        data.setdefault("html", False)
        data.setdefault("called_number", "")

        message = str(data.get("message", ""))
        priority = h.check_bool(data.get("priority")) or self._state_is_on(self.config.get(CONF_PRIORITY_MESSAGE_ENTITY, ""))
        dnd = self._state_value(self.config.get(CONF_DND_ENTITY, ""), "off") == "on" or self._night_dnd_active()
        guest = self._state_value(self.config.get(CONF_GUEST_MODE_ENTITY, ""), "off") == "on"
        requested_location = str(data.get("location", ""))
        location_ok = self._check_location(requested_location)
        speech_location = requested_location or ("home" if self.config.get(CONF_SPEECH_HOME_ONLY, False) else "")
        speech_location_ok = self._check_location(speech_location)

        defaults = h.return_list(self.config.get(CONF_NOTIFY_SERVICES, [])) or ["persistent_notification"]
        notify_services = h.normalize_notify_list(data.get("notify", True), defaults)

        use_notification = priority or (self.config.get(CONF_TEXT_NOTIFICATIONS, True) and bool(message) and h.check_notify(data.get("notify")) and location_ok)
        use_persistent = priority or (self.config.get(CONF_SCREEN_NOTIFICATIONS, True) and bool(message) and not h.check_bool(data.get("no_show")))
        use_speech = self.config.get(CONF_SPEECH_NOTIFICATIONS, True) and not dnd and (speech_location_ok or guest)
        use_phone = priority or (self.config.get(CONF_PHONE_NOTIFICATIONS, False) and bool(message) and not dnd and h.check_bool(data.get("phone", False)))

        self.set_debug("OK", {})
        try:
            if use_persistent:
                await self.notification_manager.send_persistent(data)
            if use_notification and notify_services:
                if any(self._is_mobile_notify_service(service) for service in notify_services):
                    self._prepare_confirmation(data)
                await self.notification_manager.send_notify(data, notify_services)
            if use_phone:
                await self.phone_manager.send_voice_call(data)
            alexa = data.get("alexa", False)
            alexa_priority = isinstance(alexa, dict) and h.check_bool(alexa.get("priority", False))
            use_alexa = priority or alexa_priority or (use_speech and self.config.get(CONF_ALEXA_NOTIFICATIONS, True))
            if use_alexa and h.check_notify(alexa):
                await self.alexa_manager.speak(alexa, data)
            google = data.get("google", False)
            google_priority = isinstance(google, dict) and h.check_bool(google.get("priority", False))
            use_google = priority or google_priority or (use_speech and self.config.get(CONF_GOOGLE_NOTIFICATIONS, True))
            if use_google and h.check_notify(google):
                await self.google_manager.speak(google, data)
        except Exception as err:  # noqa: BLE001
            _LOGGER.exception("Notifier Hub dispatch error")
            self.set_debug("Dispatch Error", {"dispatch_error": str(err)})
        finally:
            if self._state_is_on(self.config.get(CONF_PRIORITY_MESSAGE_ENTITY, "")):
                await self.hass.services.async_call(
                    "homeassistant", "turn_off", {"entity_id": self.config.get(CONF_PRIORITY_MESSAGE_ENTITY)}, blocking=False
                )
