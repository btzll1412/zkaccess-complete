"""ZKAccess Complete Control System Integration."""
from __future__ import annotations

import logging
from pathlib import Path

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.components.http.static import StaticPathConfig
from homeassistant.components import frontend

from .const import DOMAIN
from .coordinator import ZKAccessCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [
    Platform.LOCK,
]


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up the ZKAccess integration."""
    hass.data.setdefault(DOMAIN, {})
    
    # Register the frontend panel
    await async_register_panel(hass)
    
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up ZKAccess from a config entry."""
    
    _LOGGER.info("Setting up ZKAccess panel: %s", entry.data.get("panel_name"))
    
    # Create coordinator
    coordinator = ZKAccessCoordinator(hass, entry)
    
    # Try to connect
    if not await coordinator.async_connect():
        _LOGGER.error("Failed to connect to panel %s", entry.data.get("panel_name"))
        raise ConfigEntryNotReady(f"Cannot connect to panel at {entry.data.get('ip_address')}")
    
    # Initial data refresh
    await coordinator.async_config_entry_first_refresh()
    
    # Store coordinator
    hass.data[DOMAIN][entry.entry_id] = coordinator
    
    # Set up platforms
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


async def async_register_panel(hass: HomeAssistant) -> None:
    """Register the frontend panel."""
    
    try:
        # Get path to integration directory
        integration_dir = Path(__file__).parent
        panel_file = integration_dir / "frontend" / "zkaccess-panel.html"
        
        # Register static path using modern async method
        await hass.http.async_register_static_paths([
            StaticPathConfig(
                "/zkaccess-panel",
                str(panel_file),
                cache_headers=False
            )
        ])
        
        # Register panel in sidebar using proper import
        frontend.async_register_built_in_panel(
            hass,
            component_name="iframe",
            sidebar_title="Access Control",
            sidebar_icon="mdi:shield-lock",
            frontend_url_path="zkaccess",
            config={"url": "/zkaccess-panel"},
            require_admin=False,
        )
        
        _LOGGER.info("✅ ZKAccess panel registered successfully")
        
    except Exception as err:
        _LOGGER.error("❌ Failed to register panel: %s", err)
        _LOGGER.exception("Full error details:")
