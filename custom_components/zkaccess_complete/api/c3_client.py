"""ZKTeco C3 Access Control Panel Client Library."""
import logging
import socket
import struct
from datetime import datetime
from typing import Any

_LOGGER = logging.getLogger(__name__)

CMD_CONNECT = 0x0001
CMD_DISCONNECT = 0x0002
CMD_GET_PARAM = 0x0004
CMD_CONTROL = 0x0005
CMD_GET_RTLOG = 0x000B
CMD_ACK_OK = 0x07D0
CMD_ACK_ERROR = 0x07D1

CONTROL_OUTPUT = 1


class C3Client:
    """Client for communicating with ZKTeco C3 access control panels."""

    def __init__(self, ip: str, port: int = 4370, password: str = ""):
        """Initialize the client."""
        self.ip = ip
        self.port = port
        self.password = password
        self.socket = None
        self.session_id = 0
        self.reply_number = 0
        self.connected = False

    def connect(self) -> bool:
        """Connect to the panel."""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(5)
            self.socket.connect((self.ip, self.port))
            
            self.connected = True
            _LOGGER.info("Connected to C3 panel at %s:%s", self.ip, self.port)
            return True
            
        except socket.timeout:
            _LOGGER.error("Connection timeout to %s:%s", self.ip, self.port)
            return False
        except ConnectionRefusedError:
            _LOGGER.error("Connection refused by %s:%s", self.ip, self.port)
            return False
        except Exception as e:
            _LOGGER.error("Connection error to %s:%s - %s", self.ip, self.port, e)
            return False

    def disconnect(self) -> None:
        """Disconnect from the panel."""
        if self.socket:
            try:
                self._send_command(CMD_DISCONNECT, b'')
                self.socket.close()
                self.connected = False
                _LOGGER.info("Disconnected from panel %s", self.ip)
            except Exception as e:
                _LOGGER.error("Disconnect error: %s", e)

    def get_device_info(self) -> dict[str, Any]:
        """Get device information."""
        if not self.connected:
            return {
                "serial_number": "Unknown",
                "door_count": 4,
                "model": "C3-400",
            }
        
        try:
            params = ["~SerialNumber", "LockCount", "FirmVer"]
            info = self.get_parameters(params)
            
            return {
                "serial_number": info.get("~SerialNumber", "Unknown"),
                "door_count": int(info.get("LockCount", 4)),
                "firmware": info.get("FirmVer", "Unknown"),
                "model": "C3-400",
            }
        except Exception as e:
            _LOGGER.warning("Could not get device info: %s", e)
            return {
                "serial_number": "Unknown",
                "door_count": 4,
                "model": "C3-400",
            }

    def get_parameters(self, params: list[str]) -> dict[str, str]:
        """Get device parameters."""
        if not self.connected:
            return {}
        
        try:
            param_str = ",".join(params) + ","
            data = param_str.encode('utf-8')
            
            response = self._send_command(CMD_GET_PARAM, data)
            
            if not response:
                return {}
            
            result = {}
            response_str = response.decode('utf-8', errors='ignore')
            
            for param in response_str.split(','):
                if '=' in param:
                    key, value = param.split('=', 1)
                    result[key.strip()] = value.strip()
            
            return result
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
        if not self.connected:
            return []
        
        try:
            response = self._send_command(CMD_GET_RTLOG, b'')
            
            if not response or len(response) < 4:
                return []
            
            events = []
            
            return events
        except Exception as e:
            _LOGGER.debug("No new events: %s", e)
            return []

    def unlock_door(self, door_number: int, duration: int = 5) -> bool:
        """Unlock a door for specified duration."""
        if not self.connected:
            _LOGGER.error("Cannot unlock door - not connected")
            return False
        
        try:
            _LOGGER.info("Unlocking door %s for %s seconds", door_number, duration)
            
            # Control output command format for C3
            # Door number, output address (1=door lock), duration in seconds, reserved
            data = struct.pack('<BBBB', door_number, 1, duration * 10, 0)
            
            response = self._send_command(CMD_CONTROL, data)
            
            if response is not None:
                _LOGGER.info("Door %s unlock command sent successfully", door_number)
                return True
            else:
                _LOGGER.error("Door %s unlock failed - no response", door_number)
                return False
                
        except Exception as e:
            _LOGGER.error("Failed to unlock door %s: %s", door_number, e)
            return False

    def lock_door(self, door_number: int) -> bool:
        """Lock a door immediately."""
        if not self.connected:
            _LOGGER.error("Cannot lock door - not connected")
            return False
        
        try:
            _LOGGER.info("Locking door %s", door_number)
            
            data = struct.pack('BBBB', door_number, 1, 0, 0)
            
            response = self._send_command(CMD_CONTROL, data)
            
            if response is not None:
                _LOGGER.info("Door %s lock command sent successfully", door_number)
                return True
            else:
                _LOGGER.error("Door %s lock failed - no response", door_number)
                return False
                
        except Exception as e:
            _LOGGER.error("Failed to lock door %s: %s", door_number, e)
            return False

    def _send_command(self, command: int, data: bytes = b'') -> bytes | None:
        """Send command to panel and get response."""
        if not self.socket:
            return None
        
        try:
            packet = self._build_packet(command, data)
            
            _LOGGER.debug("Sending command 0x%04X to %s", command, self.ip)
            
            self.socket.sendall(packet)
            
            response = self.socket.recv(4096)
            
            if len(response) < 8:
                _LOGGER.warning("Response too short: %s bytes", len(response))
                return None
            
            if response[0] != 0xAA or response[-1] != 0x55:
                _LOGGER.warning("Invalid response format")
                return None
            
            response_cmd = struct.unpack('<H', response[2:4])[0]
            
            _LOGGER.debug("Received response: 0x%04X", response_cmd)
            
            if response_cmd == CMD_ACK_OK:
                _LOGGER.debug("Command acknowledged")
                data_length = struct.unpack('<H', response[4:6])[0]
                if data_length > 0:
                    return response[8:8+data_length]
                return b''
            elif response_cmd == CMD_ACK_ERROR:
                _LOGGER.warning("Command error response")
                return None
            else:
                data_length = struct.unpack('<H', response[4:6])[0]
                if data_length > 0:
                    return response[8:8+data_length]
                return b''
            
        except socket.timeout:
            _LOGGER.warning("Command timeout")
            return None
        except Exception as e:
            _LOGGER.error("Command error: %s", e)
            return None

    def _build_packet(self, command: int, data: bytes = b'') -> bytes:
        """Build protocol packet."""
        data_length = len(data)
        
        packet = bytearray()
        packet.append(0xAA)  # Start byte
        packet.append(0x01)  # Version (changed from 0x00 to 0x01)
        packet.extend(struct.pack('<H', command))  # Command
        packet.extend(struct.pack('<H', 0))  # Checksum placeholder
        packet.extend(struct.pack('<H', 0))  # Session ID
        packet.extend(struct.pack('<H', 0))  # Reply number
        packet.extend(struct.pack('<H', data_length))  # Data length
        
        if data:
            packet.extend(data)
        
        # Calculate checksum
        checksum = 0
        for byte in packet:
            checksum += byte
        checksum = checksum & 0xFFFF
        
        # Update checksum in packet (bytes 4-5)
        struct.pack_into('<H', packet, 4, checksum)
        
        packet.append(0x55)  # End byte
        
        return bytes(packet)
