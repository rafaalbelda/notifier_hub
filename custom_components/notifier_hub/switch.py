from __future__ import annotations

from homeassistant.components.switch import SwitchEntity

from .const import (
    CONF_ALEXA_NOTIFICATIONS,
    CONF_AUTO_VOLUME,
    CONF_AUTO_VOLUME_CONTROL_PLAYERS,
    CONF_DND_MODE,
    CONF_GOOGLE_NOTIFICATIONS,
    CONF_GUEST_MODE,
    CONF_HA_EVENT_NOTIFICATIONS,
    CONF_NIGHT_DND,
    CONF_PHONE_NOTIFICATIONS,
    CONF_PRIORITY_MESSAGE,
    CONF_SCREEN_NOTIFICATIONS,
    CONF_SPEECH_HOME_ONLY,
    CONF_SPEECH_NOTIFICATIONS,
    CONF_TEXT_NOTIFICATIONS,
)
from .entity import NotifierHubEntity

SWITCHES = [
    (CONF_TEXT_NOTIFICATIONS, "Notifier Hub Text Notifications", True, "mdi:message-text"),
    (CONF_SCREEN_NOTIFICATIONS, "Notifier Hub Screen Notifications", True, "mdi:message-badge"),
    (CONF_SPEECH_NOTIFICATIONS, "Notifier Hub Speech Notifications", True, "mdi:account-voice"),
    (CONF_SPEECH_HOME_ONLY, "Notifier Hub Speech Home Only", False, "mdi:home-account"),
    (CONF_ALEXA_NOTIFICATIONS, "Notifier Hub Alexa Notifications", True, "mdi:speaker-message"),
    (CONF_GOOGLE_NOTIFICATIONS, "Notifier Hub Google Notifications", True, "mdi:google-assistant"),
    (CONF_PHONE_NOTIFICATIONS, "Notifier Hub Phone Notifications", False, "mdi:phone-message"),
    (CONF_HA_EVENT_NOTIFICATIONS, "Notifier Hub Home Assistant Event Notifications", True, "mdi:home-assistant"),
    (CONF_AUTO_VOLUME, "Notifier Hub Auto Volume", False, "mdi:volume-high"),
    (CONF_AUTO_VOLUME_CONTROL_PLAYERS, "Notifier Hub Auto Volume Controls Players", True, "mdi:volume-source"),
    (CONF_DND_MODE, "Notifier Hub DND", False, "mdi:bell-off"),
    (CONF_NIGHT_DND, "Notifier Hub Night DND", False, "mdi:weather-night"),
    (CONF_GUEST_MODE, "Notifier Hub Guest Mode", False, "mdi:account-group"),
    (CONF_PRIORITY_MESSAGE, "Notifier Hub Priority Message", False, "mdi:alert-circle"),
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
        await self.coordinator.async_apply_auto_volume()
        self.coordinator.set_debug("config updated", {"config_keys": [self._key]})
        self.async_write_ha_state()
