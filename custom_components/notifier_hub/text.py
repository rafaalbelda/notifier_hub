from __future__ import annotations

from homeassistant.components.text import TextEntity

from .const import STATE_DASHBOARD_MESSAGE
from .entity import NotifierHubEntity


async def async_setup_entry(hass, entry, async_add_entities):
    hub = hass.data[entry.domain][entry.entry_id]
    entities = [NotifierHubDashboardMessageText(hub)]
    hub.register_entities(entities)
    async_add_entities(entities)


class NotifierHubDashboardMessageText(NotifierHubEntity, TextEntity):
    _attr_icon = "mdi:form-textbox"
    _attr_native_max = 1024
    _attr_mode = "text"

    def __init__(self, coordinator) -> None:
        super().__init__(
            coordinator,
            STATE_DASHBOARD_MESSAGE,
            "Notifier Hub Dashboard Message",
        )

    @property
    def native_value(self) -> str:
        return str(self.coordinator.state.get(STATE_DASHBOARD_MESSAGE, ""))

    async def async_set_value(self, value: str) -> None:
        self.coordinator.set_dashboard_message(value)
