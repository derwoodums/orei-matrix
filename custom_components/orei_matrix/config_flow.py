"""Config flow for OREI Matrix integration."""

import logging

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_HOST

from .client import OreiMatrixClient
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

DATA_SCHEMA = vol.Schema({
    vol.Required(CONF_HOST): str,
})


class OreiMatrixConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for OREI Matrix."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle the initial step — user enters host IP."""
        errors = {}

        if user_input is not None:
            host = user_input[CONF_HOST].strip()

            # Check if already configured
            await self.async_set_unique_id(host)
            self._abort_if_unique_id_configured()

            # Validate connection
            client = OreiMatrixClient(host)
            try:
                status = await client.validate_connection()
                model = status.get("model", status.get("type", "OREI Matrix"))
                title = f"OREI {model} ({host})"
            except ConnectionError:
                errors["base"] = "cannot_connect"
            except Exception:
                _LOGGER.exception("Unexpected error during config flow")
                errors["base"] = "unknown"
            else:
                return self.async_create_entry(
                    title=title,
                    data={CONF_HOST: host},
                )

        return self.async_show_form(
            step_id="user",
            data_schema=DATA_SCHEMA,
            errors=errors,
        )
