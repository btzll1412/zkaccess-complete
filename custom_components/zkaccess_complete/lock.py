"""Lock platform for ZKAccess."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.lock import LockEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up ZKAccess lock entities."""
    
    panel_data = hass.data[DOMAIN][entry.entry_id]
    panel_name = panel_data["panel_name"]
    
    # Create 4 lock entities (for C3-400)
    entities = []
    for door_num in range(1, 5):
        entities.append(ZKAccessDoorLock(entry, panel_name, door_num))
    
    async_add_entities(entities)
    
    _LOGGER.info("Added %d lock entities for %s", len(entities), panel_name)


class ZKAccessDoorLock(LockEntity):
    """Representation of a ZKAccess door lock."""

    def __init__(
        self,
        entry: ConfigEntry,
        panel_name: str,
        door_number: int,
    ) -> None:
        """Initialize the lock."""
        self._door_number = door_number
        self._panel_name = panel_name
        self._attr_name = f"{panel_name} Door {door_number}"
        self._attr_unique_id = f"{entry.entry_id}_door_{door_number}"
        self._is_locked = True
        
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": panel_name,
            "manufacturer": "ZKTeco",
            "model": "C3-400",
        }

    @property
    def is_locked(self) -> bool:
        """Return true if lock is locked."""
        return self._is_locked

    async def async_lock(self, **kwargs: Any) -> None:
        """Lock the door."""
        _LOGGER.info("Locking %s", self.name)
        self._is_locked = True
        self.async_write_ha_state()

    async def async_unlock(self, **kwargs: Any) -> None:
        """Unlock the door."""
        _LOGGER.info("Unlocking %s", self.name)
        self._is_locked = False
        self.async_write_ha_state()
