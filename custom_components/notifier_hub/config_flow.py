from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.data_entry_flow import section
from homeassistant.core import callback
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers import selector

from .const import (
    CONF_ALEXA_NOTIFY_ENTITIES,
    CONF_ALEXA_PLAYERS,
    CONF_GOOGLE_NOTIFY_SERVICE,
    CONF_GOOGLE_PLAYERS,
    CONF_GOOGLE_TTS_SERVICE,
    CONF_DEFAULT_LANGUAGE,
    CONF_DEFAULT_VOLUME,
    CONF_NOTIFY_SERVICES,
    CONF_PERSONAL_ASSISTANT,
    CONF_PERSONS,
    CONF_ALEXA_NOTIFICATIONS,
    CONF_GOOGLE_NOTIFICATIONS,
    CONF_PHONE_NOTIFICATIONS,
    CONF_SCREEN_NOTIFICATIONS,
    CONF_SPEECH_HOME_ONLY,
    CONF_SPEECH_NOTIFICATIONS,
    CONF_TEXT_NOTIFICATIONS,
    CONF_HA_EVENT_NOTIFICATIONS,
    CONF_HA_EVENT_NOTIFY_SERVICES,
    CONF_AUTO_VOLUME,
    CONF_AUTO_VOLUME_EXCLUDE_PLAYERS,
    CONF_NIGHT_DND,
    CONF_INSTALL_DASHBOARD,
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
)

SECTION_GENERAL = "general_section"
SECTION_PERSONS = "persons_section"
SECTION_TEXT_EVENTS = "text_events_section"
SECTION_VOICE = "voice_section"
SECTION_ALEXA = "alexa_section"
SECTION_GOOGLE = "google_section"
SECTION_PHONE = "phone_section"
SECTION_AUTO_VOLUME = "auto_volume_section"

CONF_NOTIFY_SERVICE_TARGETS = "notify_service_targets"
CONF_NOTIFY_ENTITY_TARGETS = "notify_entity_targets"
CONF_HA_EVENT_NOTIFY_SERVICE_TARGETS = "ha_event_notify_service_targets"
CONF_HA_EVENT_NOTIFY_ENTITY_TARGETS = "ha_event_notify_entity_targets"


class NotifierHubConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: config_entries.ConfigEntry):
        return NotifierHubOptionsFlow(config_entry)

    async def async_step_user(self, user_input: dict[str, Any] | None = None):
        if user_input is not None:
            user_input = _flatten_sections(user_input)
            await self.async_set_unique_id(DOMAIN)
            self._abort_if_unique_id_configured(updates=user_input)
            return self.async_create_entry(title="Notifier Hub", data=user_input)
        return self.async_show_form(step_id="user", data_schema=self._schema())

    async def async_step_import(self, user_input: dict[str, Any]):
        await self.async_set_unique_id(DOMAIN)
        self._abort_if_unique_id_configured(updates=user_input)
        return self.async_create_entry(title="Notifier Hub", data=user_input)

    def _schema(self):
        return _schema(self.hass)


class NotifierHubOptionsFlow(config_entries.OptionsFlow):
    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        self._config_entry = config_entry

    async def async_step_init(self, user_input: dict[str, Any] | None = None):
        if user_input is not None:
            user_input = _flatten_sections(user_input)
            return self.async_create_entry(title="", data=user_input)

        data = dict(self._config_entry.data)
        data.update(dict(self._config_entry.options))
        return self.async_show_form(step_id="init", data_schema=_schema(self.hass, data))


def _notify_service_options(hass) -> list[str]:
    services = hass.services.async_services().get("notify", {})
    return [f"notify.{service}" for service in sorted(services)]


def _notify_entity_options(hass) -> list[str]:
    entity_options = set(hass.states.async_entity_ids("notify"))
    entity_options.update(entry.entity_id for entry in er.async_get(hass).entities.values() if entry.domain == "notify")
    return sorted(entity_options)


def _as_list(value: Any) -> list[str]:
    if value is None or value == "":
        return []
    if isinstance(value, list):
        return [str(item) for item in value if str(item)]
    if isinstance(value, (set, tuple)):
        return [str(item) for item in value if str(item)]
    return [item.strip() for item in str(value).split(",") if item.strip()]


def _flatten_sections(data: dict[str, Any]) -> dict[str, Any]:
    flattened: dict[str, Any] = {}
    for key, value in data.items():
        if key.endswith("_section") and isinstance(value, dict):
            flattened.update(value)
        else:
            flattened[key] = value
    _merge_notify_targets(flattened, CONF_NOTIFY_SERVICES, CONF_NOTIFY_SERVICE_TARGETS, CONF_NOTIFY_ENTITY_TARGETS)
    _merge_notify_targets(
        flattened,
        CONF_HA_EVENT_NOTIFY_SERVICES,
        CONF_HA_EVENT_NOTIFY_SERVICE_TARGETS,
        CONF_HA_EVENT_NOTIFY_ENTITY_TARGETS,
    )
    return flattened


