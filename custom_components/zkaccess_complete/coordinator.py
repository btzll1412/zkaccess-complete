"""Data update coordinator for ZKAccess."""
from __future__ import annotations

from datetime import timedelta
import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_IP_ADDRESS, CONF_PORT
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)

from .const import (
    DOMAIN,
    CONF_PASSWORD,
    DEFAULT_PORT,
)
from .api.c3_client import C3Client

_LOGGER = logging.getLogger(__name__)


class ZKAccessCoordinator(DataUpdateCoordinator):
    """Class to manage fetching ZKAccess data."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize."""
        self.entry = entry
        self.client = C3Client(
            ip=entry.data[CONF_IP_ADDRESS],
            port=entry.data.get(CONF_PORT, DEFAULT_PORT),
            password=entry.data.get(CONF_PASSWORD, ""),
        )
        
        # Panel info
        self.panel_name = entry.data.get("panel_name", "Access Panel")
        self.serial_number = None
        self.door_count = 4
        self.model = "C3-400"
        
        # Event buffer for live monitoring
        self.event_buffer = []
        self.max_events = 1000
        
        # Update interval from options
        scan_interval = entry.options.get("scan_interval", 5)

        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_{entry.entry_id}",
            update_interval=timedelta(seconds=scan_interval),
        )

    async def async_connect(self) -> bool:
        """Connect to the panel."""
        try:
            connected = await self.hass.async_add_executor_job(
                self.client.connect
            )
            
            if connected:
                # Get panel information
                info = await self.hass.async_add_executor_job(
                    self.client.get_device_info
                )
                self.serial_number = info.get("serial_number")
                self.door_count = info.get("door_count", 4)
                self.model = info.get("model", "C3-400")
                
                _LOGGER.info(
                    "Connected to %s (%s) - %s doors",
                    self.panel_name,
                    self.serial_number,
                    self.door_count,
                )
                return True
            
            return False
            
        except Exception as err:
            _LOGGER.error("Failed to connect to panel: %s", err)
            return False

    async def async_disconnect(self) -> None:
        """Disconnect from the panel."""
        try:
            await self.hass.async_add_executor_job(self.client.disconnect)
            _LOGGER.info("Disconnected from %s", self.panel_name)
        except Exception as err:
            _LOGGER.error("Error disconnecting: %s", err)

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from panel."""
        try:
            # Get door status
            doors = await self.hass.async_add_executor_job(
                self.client.get_door_status
            )
            
            # Get events
            events = await self.hass.async_add_executor_job(
                self.client.get_events
            )
            
            # Add new events to buffer
            if events:
                self.event_buffer.extend(events)
                # Keep only last N events
                if len(self.event_buffer) > self.max_events:
                    self.event_buffer = self.event_buffer[-self.max_events:]
                
                # Send notifications for important events
                await self._process_events(events)
            
            # Get aux inputs status
            aux_inputs = await self.hass.async_add_executor_job(
                self.client.get_aux_inputs
            )
            
            # Get aux outputs status
            aux_outputs = await self.hass.async_add_executor_job(
                self.client.get_aux_outputs
            )
            
            return {
                "doors": doors,
                "events": events,
                "aux_inputs": aux_inputs,
                "aux_outputs": aux_outputs,
                "connected": True,
            }

        except Exception as err:
            _LOGGER.error("Error updating data: %s", err)
            raise UpdateFailed(f"Error communicating with panel: {err}")

    async def _process_events(self, events: list[dict]) -> None:
        """Process events and send notifications."""
        if not self.entry.options.get("enable_notifications", True):
            return
        
        for event in events:
            event_type = event.get("event_type")
            
            # Send notification for important events
            if event_type in [205, 206, 2, 3]:  # Access denied, duress, alarms
                await self._send_notification(event)

    async def _send_notification(self, event: dict) -> None:
        """Send HA notification for event."""
        event_type_name = event.get("event_type_name", "Unknown Event")
        door_name = event.get("door_name", f"Door {event.get('door')}")
        user_name = event.get("user_name", "Unknown")
        
        message = f"{event_type_name} - {door_name}"
        if user_name != "Unknown":
            message += f" - {user_name}"
        
        await self.hass.services.async_call(
            "persistent_notification",
            "create",
            {
                "title": "ZKAccess Alert",
                "message": message,
                "notification_id": f"zkaccess_{event.get('timestamp')}",
            },
        )

    async def unlock_door(self, door_number: int, duration: int = 5) -> bool:
        """Unlock a specific door."""
        try:
            result = await self.hass.async_add_executor_job(
                self.client.unlock_door, door_number, duration
            )
            await self.async_request_refresh()
            return result
        except Exception as err:
            _LOGGER.error("Failed to unlock door %s: %s", door_number, err)
            return False

    async def lock_door(self, door_number: int) -> bool:
        """Lock a specific door."""
        try:
            result = await self.hass.async_add_executor_job(
                self.client.lock_door, door_number
            )
            await self.async_request_refresh()
            return result
        except Exception as err:
            _LOGGER.error("Failed to lock door %s: %s", door_number, err)
            return False
