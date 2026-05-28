from __future__ import annotations

import asyncio
import logging
from typing import Any

import voluptuous as vol
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_NAME, Platform
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.typing import ConfigType

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
    CONF_SIP_SERVER_NAME,
    CONF_TTS_WAIT_TIME,
    DEFAULT_LANGUAGE,
    DEFAULT_PERSONAL_ASSISTANT,
    DEFAULT_SIP_SERVER_NAME,
    DEFAULT_TTS_WAIT_TIME,
    DEFAULT_VOLUME,
    DEFAULT_GOOGLE_NOTIFY_SERVICE,
    DEFAULT_GOOGLE_TTS_SERVICE,
    DOMAIN,
    EVENT_NOTIFIER,
    SERVICE_SEND,
    SERVICE_SET_CONFIG,
)
from .notification_manager import NotificationManager
from .phone_manager import PhoneManager

_LOGGER = logging.getLogger(__name__)
PLATFORMS = [Platform.SENSOR, Platform.BINARY_SENSOR]

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
                vol.Optional("text_notifications", default=True): cv.boolean,
                vol.Optional("screen_notifications", default=True): cv.boolean,
                vol.Optional("speech_notifications", default=True): cv.boolean,
                vol.Optional("phone_notifications", default=False): cv.boolean,
                vol.Optional("dnd_entity", default=""): cv.string,
                vol.Optional("guest_mode_entity", default=""): cv.string,
                vol.Optional("priority_message_entity", default=""): cv.string,
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

SET_CONFIG_SCHEMA = vol.Schema({vol.Required("config"): dict}, extra=vol.ALLOW_EXTRA)


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
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


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
            "alexa_speak": False,
            "alexa_attributes": {},
            "google_speak": False,
            "google_attributes": {},
        }
        self.entities: list[Any] = []
        self.notification_manager = NotificationManager(hass, self)
        self.phone_manager = PhoneManager(hass, self)
        self.alexa_manager = AlexaManager(hass, self)
        self.google_manager = GoogleManager(hass, self)
        self._remove_listener = None

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
        data.setdefault("text_notifications", True)
        data.setdefault("screen_notifications", True)
        data.setdefault("speech_notifications", True)
        data.setdefault("phone_notifications", False)
        return data

    async def async_setup(self) -> None:
        self.hass.services.async_register(DOMAIN, SERVICE_SEND, self._handle_send, schema=SEND_SCHEMA)
        self.hass.services.async_register(DOMAIN, SERVICE_SET_CONFIG, self._handle_set_config, schema=SET_CONFIG_SCHEMA)
        self._remove_listener = self.hass.bus.async_listen(EVENT_NOTIFIER, self._handle_notifier_event)
        self.set_debug("on", {})

    async def async_unload(self) -> None:
        if self._remove_listener:
            self._remove_listener()
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

    def set_debug(self, state: str, attributes: dict[str, Any]) -> None:
        self.state["debug"] = state
        self.state["debug_attributes"] = attributes
        self._refresh_entities()

    def set_last_message(self, message: str) -> None:
        self.state["last_message"] = message
        self._refresh_entities()

    def set_alexa_speak(self, is_on: bool, attributes: dict[str, Any]) -> None:
        self.state["alexa_speak"] = is_on
        self.state["alexa_attributes"] = attributes
        self._refresh_entities()

    def set_google_speak(self, is_on: bool, attributes: dict[str, Any]) -> None:
        self.state["google_speak"] = is_on
        self.state["google_attributes"] = attributes
        self._refresh_entities()

    async def _handle_set_config(self, call: ServiceCall) -> None:
        self.config.update(call.data.get("config", {}))
        self.set_debug("config updated", {"config_keys": sorted(call.data.get("config", {}).keys())})

    async def _handle_notifier_event(self, event) -> None:
        data = dict(event.data or {})
        if isinstance(data.get("ad"), dict):
            # AppDaemon command compatibility. In a native integration no restart_app exists.
            self.set_debug("ad command ignored", {"command": data["ad"].get("command")})
            return
        await self.dispatch(data)

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
        priority = h.check_bool(data.get("priority")) or self._state_is_on(self.config.get("priority_message_entity", ""))
        dnd = self._state_value(self.config.get("dnd_entity", ""), "off") == "on"
        guest = self._state_value(self.config.get("guest_mode_entity", ""), "off") == "on"
        location_ok = self._check_location(str(data.get("location", "")))

        defaults = h.return_list(self.config.get(CONF_NOTIFY_SERVICES, [])) or ["persistent_notification"]
        notify_services = h.normalize_notify_list(data.get("notify", True), defaults)

        use_notification = priority or (self.config.get("text_notifications", True) and bool(message) and h.check_notify(data.get("notify")) and location_ok)
        use_persistent = priority or (self.config.get("screen_notifications", True) and bool(message) and not h.check_bool(data.get("no_show")))
        use_tts = priority or (self.config.get("speech_notifications", True) and not dnd and (location_ok or guest))
        use_phone = priority or (self.config.get("phone_notifications", False) and bool(message) and not dnd and h.check_bool(data.get("phone", False)))

        self.set_debug("OK", {})
        try:
            if use_persistent:
                await self.notification_manager.send_persistent(data)
            if use_notification and notify_services:
                await self.notification_manager.send_notify(data, notify_services)
            if use_phone:
                await self.phone_manager.send_voice_call(data)
            alexa = data.get("alexa", False)
            alexa_priority = isinstance(alexa, dict) and h.check_bool(alexa.get("priority", False))
            if (use_tts or alexa_priority) and h.check_notify(alexa):
                await self.alexa_manager.speak(alexa, data)
            google = data.get("google", False)
            google_priority = isinstance(google, dict) and h.check_bool(google.get("priority", False))
            if (use_tts or google_priority) and h.check_notify(google):
                await self.google_manager.speak(google, data)
        except Exception as err:  # noqa: BLE001
            _LOGGER.exception("Notifier Hub dispatch error")
            self.set_debug("Dispatch Error", {"dispatch_error": str(err)})
        finally:
            if self._state_is_on(self.config.get("priority_message_entity", "")):
                await self.hass.services.async_call(
                    "input_boolean", "turn_off", {"entity_id": self.config.get("priority_message_entity")}, blocking=False
                )
