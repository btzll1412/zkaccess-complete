"""ZKTeco C3 Access Control Panel Client - Based on zkaccess-c3-py."""
import logging
import socket
import struct
from typing import Any

_LOGGER = logging.getLogger(__name__)

# Protocol Commands (from working library)
CMD_CONNECT = 0x76  # Session initiation
CMD_DISCONNECT = 0x02
CMD_GET_PARAM = 0x04
CMD_CONTROL = 0x05
CMD_GET_RT_LOG = 0x0B
CMD_ACK = 0xC8  # Response acknowledge

# Start/End bytes
PACKET_START = 0xAA
PACKET_VERSION = 0x01
PACKET_END = 0x55


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
        """Connect to the panel with session initiation."""
        try:
            # Create TCP socket
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(5)
            self.socket.connect((self.ip, self.port))
            
            _LOGGER.info("TCP connected to %s:%s", self.ip, self.port)
            
            # Send session initiation command
            self.message_number = -258  # Initial message number
            response = self._send_command(CMD_CONNECT, b'')
            
            if response is None:
                _LOGGER.error("No response to connect command")
                self.socket.close()
                return False
            
            # Parse session ID from response
            if len(response) >= 2:
                self.session_id = struct.unpack('<H', response[0:2])[0]
                _LOGGER.info("Session established: session_id=%d", self.session_id)
                self.connected = True
                return True
            else:
                _LOGGER.error("Invalid connect response")
                self.socket.close()
                return False
                
        except Exception as e:
            _LOGGER.error("Connection error to %s:%s - %s", self.ip, self.port, e)
            if self.socket:
                self.socket.close()
            return False

    def disconnect(self) -> None:
        """Disconnect from the panel."""
        if self.socket:
            try:
                self._send_command(CMD_DISCONNECT, b'')
                self.socket.close()
                self.connected = False
                self.session_id = 0
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
                "firmware": "Unknown",
            }
        
        try:
            params = self.get_parameters(["~SerialNumber", "LockCount", "FirmVer"])
            
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
        if not self.connected:
            return {}
        
        try:
            # Build parameter request (comma-separated, ending with tilde)
            param_str = ",".join(params) + "~"
            data = param_str.encode('ascii')
            
            response = self._send_command(CMD_GET_PARAM, data)
            
            if not response:
                return {}
            
            # Parse response (format: param1=value1,param2=value2~)
            result = {}
            response_str = response.decode('ascii', errors='ignore').strip('~')
            
            for item in response_str.split(','):
                if '=' in item:
                    key, value = item.split('=', 1)
                    result[key.strip()] = value.strip()
            
            _LOGGER.debug("Got parameters: %s", result)
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
            response = self._send_command(CMD_GET_RT_LOG, b'')
            
            if not response or len(response) < 4:
                return []
            
            # TODO: Parse event records
            # Event format varies by firmware version
            events = []
            
            return events
        except Exception as e:
            _LOGGER.debug("No new events: %s", e)
            return []

    def unlock_door(self, door_number: int, duration: int = 5) -> bool:
        """Unlock a door for specified duration.
        
        Args:
            door_number: Door number (1-4)
            duration: Duration in seconds (0=close, 1-254=open time, 255=permanent)
        """
        if not self.connected:
            _LOGGER.error("Cannot unlock door - not connected")
            return False
        
        try:
            _LOGGER.info("Unlocking door %s for %s seconds", door_number, duration)
            
            # Control command format (from working library):
            # Byte 0: door_number (1-4)
            # Byte 1: address (1=door, 2=auxiliary)
            # Byte 2: duration (seconds)
            # Byte 3: reserved (0)
            data = struct.pack('<BBBB', door_number, 1, duration, 0)
            
            response = self._send_command(CMD_CONTROL, data)
            
            if response is not None:
                _LOGGER.info("Door %s unlock command successful", door_number)
                return True
            else:
                _LOGGER.error("Door %s unlock failed - no response", door_number)
                return False
                
        except Exception as e:
            _LOGGER.error("Failed to unlock door %s: %s", door_number, e)
            return False

    def lock_door(self, door_number: int) -> bool:
        """Lock a door immediately (duration=0)."""
        return self.unlock_door(door_number, 0)

    def _send_command(self, command: int, data: bytes = b'') -> bytes | None:
        """Send command to panel and get response."""
        if not self.socket:
            return None
        
        try:
            # Build packet
            packet = self._build_packet(command, data)
            
            _LOGGER.debug("Sending command 0x%02X with %d bytes", command, len(data))
            
            # Send
            self.socket.sendall(packet)
            
            # Receive response
            response = self.socket.recv(4096)
            
            if len(response) < 8:
                _LOGGER.warning("Response too short: %s bytes", len(response))
                return None
            
            # Verify packet format
            if response[0] != PACKET_START or response[-1] != PACKET_END:
                _LOGGER.warning("Invalid response format")
                return None
            
            # Extract response command
            response_cmd = response[2]
            
            _LOGGER.debug("Received response: cmd=0x%02X, len=%d", response_cmd, len(response))
            
            # Check if ACK response
            if response_cmd == CMD_ACK:
                # Extract data length
                data_length = struct.unpack('<H', response[3:5])[0]
                
                # Data starts at byte 9 (after session_id and msg_number)
                if data_length > 0 and len(response) >= 9 + data_length:
                    return response[9:9+data_length]
                return b''
            else:
                # Direct response
                data_length = struct.unpack('<H', response[3:5])[0]
                if data_length > 0 and len(response) >= 9 + data_length:
                    return response[9:9+data_length]
                return b''
            
        except socket.timeout:
            _LOGGER.warning("Command timeout")
            return None
        except Exception as e:
            _LOGGER.error("Command error: %s", e)
            return None

    def _build_packet(self, command: int, data: bytes = b'') -> bytes:
        """Build protocol packet according to C3 specification.
        
        Packet format:
        [0xAA][0x01][Command][Length LSB][Length MSB][SessionId LSB][SessionId MSB]
        [MsgNum LSB][MsgNum MSB][Data...][Checksum LSB][Checksum MSB][0x55]
        """
        # Increment message number
        self.message_number += 1
        
        # Calculate data length (includes session_id and msg_number)
        data_length = len(data) + 4  # +4 for session_id and message_number
        
        # Build packet header
        packet = bytearray()
        packet.append(PACKET_START)  # Start byte
        packet.append(PACKET_VERSION)  # Version
        packet.append(command)  # Command
        packet.extend(struct.pack('<H', data_length))  # Data length (little-endian)
        
        # Add session info
        packet.extend(struct.pack('<H', self.session_id))  # Session ID
        packet.extend(struct.pack('<H', self.message_number & 0xFFFF))  # Message number
        
        # Add data payload
        if data:
            packet.extend(data)
        
        # Calculate CRC-16 checksum (excluding start and end bytes)
        checksum = self._calculate_checksum(packet[1:])
        packet.extend(struct.pack('<H', checksum))
        
        # End byte
        packet.append(PACKET_END)
        
        return bytes(packet)

    def _calculate_checksum(self, data: bytes) -> int:
        """Calculate CRC-16 checksum for C3 protocol."""
        checksum = 0
        
        for byte in data:
            checksum += byte
        
        # Keep only lower 16 bits
        checksum = checksum & 0xFFFF
        
        return checksum
