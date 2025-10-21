"""Sensor platform for ZKAccess."""
from __future__ import annotations

import logging

from homeassistant.components.sensor import SensorEntity
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
    """Set up ZKAccess sensor entities."""
    coordinator: ZKAccessCoordinator = hass.data[DOMAIN][entry.entry_id]
    
    entities = [
        ZKAccessEventCountSensor(coordinator, entry),
        ZKAccessStatusSensor(coordinator, entry),
    ]
    
    async_add_entities(entities)


class ZKAccessEventCountSensor(CoordinatorEntity, SensorEntity):
    """Sensor showing event count."""

    def __init__(
        self,
        coordinator: ZKAccessCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        
        self._attr_name = f"{coordinator.panel_name} Event Count"
        self._attr_unique_id = f"{entry.entry_id}_event_count"
        self._attr_icon = "mdi:counter"
        
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": coordinator.panel_name,
            "manufacturer": "ZKTeco",
            "model": coordinator.model,
        }

    @property
    def native_value(self) -> int:
        """Return the event count."""
        return len(self.coordinator.event_buffer)


class ZKAccessStatusSensor(CoordinatorEntity, SensorEntity):
    """Sensor showing panel status."""

    def __init__(
        self,
        coordinator: ZKAccessCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        
        self._attr_name = f"{coordinator.panel_name} Status"
        self._attr_unique_id = f"{entry.entry_id}_status"
        self._attr_icon = "mdi:check-network"
        
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": coordinator.panel_name,
            "manufacturer": "ZKTeco",
            "model": coordinator.model,
        }

    @property
    def native_value(self) -> str:
        """Return the status."""
        if self.coordinator.data and self.coordinator.data.get("connected"):
            return "Online"
        return "Offline"
