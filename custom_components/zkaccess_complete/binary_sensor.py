"""Binary sensor platform for ZKAccess."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
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
    """Set up ZKAccess binary sensor entities."""
    coordinator: ZKAccessCoordinator = hass.data[DOMAIN][entry.entry_id]
    
    entities = []
    
    # Add door sensor for each door
    for door_num in range(1, coordinator.door_count + 1):
        entities.append(ZKAccessDoorSensor(coordinator, entry, door_num))
    
    async_add_entities(entities)


class ZKAccessDoorSensor(CoordinatorEntity, BinarySensorEntity):
    """Representation of a ZKAccess door sensor."""

    _attr_device_class = BinarySensorDeviceClass.DOOR

    def __init__(
        self,
        coordinator: ZKAccessCoordinator,
        entry: ConfigEntry,
        door_number: int,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        
        self._door_number = door_number
        self._attr_name = f"{coordinator.panel_name} Door {door_number} Sensor"
        self._attr_unique_id = f"{entry.entry_id}_door_{door_number}_sensor"
        
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": coordinator.panel_name,
            "manufacturer": "ZKTeco",
            "model": coordinator.model,
        }

    @property
    def is_on(self) -> bool:
        """Return true if door is open."""
        if not self.coordinator.data:
            return False
        
        doors = self.coordinator.data.get("doors", [])
        
        for door in doors:
            if door.get("door") == self._door_number:
                return door.get("sensor_open", False)
        
        return False

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional attributes."""
        return {
            "door_number": self._door_number,
            "panel": self.coordinator.panel_name,
        }
