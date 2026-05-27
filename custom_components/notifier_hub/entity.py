from __future__ import annotations

from homeassistant.helpers.entity import Entity
from .const import DOMAIN


class NotifierHubEntity(Entity):
    _attr_should_poll = False

    def __init__(self, coordinator, key: str, name: str) -> None:
        self.coordinator = coordinator
        self._key = key
        self._attr_name = name
        self._attr_unique_id = f"{DOMAIN}_{key}"

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, "notifier_hub")},
            "name": "Notifier Hub",
            "manufacturer": "Notifier Hub conversion",
        }

    async def async_update_state(self):
        self.async_write_ha_state()
