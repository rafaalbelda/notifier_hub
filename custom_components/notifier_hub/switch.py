from __future__ import annotations

from homeassistant.components.switch import SwitchEntity

from .const import (
    CONF_ALEXA_NOTIFICATIONS,
    CONF_GOOGLE_NOTIFICATIONS,
    CONF_HA_EVENT_NOTIFICATIONS,
    CONF_PHONE_NOTIFICATIONS,
    CONF_SCREEN_NOTIFICATIONS,
    CONF_SPEECH_NOTIFICATIONS,
    CONF_TEXT_NOTIFICATIONS,
)
from .entity import NotifierHubEntity

SWITCHES = [
    (CONF_TEXT_NOTIFICATIONS, "Notifier Hub Text Notifications", True, "mdi:message-text"),
    (CONF_SCREEN_NOTIFICATIONS, "Notifier Hub Screen Notifications", True, "mdi:monitor-message"),
    (CONF_SPEECH_NOTIFICATIONS, "Notifier Hub Speech Notifications", True, "mdi:account-voice"),
    (CONF_ALEXA_NOTIFICATIONS, "Notifier Hub Alexa Notifications", True, "mdi:amazon-alexa"),
    (CONF_GOOGLE_NOTIFICATIONS, "Notifier Hub Google Notifications", True, "mdi:google-assistant"),
    (CONF_PHONE_NOTIFICATIONS, "Notifier Hub Phone Notifications", False, "mdi:phone-message"),
    (CONF_HA_EVENT_NOTIFICATIONS, "Notifier Hub Home Assistant Event Notifications", True, "mdi:home-assistant"),
]


async def async_setup_entry(hass, entry, async_add_entities):
    hub = hass.data[entry.domain][entry.entry_id]
    entities = [
        NotifierHubSwitch(hub, key, name, default, icon)
        for key, name, default, icon in SWITCHES
    ]
    hub.register_entities(entities)
    async_add_entities(entities)


class NotifierHubSwitch(NotifierHubEntity, SwitchEntity):
    def __init__(self, coordinator, key: str, name: str, default: bool, icon: str) -> None:
        super().__init__(coordinator, key, name)
        self.default = default
        self._attr_icon = icon

    @property
    def is_on(self) -> bool:
        return bool(self.coordinator.config.get(self._key, self.default))

    async def async_turn_on(self, **kwargs) -> None:
        await self._set_enabled(True)

    async def async_turn_off(self, **kwargs) -> None:
        await self._set_enabled(False)

    async def _set_enabled(self, enabled: bool) -> None:
        self.coordinator.config[self._key] = enabled
        options = dict(self.coordinator.entry.options)
        options[self._key] = enabled
        self.coordinator.hass.config_entries.async_update_entry(
            self.coordinator.entry,
            options=options,
        )
        self.coordinator.set_debug("config updated", {"config_keys": [self._key]})
        self.async_write_ha_state()
