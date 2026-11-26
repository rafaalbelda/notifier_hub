from __future__ import annotations

from homeassistant.helpers.entity import Entity
from .const import DOMAIN


class NotifierHubEntity(Entity):
    _attr_should_poll = False
    _attr_has_entity_name = True

    def __init__(self, coordinator, key: str, name: str | None = None, translation_key: str | None = None) -> None:
        self.coordinator = coordinator
        self._key = key
        self._attr_unique_id = f"{DOMAIN}_{key}"
        if translation_key is not None:
            self._attr_translation_key = translation_key
        elif name is not None:
            self._attr_name = name

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, "notifier_hub")},
            "name": "Notifier Hub",
            "manufacturer": "Notifier Hub conversion",
        }

    async def async_update_state(self):
        self.async_write_ha_state()
