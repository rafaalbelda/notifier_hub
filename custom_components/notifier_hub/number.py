from __future__ import annotations

from homeassistant.components.number import NumberEntity

from .const import AUTO_VOLUME_PERIODS
from .entity import NotifierHubEntity


async def async_setup_entry(hass, entry, async_add_entities):
    hub = hass.data[entry.domain][entry.entry_id]
    entities = [
        NotifierHubVolumeNumber(hub, key, label, default_volume)
        for key, (label, _, default_volume) in AUTO_VOLUME_PERIODS.items()
    ]
    hub.register_entities(entities)
    async_add_entities(entities)


class NotifierHubVolumeNumber(NotifierHubEntity, NumberEntity):
    _attr_native_min_value = 0
    _attr_native_max_value = 100
    _attr_native_step = 1
    _attr_native_unit_of_measurement = "%"
    _attr_icon = "mdi:volume-high"

    def __init__(self, coordinator, key: str, label: str, default_volume: int) -> None:
        super().__init__(coordinator, f"auto_volume_{key}_volume", f"Notifier Hub {label} Volume")
        self.default_volume = default_volume

    @property
    def native_value(self):
        return int(float(self.coordinator.config.get(self._key, self.default_volume)))

    async def async_set_native_value(self, value: float) -> None:
        self.coordinator.config[self._key] = int(value)
        options = dict(self.coordinator.entry.options)
        options[self._key] = int(value)
        self.coordinator.hass.config_entries.async_update_entry(self.coordinator.entry, options=options)
        await self.coordinator.async_apply_auto_volume()
        self.async_write_ha_state()
