"""Lock platform for ZKAccess."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.lock import LockEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import ZKAccessCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up ZKAccess lock entities."""
    coordinator: ZKAccessCoordinator = hass.data[DOMAIN][entry.entry_id]
    
    # Create a lock entity for each door
    entities = []
    for door_num in range(1, coordinator.door_count + 1):
        entities.append(ZKAccessDoorLock(coordinator, entry, door_num))
    
    async_add_entities(entities)
    
    _LOGGER.info("Added %d lock entities for %s", len(entities), coordinator.panel_name)


class ZKAccessDoorLock(CoordinatorEntity, LockEntity):
    """Representation of a ZKAccess door lock."""

    def __init__(
        self,
        coordinator: ZKAccessCoordinator,
        entry: ConfigEntry,
        door_number: int,
    ) -> None:
        """Initialize the lock."""
        super().__init__(coordinator)
        
        self._door_number = door_number
        self._attr_name = f"{coordinator.panel_name} Door {door_number}"
        self._attr_unique_id = f"{entry.entry_id}_door_{door_number}"
        self._attr_has_entity_name = True
        
        # Device info
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": coordinator.panel_name,
            "manufacturer": "ZKTeco",
            "model": coordinator.model,
            "sw_version": coordinator.serial_number,
        }

    @property
    def is_locked(self) -> bool:
        """Return true if lock is locked."""
        if not self.coordinator.data:
            return True
        
        doors = self.coordinator.data.get("doors", [])
        
        for door in doors:
            if door.get("door") == self._door_number:
                return door.get("locked", True)
        
        return True

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self.coordinator.connected and self.coordinator.last_update_success

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional state attributes."""
        return {
            "door_number": self._door_number,
            "panel": self.coordinator.panel_name,
            "panel_ip": self.coordinator.client.ip,
        }

    async def async_lock(self, **kwargs: Any) -> None:
        """Lock the door."""
        await self.coordinator.lock_door(self._door_number)

    async def async_unlock(self, **kwargs: Any) -> None:
        """Unlock the door."""
        _LOGGER.error("🔵 Lock entity async_unlock called for door %s", self._door_number)
    
        duration = self.coordinator.entry.options.get("unlock_duration", 5)
        _LOGGER.error("🔵 Calling coordinator.unlock_door with duration=%s", duration)
    
        result = await self.coordinator.unlock_door(self._door_number, duration)
        _LOGGER.error("🔵 Coordinator returned: %s", result)
