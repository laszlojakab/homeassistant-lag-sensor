"""The configuration flow for lag sensor integration."""
from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_DELAY_TIME, CONF_ENTITY_ID, CONF_NAME
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import selector

from custom_components.lag_sensor.const import DOMAIN


@config_entries.HANDLERS.register(DOMAIN)
class LagSensorConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Configuration flow handler for lag sensor integration."""

    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """Handles the step when integration added from the UI."""
        data_schema = vol.Schema(
            {
                vol.Required(CONF_NAME): str,
                vol.Required(CONF_ENTITY_ID): selector.EntitySelector(),
                vol.Required(CONF_DELAY_TIME): selector.TimeSelector(),
            }
        )

        if user_input is not None:
            await self.async_set_unique_id(
                user_input.get(CONF_ENTITY_ID) + str(user_input.get(CONF_DELAY_TIME))
            )

            self._abort_if_unique_id_configured()

            return self.async_create_entry(
                title=f"Lag sensor ({user_input.get(CONF_NAME)})", data=user_input
            )

        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
        )
