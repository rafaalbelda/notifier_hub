from __future__ import annotations

from homeassistant.components.button import ButtonEntity

from .entity import NotifierHubEntity


async def async_setup_entry(hass, entry, async_add_entities):
    hub = hass.data[entry.domain][entry.entry_id]
    entities = [NotifierHubSendDashboardMessageButton(hub)]
    hub.register_entities(entities)
    async_add_entities(entities)


class NotifierHubSendDashboardMessageButton(NotifierHubEntity, ButtonEntity):
    _attr_icon = "mdi:send"

    def __init__(self, coordinator) -> None:
        super().__init__(
            coordinator,
            "send_dashboard_message",
            "Notifier Hub Send Dashboard Message",
        )

    async def async_press(self) -> None:
        await self.coordinator.async_send_dashboard_message()
