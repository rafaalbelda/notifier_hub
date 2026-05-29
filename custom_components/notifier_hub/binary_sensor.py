from __future__ import annotations

from homeassistant.components.binary_sensor import BinarySensorDeviceClass, BinarySensorEntity
from .entity import NotifierHubEntity


async def async_setup_entry(hass, entry, async_add_entities):
    hub = hass.data[entry.domain][entry.entry_id]
    entities = [
        NotifierHubBinarySensor(hub, "alexa_speak", "Notifier Hub Alexa Speak", "alexa_speak", "alexa_attributes"),
        NotifierHubBinarySensor(hub, "google_speak", "Notifier Hub Google Speak", "google_speak", "google_attributes"),
        NotifierHubHomeOccupiedBinarySensor(hub),
    ]
    hub.register_entities(entities)
    async_add_entities(entities)


class NotifierHubBinarySensor(NotifierHubEntity, BinarySensorEntity):
    def __init__(self, coordinator, key: str, name: str, state_key: str, attr_key: str) -> None:
        super().__init__(coordinator, key, name)
        self.state_key = state_key
        self.attr_key = attr_key

    @property
    def is_on(self):
        return bool(self.coordinator.state.get(self.state_key, False))

    @property
    def extra_state_attributes(self):
        return self.coordinator.state.get(self.attr_key, {})


class NotifierHubHomeOccupiedBinarySensor(NotifierHubEntity, BinarySensorEntity):
    _attr_device_class = BinarySensorDeviceClass.OCCUPANCY

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator, "home_occupied", "Notifier Hub Home Occupied")

    @property
    def is_on(self):
        return self.coordinator.presence_summary()["is_home"]

    @property
    def extra_state_attributes(self):
        summary = self.coordinator.presence_summary()
        return {
            "home_count": summary["home_count"],
            "total_count": summary["total_count"],
            "home_persons": summary["home_persons"],
            "home_person_names": summary["home_person_names"],
            "home_person_details": summary["home_person_details"],
            "away_persons": summary["away_persons"],
            "away_person_names": summary["away_person_names"],
            "away_person_details": summary["away_person_details"],
        }
