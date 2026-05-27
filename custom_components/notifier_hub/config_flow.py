from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.helpers import selector

from .const import (
    CONF_ALEXA_PLAYERS,
    CONF_ALEXA_SKILL_ID,
    CONF_GOOGLE_NOTIFY_SERVICE,
    CONF_GOOGLE_PLAYERS,
    CONF_GOOGLE_TTS_SERVICE,
    CONF_DEFAULT_LANGUAGE,
    CONF_DEFAULT_VOLUME,
    CONF_NOTIFY_SERVICES,
    CONF_PERSONAL_ASSISTANT,
    CONF_SIP_SERVER_NAME,
    CONF_TTS_WAIT_TIME,
    DEFAULT_LANGUAGE,
    DEFAULT_PERSONAL_ASSISTANT,
    DEFAULT_SIP_SERVER_NAME,
    DEFAULT_TTS_WAIT_TIME,
    DEFAULT_VOLUME,
    DEFAULT_GOOGLE_NOTIFY_SERVICE,
    DEFAULT_GOOGLE_TTS_SERVICE,
    DOMAIN,
)


class NotifierHubConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None):
        if user_input is not None:
            await self.async_set_unique_id(DOMAIN)
            self._abort_if_unique_id_configured(updates=user_input)
            return self.async_create_entry(title="Notifier Hub", data=user_input)
        return self.async_show_form(step_id="user", data_schema=self._schema())

    async def async_step_import(self, user_input: dict[str, Any]):
        await self.async_set_unique_id(DOMAIN)
        self._abort_if_unique_id_configured(updates=user_input)
        return self.async_create_entry(title="Notifier Hub", data=user_input)

    def _schema(self):
        return vol.Schema(
            {
                vol.Optional(CONF_PERSONAL_ASSISTANT, default=DEFAULT_PERSONAL_ASSISTANT): str,
                vol.Optional(CONF_NOTIFY_SERVICES, default=[]): selector.SelectSelector(
                    selector.SelectSelectorConfig(options=[], multiple=True, custom_value=True)
                ),
                vol.Optional(CONF_ALEXA_PLAYERS, default=[]): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain="media_player", multiple=True)
                ),
                vol.Optional(CONF_ALEXA_SKILL_ID, default=""): str,
                vol.Optional(CONF_GOOGLE_PLAYERS, default=[]): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain="media_player", multiple=True)
                ),
                vol.Optional(CONF_GOOGLE_TTS_SERVICE, default=DEFAULT_GOOGLE_TTS_SERVICE): str,
                vol.Optional(CONF_GOOGLE_NOTIFY_SERVICE, default=DEFAULT_GOOGLE_NOTIFY_SERVICE): str,
                vol.Optional(CONF_SIP_SERVER_NAME, default=DEFAULT_SIP_SERVER_NAME): str,
                vol.Optional(CONF_DEFAULT_LANGUAGE, default=DEFAULT_LANGUAGE): str,
                vol.Optional(CONF_DEFAULT_VOLUME, default=DEFAULT_VOLUME): float,
                vol.Optional(CONF_TTS_WAIT_TIME, default=DEFAULT_TTS_WAIT_TIME): float,
            }
        )
