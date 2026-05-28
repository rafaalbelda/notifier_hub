from __future__ import annotations

from datetime import time

from homeassistant.components.time import TimeEntity

from .const import AUTO_VOLUME_PERIODS
from .entity import NotifierHubEntity


async def async_setup_entry(hass, entry, async_add_entities):
    hub = hass.data[entry.domain][entry.entry_id]
    entities = [
        NotifierHubPeriodTime(hub, key, label, default_time)
        for key, (label, default_time, _) in AUTO_VOLUME_PERIODS.items()
    ]
    hub.register_entities(entities)
    async_add_entities(entities)


class NotifierHubPeriodTime(NotifierHubEntity, TimeEntity):
    _attr_icon = "mdi:clock-time-four-outline"

    def __init__(self, coordinator, key: str, label: str, default_time: str) -> None:
        super().__init__(coordinator, f"auto_volume_{key}_time", f"Notifier Hub {label} Start")
        self.default_time = default_time

    @property
    def native_value(self) -> time:
        return self.coordinator._parse_time(self.coordinator.config.get(self._key), self.default_time)

    async def async_set_value(self, value: time) -> None:
        serialized = value.strftime("%H:%M:%S")
        self.coordinator.config[self._key] = serialized
        options = dict(self.coordinator.entry.options)
        options[self._key] = serialized
        self.coordinator.hass.config_entries.async_update_entry(self.coordinator.entry, options=options)
        await self.coordinator.async_apply_auto_volume()
        self.async_write_ha_state()
