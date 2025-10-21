"""ZKAccess Complete Control System Integration."""
from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady

from .const import DOMAIN
from .coordinator import ZKAccessCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [
    Platform.LOCK,
]


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up the ZKAccess integration."""
    hass.data.setdefault(DOMAIN, {})
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up ZKAccess from a config entry."""
    
    _LOGGER.info("Setting up ZKAccess panel: %s", entry.data.get("panel_name"))
    
    coordinator = ZKAccessCoordinator(hass, entry)
    
    if not await coordinator.async_connect():
        _LOGGER.error("Failed to connect to panel %s at %s", 
                     entry.data.get("panel_name"),
                     entry.data.get("ip_address"))
        raise ConfigEntryNotReady(
            f"Cannot connect to panel at {entry.data.get('ip_address')}"
        )
    
    await coordinator.async_config_entry_first_refresh()
    
    hass.data[DOMAIN][entry.entry_id] = coordinator
    
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    
    _LOGGER.info("ZKAccess panel setup complete: %s", entry.data.get("panel_name"))
    
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    
    if unload_ok:
        coordinator = hass.data[DOMAIN].pop(entry.entry_id)
        await coordinator.async_disconnect()
    
    return unload_ok
