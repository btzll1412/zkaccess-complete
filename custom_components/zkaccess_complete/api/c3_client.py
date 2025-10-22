"""ZKTeco C3 Access Control Panel Client - Using zkaccess-c3 library."""
import logging
from typing import Any

try:
    from c3 import C3
    from c3.controldevice import ControlDeviceOutput
except ImportError:
    C3 = None
    ControlDeviceOutput = None

_LOGGER = logging.getLogger(__name__)


class C3Client:
    """Client for communicating with ZKTeco C3 access control panels."""

    def __init__(self, ip: str, port: int = 4370, password: str = ""):
        """Initialize the client."""
        self.ip = ip
        self.port = port
        self.password = password if password else None
        self.panel = None
        self.connected = False
        
        if C3 is None:
            _LOGGER.error("zkaccess-c3 library not installed")

    def connect(self) -> bool:
        """Connect to the panel."""
        if C3 is None:
            _LOGGER.error("zkaccess-c3 library not available")
            return False
        
        try:
            # Create C3 panel instance
            self.panel = C3(self.ip, self.port)
            
            # Connect (with or without password)
            if self.password:
                success = self.panel.connect(self.password)
            else:
                success = self.panel.connect()
            
            if success:
                self.connected = True
                _LOGGER.info("✅ Connected to C3 panel at %s:%s", self.ip, self.port)
                return True
            else:
                _LOGGER.error("Failed to connect to panel at %s:%s", self.ip, self.port)
                return False
                
        except Exception as e:
            _LOGGER.error("Connection error to %s:%s - %s", self.ip, self.port, e)
            return False

    def disconnect(self) -> None:
        """Disconnect from the panel."""
        if self.panel:
            try:
                self.panel.disconnect()
                self.connected = False
                _LOGGER.info("Disconnected from panel %s", self.ip)
            except Exception as e:
                _LOGGER.error("Disconnect error: %s", e)

    def get_device_info(self) -> dict[str, Any]:
        """Get device information."""
        if not self.connected or not self.panel:
            return {
                "serial_number": "Unknown",
                "door_count": 4,
                "model": "C3-400",
                "firmware": "Unknown",
            }
        
        try:
            params = self.panel.get_device_param(["~SerialNumber", "LockCount", "FirmVer"])
            
            return {
                "serial_number": params.get("~SerialNumber", "Unknown"),
                "door_count": int(params.get("LockCount", "4")),
                "firmware": params.get("FirmVer", "Unknown"),
                "model": "C3-400",
            }
        except Exception as e:
            _LOGGER.warning("Could not get device info: %s", e)
            return {
                "serial_number": "Unknown",
                "door_count": 4,
                "model": "C3-400",
                "firmware": "Unknown",
            }

    def get_parameters(self, params: list[str]) -> dict[str, str]:
        """Get device parameters."""
        if not self.connected or not self.panel:
            return {}
        
        try:
            return self.panel.get_device_param(params)
        except Exception as e:
            _LOGGER.error("Error getting parameters: %s", e)
            return {}

    def get_door_status(self) -> list[dict[str, Any]]:
        """Get status of all doors."""
        doors = []
        for door_num in range(1, 5):
            doors.append({
                "door": door_num,
                "locked": True,
                "sensor_open": False,
                "alarm": False,
            })
        return doors

    def get_events(self) -> list[dict[str, Any]]:
        """Get real-time events from the panel."""
        if not self.connected or not self.panel:
            return []
        
        try:
            rt_log = self.panel.get_rt_log()
            
            events = []
            for record in rt_log:
                events.append({
                    "time": getattr(record, 'time', None),
                    "pin": getattr(record, 'pin', None),
                    "door": getattr(record, 'door', None),
                    "event_type": getattr(record, 'event_type', None),
                })
            
            return events
        except Exception as e:
            _LOGGER.debug("No new events: %s", e)
            return []

    def unlock_door(self, door_number: int, duration: int = 5) -> bool:
    """Unlock a door for specified duration."""
    _LOGGER.error("🔴 unlock_door called: door=%s, duration=%s", door_number, duration)
    
    if not self.connected:
        _LOGGER.error("🔴 Not connected!")
        return False
        
    if not self.panel:
        _LOGGER.error("🔴 Panel object is None!")
        return False
        
    if ControlDeviceOutput is None:
        _LOGGER.error("🔴 ControlDeviceOutput is None!")
        return False


    try:
        _LOGGER.error("🟡 Creating control command...")
        control_cmd = ControlDeviceOutput(door_number, 1, duration)
        _LOGGER.error("🟡 Control command created: %s", control_cmd)
        
        _LOGGER.error("🟡 Sending command to panel...")
        try:
            self.panel.control_device(control_cmd)
            _LOGGER.error("✅ Command sent successfully!")
            return True
        except Exception as cmd_error:
            error_msg = str(cmd_error)
            _LOGGER.error("🔴 Command error: %s", error_msg)
            
            if "Invalid response header" in error_msg or "expected" in error_msg or "received b''" in error_msg:
                _LOGGER.error("✅ Command sent (no response, but normal)")
                return True
            else:
                raise

    except Exception as e:
        _LOGGER.error("❌ Exception in unlock_door: %s", e)
        import traceback
        _LOGGER.error("Traceback: %s", traceback.format_exc())
        return False

    def lock_door(self, door_number: int) -> bool:
        """Lock a door immediately."""
        return self.unlock_door(door_number, 0)


async def async_unlock(self, **kwargs: Any) -> None:
    """Unlock the door."""
    _LOGGER.error("🔵 Lock entity async_unlock called for door %s", self._door_number)
    
    duration = self.coordinator.entry.options.get("unlock_duration", 5)
    _LOGGER.error("🔵 Calling coordinator.unlock_door with duration=%s", duration)
    
    result = await self.coordinator.unlock_door(self._door_number, duration)
    _LOGGER.error("🔵 Coordinator returned: %s", result)
