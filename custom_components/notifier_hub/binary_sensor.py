from __future__ import annotations

from homeassistant.components.binary_sensor import BinarySensorEntity
from .entity import NotifierHubEntity


async def async_setup_entry(hass, entry, async_add_entities):
    hub = hass.data[entry.domain][entry.entry_id]
    entities = [
        NotifierHubBinarySensor(hub, "alexa_speak", "Notifier Hub Alexa Speak", "alexa_speak", "alexa_attributes"),
        NotifierHubBinarySensor(hub, "google_speak", "Notifier Hub Google Speak", "google_speak", "google_attributes"),
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
