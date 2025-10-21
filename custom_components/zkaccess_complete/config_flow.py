"""Config flow for ZKAccess Complete Control System."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_IP_ADDRESS, CONF_PORT
from homeassistant.core import HomeAssistant, callback
from homeassistant.data_entry_flow import FlowResult
import homeassistant.helpers.config_validation as cv

from .const import (
    DOMAIN,
    CONF_PANEL_NAME,
    CONF_PASSWORD,
    CONF_DOORS,
    DEFAULT_PORT,
)
from .api.c3_client import C3Client

_LOGGER = logging.getLogger(__name__)


async def validate_connection(
    hass: HomeAssistant, data: dict[str, Any]
) -> dict[str, Any]:
    """Validate the user input allows us to connect."""
    
    client = C3Client(
        ip=data[CONF_IP_ADDRESS],
        port=data.get(CONF_PORT, DEFAULT_PORT),
        password=data.get(CONF_PASSWORD, ""),
    )
    
    # Test connection
    if not await hass.async_add_executor_job(client.connect):
        raise ConnectionError("Cannot connect to panel")
    
    # Get panel info
    info = await hass.async_add_executor_job(client.get_device_info)
    
    # Disconnect
    await hass.async_add_executor_job(client.disconnect)
    
    return {
        "title": data[CONF_PANEL_NAME],
        "serial_number": info.get("serial_number", "Unknown"),
        "model": info.get("model", "C3-400"),
        "firmware": info.get("firmware", "Unknown"),
        "door_count": info.get("door_count", 4),
    }


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
                info = await validate_connection(self.hass, user_input)
            except ConnectionError:
                errors["base"] = "cannot_connect"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            else:
                # Create unique ID based on IP
                await self.async_set_unique_id(user_input[CONF_IP_ADDRESS])
                self._abort_if_unique_id_configured()
                
                return self.async_create_entry(
                    title=info["title"],
                    data=user_input,
                )

        # Show form
        data_schema = vol.Schema(
            {
                vol.Required(CONF_PANEL_NAME, default="Access Panel"): str,
                vol.Required(CONF_IP_ADDRESS): str,
                vol.Optional(CONF_PORT, default=DEFAULT_PORT): cv.port,
                vol.Optional(CONF_PASSWORD): str,
            }
        )

        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
            errors=errors,
            description_placeholders={
                "docs_url": "https://github.com/btzll1412/zkaccess-complete"
            },
        )

    @staticmethod
    @callback
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
