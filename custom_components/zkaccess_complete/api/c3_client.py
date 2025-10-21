"""ZKTeco C3 Access Control Panel Client Library."""
import logging
import socket
import struct
from datetime import datetime
from typing import Any

_LOGGER = logging.getLogger(__name__)

# Protocol commands
CMD_CONNECT = 0x76
CMD_DISCONNECT = 0x02
CMD_GET_PARAM = 0x04
CMD_CONTROL = 0x05
CMD_GET_RTLOG = 0x0B
CMD_RESPONSE = 0xC8

# Control commands
CONTROL_UNLOCK = 1
CONTROL_LOCK = 2
CONTROL_CANCEL_ALARM = 3
CONTROL_RESTART = 4


class C3Client:
    """Client for communicating with ZKTeco C3 access control panels."""

    def __init__(self, ip: str, port: int = 4370, password: str = ""):
        """Initialize the client."""
        self.ip = ip
        self.port = port
        self.password = password
        self.socket = None
        self.session_id = 0
        self.message_number = 0
        self.connected = False

    def connect(self) -> bool:
        """Connect to the panel."""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(5)
            self.socket.connect((self.ip, self.port))
            
            # Send connect command
            response = self._send_command(CMD_CONNECT)
            
            if response:
                self.connected = True
                self.session_id = struct.unpack('<H', response[0:2])[0]
                _LOGGER.info("Connected to panel %s (Session: %s)", self.ip, self.session_id)
                return True
            
            return False
            
        except Exception as e:
            _LOGGER.error("Connection error: %s", e)
            return False

    def disconnect(self) -> None:
        """Disconnect from the panel."""
        if self.socket:
            try:
                self._send_command(CMD_DISCONNECT)
                self.socket.close()
                self.connected = False
                _LOGGER.info("Disconnected from panel %s", self.ip)
            except Exception as e:
                _LOGGER.error("Disconnect error: %s", e)

    def get_device_info(self) -> dict[str, Any]:
        """Get device information."""
        params = [
            "~SerialNumber",
            "LockCount",
            "ReaderCount",
            "AuxInCount",
            "AuxOutCount",
            "FirmVer",
            "MachineType",
        ]
        
        info = self.get_parameters(params)
        
        return {
            "serial_number": info.get("~SerialNumber", "Unknown"),
            "door_count": int(info.get("LockCount", 4)),
            "reader_count": int(info.get("ReaderCount", 4)),
            "aux_in_count": int(info.get("AuxInCount", 0)),
            "aux_out_count": int(info.get("AuxOutCount", 0)),
            "firmware": info.get("FirmVer", "Unknown"),
            "model": self._parse_model(info.get("MachineType", "C3-400")),
        }

    def get_parameters(self, params: list[str]) -> dict[str, str]:
        """Get device parameters."""
        # Build parameter request
        param_str = ",".join(params) + ","
        data = param_str.encode('utf-8')
        
        response = self._send_command(CMD_GET_PARAM, data)
        
        if not response:
            return {}
        
        # Parse response
        result = {}
        response_str = response.decode('utf-8', errors='ignore')
        
        for param in response_str.split(','):
            if '=' in param:
                key, value = param.split('=', 1)
                result[key.strip()] = value.strip()
        
        return result

    def get_door_status(self) -> list[dict[str, Any]]:
        """Get status of all doors."""
        doors = []
        
        info = self.get_device_info()
        door_count = info.get("door_count", 4)
        
        for door_num in range(1, door_count + 1):
            doors.append({
                "door": door_num,
                "locked": True,  # Default state
                "sensor_open": False,
                "alarm": False,
            })
        
        return doors

    def get_events(self) -> list[dict[str, Any]]:
        """Get real-time events from the panel."""
        response = self._send_command(CMD_GET_RTLOG)
        
        if not response or len(response) < 4:
            return []
        
        events = []
        offset = 4  # Skip header
        
        while offset + 16 <= len(response):
            try:
                # Parse event record (16 bytes)
                event_data = response[offset:offset+16]
                
                # Basic parsing - adjust based on actual protocol
                door = event_data[0]
                event_type = event_data[1]
                card = struct.unpack('<I', event_data[4:8])[0]
                timestamp_raw = struct.unpack('<I', event_data[8:12])[0]
                
                timestamp = datetime.fromtimestamp(timestamp_raw) if timestamp_raw > 0 else datetime.now()
                
                events.append({
                    "door": door,
                    "event_type": event_type,
                    "event_type_name": self._get_event_name(event_type),
                    "card": str(card) if card > 0 else None,
                    "timestamp": timestamp,
                    "user_name": "Unknown",  # Will be resolved from database
                })
                
                offset += 16
                
            except Exception as e:
                _LOGGER.error("Error parsing event: %s", e)
                break
        
        return events

    def unlock_door(self, door_number: int, duration: int = 5) -> bool:
        """Unlock a door for specified duration."""
        # Control output command
        data = struct.pack('<BBBB', door_number, 1, duration, 0)
        response = self._send_command(CMD_CONTROL, data)
        return response is not None

    def lock_door(self, door_number: int) -> bool:
        """Lock a door immediately."""
        data = struct.pack('<BBBB', door_number, 1, 0, 0)
        response = self._send_command(CMD_CONTROL, data)
        return response is not None

    def get_aux_inputs(self) -> list[dict[str, Any]]:
        """Get auxiliary input status."""
        # Placeholder - implement based on your needs
        return []

    def get_aux_outputs(self) -> list[dict[str, Any]]:
        """Get auxiliary output status."""
        # Placeholder - implement based on your needs
        return []

    def _send_command(self, command: int, data: bytes = b'') -> bytes | None:
        """Send command to panel and get response."""
        if not self.socket:
            return None
        
        try:
            # Build packet
            packet = self._build_packet(command, data)
            
            # Send
            self.socket.send(packet)
            
            # Receive response
            response = self.socket.recv(4096)
            
            if len(response) < 8:
                return None
            
            # Verify response
            if response[0] != 0xAA or response[-1] != 0x55:
                _LOGGER.error("Invalid response format")
                return None
            
            # Extract data
            data_length = struct.unpack('<H', response[3:5])[0]
            if data_length > 0:
                return response[7:7+data_length]
            
            return b''
            
        except Exception as e:
            _LOGGER.error("Command error: %s", e)
            return None

    def _build_packet(self, command: int, data: bytes = b'') -> bytes:
        """Build protocol packet."""
        # Add session info if connected
        if self.connected and self.session_id > 0:
            self.message_number += 1
            session_data = struct.pack('<HH', self.session_id, self.message_number)
            data = session_data + data
        
        data_length = len(data)
        
        # Build packet: start + version + command + length + data + checksum + end
        packet = struct.pack('<BBBH', 0xAA, 0x01, command, data_length)
        packet += data
        
        # Calculate checksum (CRC16)
        checksum = self._calculate_checksum(packet[1:])
        packet += struct.pack('<H', checksum)
        packet += b'\x55'
        
        return packet

    def _calculate_checksum(self, data: bytes) -> int:
        """Calculate CRC16 checksum."""
        crc = 0
        for byte in data:
            crc ^= byte
            for _ in range(8):
                if crc & 1:
                    crc = (crc >> 1) ^ 0xA001
                else:
                    crc >>= 1
        return crc

    def _parse_model(self, machine_type: str) -> str:
        """Parse machine type to model name."""
        if "400" in machine_type:
            return "C3-400"
        elif "200" in machine_type:
            return "C3-200"
        elif "100" in machine_type:
            return "C3-100"
        return "C3-400"

    def _get_event_name(self, event_type: int) -> str:
        """Get human-readable event name."""
        names = {
            0: "Normal Open",
            1: "Normal Close",
            200: "Card Swipe",
            201: "PIN Entered",
            202: "Card + PIN",
            205: "Access Denied",
            206: "Duress",
        }
        return names.get(event_type, f"Event {event_type}")
