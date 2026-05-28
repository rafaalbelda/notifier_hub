from __future__ import annotations

from homeassistant.components.sensor import SensorEntity
from .entity import NotifierHubEntity


async def async_setup_entry(hass, entry, async_add_entities):
    hub = hass.data[entry.domain][entry.entry_id]
    entities = [
        NotifierHubSensor(hub, "debug_error", "Notifier Hub Debug", "debug"),
        NotifierHubSensor(hub, "last_message", "Notifier Hub Last Message", "last_message"),
        NotifierHubSensor(hub, "day_period", "Notifier Hub Day Period", "day_period"),
        NotifierHubSensor(hub, "day_period_volume", "Notifier Hub Day Period Volume", "day_period_volume"),
    ]
    hub.register_entities(entities)
    async_add_entities(entities)


class NotifierHubSensor(NotifierHubEntity, SensorEntity):
    def __init__(self, coordinator, key: str, name: str, data_key: str) -> None:
        super().__init__(coordinator, key, name)
        self.data_key = data_key

    @property
    def native_value(self):
        return self.coordinator.state.get(self.data_key, "")

    @property
    def extra_state_attributes(self):
        if self.data_key == "debug":
            return self.coordinator.state.get("debug_attributes", {})
        if self.data_key == "day_period_volume":
            return {
                "volume_level": self.coordinator.state.get("day_period_volume_level", 0.0),
                "period": self.coordinator.state.get("day_period", ""),
            }
        return None
