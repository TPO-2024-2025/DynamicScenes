"""Config flow for Dynamic Scenes integration."""

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries

from .constants import ENTRYDATA, INTEGRATION_DOMAIN

_LOGGER = logging.getLogger(__name__)


STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(ENTRYDATA.UPDATE_INTERVAL): vol.All(
            vol.Coerce(int), vol.Range(min=1, max=3600)
        )
    }
)

class DynamicScenesConfigFlow(config_entries.ConfigFlow, domain=INTEGRATION_DOMAIN):
    """Handle a config flow for Dynamic Scenes."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_LOCAL_PUSH

    async def async_step_user(self, user_input: dict[str, Any] | None = None):
        """Handle the first step of configuration."""
        if user_input is not None: # When the user submits the form:
            _LOGGER.debug("CONFIG_FLOW: User input: %s", user_input)
            # Store the scene data and rerun interval in the config entry
            return self.async_create_entry(title="Dynamic Scenes", data=user_input)

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors={}
        )