def _merge_notify_targets(data: dict[str, Any], target_key: str, service_key: str, entity_key: str) -> None:
    if service_key not in data and entity_key not in data:
        return
    combined = _as_list(data.pop(service_key, [])) + _as_list(data.pop(entity_key, []))
    data[target_key] = list(dict.fromkeys(combined))


def _split_notify_targets(hass, targets: list[str], service_options: list[str]) -> tuple[list[str], list[str]]:
    services: list[str] = []
    entities: list[str] = []
    service_set = set(service_options)
    entity_set = set(_notify_entity_options(hass))
    for target in targets:
        if target in entity_set:
            entities.append(target)
        elif target in service_set:
            services.append(target)
        elif target.strip().lower().startswith("notify."):
            entities.append(target)
        else:
            services.append(target)
    return services, entities


def _schema(hass, defaults: dict[str, Any] | None = None):
    defaults = defaults or {}
    notify_services = _as_list(defaults.get(CONF_NOTIFY_SERVICES, []))
    ha_event_notify_services = _as_list(defaults.get(CONF_HA_EVENT_NOTIFY_SERVICES, []))
    notify_service_options = _notify_service_options(hass)
    notify_entity_options = _notify_entity_options(hass)
    notify_service_targets, notify_entity_targets = _split_notify_targets(hass, notify_services, notify_service_options)
    ha_event_notify_service_targets, ha_event_notify_entity_targets = _split_notify_targets(
        hass,
        ha_event_notify_services,
        notify_service_options,
    )
    notify_service_options = sorted(set(notify_service_options) | set(notify_service_targets) | set(ha_event_notify_service_targets))
    notify_entity_options = sorted(set(notify_entity_options) | set(notify_entity_targets) | set(ha_event_notify_entity_targets))
    location_tracker = defaults.get("location_tracker", "")

    def default(key: str, fallback: Any) -> Any:
        return defaults.get(key, fallback)

    location_tracker_key = (
        vol.Optional("location_tracker", default=location_tracker)
        if location_tracker
        else vol.Optional("location_tracker")
    )

    return vol.Schema(
        {
            vol.Optional(SECTION_GENERAL): section(
                vol.Schema(
                    {
                        vol.Optional(
                            CONF_PERSONAL_ASSISTANT,
                            default=default(CONF_PERSONAL_ASSISTANT, DEFAULT_PERSONAL_ASSISTANT),
                        ): str,
                        vol.Optional(
                            CONF_INSTALL_DASHBOARD,
                            default=default(CONF_INSTALL_DASHBOARD, True),
                        ): selector.BooleanSelector(),
                    }
                ),
                {"collapsed": False},
            ),
            vol.Optional(SECTION_PERSONS): section(
                vol.Schema(
                    {
                        vol.Optional(CONF_PERSONS, default=_as_list(default(CONF_PERSONS, []))): selector.EntitySelector(
                            selector.EntitySelectorConfig(domain="person", multiple=True)
                        ),
                        location_tracker_key: selector.EntitySelector(
                            selector.EntitySelectorConfig(domain=["group", "person", "device_tracker", "sensor"])
                        ),
                    }
                ),
                {"collapsed": False},
            ),
            vol.Optional(SECTION_TEXT_EVENTS): section(
                vol.Schema(
                    {
                        vol.Optional(
                            CONF_TEXT_NOTIFICATIONS,
                            default=default(CONF_TEXT_NOTIFICATIONS, True),
                        ): selector.BooleanSelector(),
                        vol.Optional(
                            CONF_SCREEN_NOTIFICATIONS,
                            default=default(CONF_SCREEN_NOTIFICATIONS, True),
                        ): selector.BooleanSelector(),
                        vol.Optional(CONF_NOTIFY_SERVICE_TARGETS, default=notify_service_targets): selector.SelectSelector(
                            selector.SelectSelectorConfig(options=notify_service_options, multiple=True, custom_value=True)
                        ),
                        vol.Optional(CONF_NOTIFY_ENTITY_TARGETS, default=notify_entity_targets): selector.SelectSelector(
                            selector.SelectSelectorConfig(options=notify_entity_options, multiple=True, custom_value=True)
                        ),
                        vol.Optional(
                            CONF_HA_EVENT_NOTIFICATIONS,
                            default=default(CONF_HA_EVENT_NOTIFICATIONS, True),
                        ): selector.BooleanSelector(),
                        vol.Optional(
                            CONF_HA_EVENT_NOTIFY_SERVICE_TARGETS,
                            default=ha_event_notify_service_targets,
                        ): selector.SelectSelector(
                            selector.SelectSelectorConfig(options=notify_service_options, multiple=True, custom_value=True)
                        ),
                        vol.Optional(
                            CONF_HA_EVENT_NOTIFY_ENTITY_TARGETS,
                            default=ha_event_notify_entity_targets,
                        ): selector.SelectSelector(
                            selector.SelectSelectorConfig(options=notify_entity_options, multiple=True, custom_value=True)
                        ),
                    }
                ),
                {"collapsed": False},
            ),
            vol.Optional(SECTION_VOICE): section(
                vol.Schema(
                    {
                        vol.Optional(
                            CONF_SPEECH_NOTIFICATIONS,
                            default=default(CONF_SPEECH_NOTIFICATIONS, True),
                        ): selector.BooleanSelector(),
                        vol.Optional(
                            CONF_SPEECH_HOME_ONLY,
                            default=default(CONF_SPEECH_HOME_ONLY, False),
                        ): selector.BooleanSelector(),
                        vol.Optional(CONF_DEFAULT_LANGUAGE, default=default(CONF_DEFAULT_LANGUAGE, DEFAULT_LANGUAGE)): str,
                        vol.Optional(CONF_DEFAULT_VOLUME, default=default(CONF_DEFAULT_VOLUME, DEFAULT_VOLUME)): vol.Coerce(float),
                        vol.Optional(CONF_TTS_WAIT_TIME, default=default(CONF_TTS_WAIT_TIME, DEFAULT_TTS_WAIT_TIME)): vol.Coerce(float),
                    }
                ),
                {"collapsed": False},
            ),
            vol.Optional(SECTION_ALEXA): section(
                vol.Schema(
                    {
                        vol.Optional(
                            CONF_ALEXA_NOTIFICATIONS,
                            default=default(CONF_ALEXA_NOTIFICATIONS, True),
                        ): selector.BooleanSelector(),
                        vol.Optional(CONF_ALEXA_PLAYERS, default=default(CONF_ALEXA_PLAYERS, [])): selector.EntitySelector(
                            selector.EntitySelectorConfig(domain="media_player", multiple=True)
                        ),
                        vol.Optional(
                            CONF_ALEXA_NOTIFY_ENTITIES,
                            default=default(CONF_ALEXA_NOTIFY_ENTITIES, []),
                        ): selector.EntitySelector(selector.EntitySelectorConfig(domain="notify", multiple=True)),
                    }
                ),
                {"collapsed": False},
            ),
            vol.Optional(SECTION_GOOGLE): section(
                vol.Schema(
                    {
                        vol.Optional(
                            CONF_GOOGLE_NOTIFICATIONS,
                            default=default(CONF_GOOGLE_NOTIFICATIONS, True),
                        ): selector.BooleanSelector(),
                        vol.Optional(CONF_GOOGLE_PLAYERS, default=default(CONF_GOOGLE_PLAYERS, [])): selector.EntitySelector(
                            selector.EntitySelectorConfig(domain="media_player", multiple=True)
                        ),
                        vol.Optional(
                            CONF_GOOGLE_NOTIFY_SERVICE,
                            default=default(CONF_GOOGLE_NOTIFY_SERVICE, DEFAULT_GOOGLE_NOTIFY_SERVICE),
                        ): str,
                        vol.Optional(
                            CONF_GOOGLE_TTS_SERVICE,
                            default=default(CONF_GOOGLE_TTS_SERVICE, DEFAULT_GOOGLE_TTS_SERVICE),
                        ): str,
                    }
                ),
                {"collapsed": True},
            ),
            vol.Optional(SECTION_PHONE): section(
                vol.Schema(
                    {
                        vol.Optional(
                            CONF_PHONE_NOTIFICATIONS,
                            default=default(CONF_PHONE_NOTIFICATIONS, False),
                        ): selector.BooleanSelector(),
                        vol.Optional(CONF_SIP_SERVER_NAME, default=default(CONF_SIP_SERVER_NAME, DEFAULT_SIP_SERVER_NAME)): str,
                    }
                ),
                {"collapsed": True},
            ),
            vol.Optional(SECTION_AUTO_VOLUME): section(
                vol.Schema(
                    {
                        vol.Optional(CONF_AUTO_VOLUME, default=default(CONF_AUTO_VOLUME, False)): selector.BooleanSelector(),
                        vol.Optional(CONF_NIGHT_DND, default=default(CONF_NIGHT_DND, False)): selector.BooleanSelector(),
                        vol.Optional(
                            CONF_AUTO_VOLUME_EXCLUDE_PLAYERS,
                            default=_as_list(default(CONF_AUTO_VOLUME_EXCLUDE_PLAYERS, [])),
                        ): selector.EntitySelector(
                            selector.EntitySelectorConfig(domain="media_player", multiple=True)
                        ),
                    }
                ),
                {"collapsed": False},
            ),
        }
    )
