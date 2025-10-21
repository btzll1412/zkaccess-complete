"""Config flow for ZKAccess Complete Control System."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_IP_ADDRESS, CONF_PORT
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
import homeassistant.helpers.config_validation as cv

from .const import (
    DOMAIN,
    CONF_PANEL_NAME,
    CONF_PASSWORD,
    DEFAULT_PORT,
)

_LOGGER = logging.getLogger(__name__)


class ZKAccessConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for ZKAccess."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                # Basic validation - just check if IP is provided
                ip = user_input[CONF_IP_ADDRESS]
                
                # Create unique ID based on IP
                await self.async_set_unique_id(ip)
                self._abort_if_unique_id_configured()
                
                return self.async_create_entry(
                    title=user_input[CONF_PANEL_NAME],
                    data=user_input,
                )
                
            except Exception as err:
                _LOGGER.exception("Unexpected exception: %s", err)
                errors["base"] = "unknown"

        # Show form
        data_schema = vol.Schema(
            {
                vol.Required(CONF_PANEL_NAME, default="Access Panel"): str,
                vol.Required(CONF_IP_ADDRESS): str,
                vol.Optional(CONF_PORT, default=DEFAULT_PORT): cv.port,
                vol.Optional(CONF_PASSWORD, default=""): str,
            }
        )

        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
            errors=errors,
        )

    @staticmethod
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> ZKAccessOptionsFlowHandler:
        """Get the options flow for this handler."""
        return ZKAccessOptionsFlowHandler(config_entry)


class ZKAccessOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options flow for ZKAccess."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        "scan_interval",
                        default=self.config_entry.options.get("scan_interval", 5),
                    ): vol.All(vol.Coerce(int), vol.Range(min=1, max=60)),
                    vol.Optional(
                        "unlock_duration",
                        default=self.config_entry.options.get("unlock_duration", 5),
                    ): vol.All(vol.Coerce(int), vol.Range(min=1, max=255)),
                    vol.Optional(
                        "enable_notifications",
                        default=self.config_entry.options.get("enable_notifications", True),
                    ): bool,
                }
            ),
        )
