from __future__ import annotations

from homeassistant.components.sensor import SensorEntity
from .entity import NotifierHubEntity


async def async_setup_entry(hass, entry, async_add_entities):
    hub = hass.data[entry.domain][entry.entry_id]
    entities = [
        NotifierHubSensor(hub, "debug_error", "Notifier Hub Debug", "debug"),
        NotifierHubSensor(hub, "last_message", "Notifier Hub Last Message", "last_message"),
        NotifierHubPersonalAssistantSensor(hub),
        NotifierHubSensor(hub, "day_period", "Notifier Hub Day Period", "day_period"),
        NotifierHubSensor(hub, "day_period_volume", "Notifier Hub Day Period Volume", "day_period_volume"),
        NotifierHubHomePeopleSensor(hub),
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


class NotifierHubPersonalAssistantSensor(NotifierHubEntity, SensorEntity):
    _attr_icon = "mdi:account-voice"

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator, "personal_assistant", "Notifier Hub Personal Assistant")

    @property
    def native_value(self):
        return self.coordinator.config.get("personal_assistant", "Assistant")


class NotifierHubHomePeopleSensor(NotifierHubEntity, SensorEntity):
    _attr_icon = "mdi:account-multiple-check"

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator, "home_people", "Notifier Hub Home People")

    @property
    def native_value(self):
        return self.coordinator.presence_summary()["home_count"]

    @property
    def extra_state_attributes(self):
        summary = self.coordinator.presence_summary()
        return {
            "total_count": summary["total_count"],
            "away_count": summary["away_count"],
            "is_home": summary["is_home"],
            "home_persons": summary["home_persons"],
            "home_person_names": summary["home_person_names"],
            "home_person_details": summary["home_person_details"],
            "away_persons": summary["away_persons"],
            "away_person_names": summary["away_person_names"],
            "away_person_details": summary["away_person_details"],
            "persons": summary["persons"],
        }
