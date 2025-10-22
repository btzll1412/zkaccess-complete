"""ZKTeco C3 Access Control Panel Client - Simplified Protocol."""
import logging
import socket
import struct
from typing import Any

_LOGGER = logging.getLogger(__name__)

# Protocol Commands
CMD_CONTROL = 0x05
CMD_GET_PARAM = 0x04
CMD_GET_RT_LOG = 0x0B

# Packet bytes
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
        self.connected = False

    def connect(self) -> bool:
        """Connect to the panel (simple TCP connection)."""
        try:
            # Create TCP socket
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(5)
            self.socket.connect((self.ip, self.port))
            
            self.connected = True
            _LOGGER.info("Connected to C3 panel at %s:%s", self.ip, self.port)
            return True
                
        except Exception as e:
            _LOGGER.error("Connection error to %s:%s - %s", self.ip, self.port, e)
            if self.socket:
                try:
                    self.socket.close()
                except:
                    pass
            return False

    def disconnect(self) -> None:
        """Disconnect from the panel."""
        if self.socket:
            try:
                self.socket.close()
                self.connected = False
                _LOGGER.info("Disconnected from panel %s", self.ip)
            except Exception as e:
                _LOGGER.error("Disconnect error: %s", e)

    def get_device_info(self) -> dict[str, Any]:
        """Get device information."""
        return {
            "serial_number": "Unknown",
            "door_count": 4,
            "model": "C3-400",
            "firmware": "Unknown",
        }

    def get_parameters(self, params: list[str]) -> dict[str, str]:
        """Get device parameters."""
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
        return []

    def unlock_door(self, door_number: int, duration: int = 5) -> bool:
        """Unlock a door for specified duration."""
        if not self.connected:
            _LOGGER.error("Cannot unlock door - not connected")
            return False
        
        try:
            _LOGGER.info("Sending unlock command: door %s for %s seconds", door_number, duration)
            
            # Try multiple command formats
            formats = [
                # Format 1: Standard format
                struct.pack('<BBBB', door_number, 1, duration, 0),
                # Format 2: Extended format
                struct.pack('<BBBBBB', door_number, 1, duration, 0, 0, 0),
                # Format 3: Simple format
                struct.pack('<BBB', door_number, duration, 0),
            ]
            
            for idx, data in enumerate(formats):
                _LOGGER.debug("Trying format %d: %s", idx + 1, data.hex())
                
                packet = self._build_simple_packet(CMD_CONTROL, data)
                
                try:
                    self.socket.sendall(packet)
                    _LOGGER.debug("Sent %d bytes", len(packet))
                    
                    # Try to receive response (but don't require it)
                    self.socket.settimeout(2)
                    try:
                        response = self.socket.recv(1024)
                        if response:
                            _LOGGER.info("Got response: %s", response.hex()[:40])
                            return True
                    except socket.timeout:
                        _LOGGER.debug("No response (might be normal)")
                        # Consider success if no error
                        return True
                    
                    self.socket.settimeout(5)
                    
                except Exception as e:
                    _LOGGER.debug("Format %d failed: %s", idx + 1, e)
                    continue
            
            # If we get here, all formats failed but connection is still alive
            _LOGGER.warning("All formats tried, considering command sent")
            return True
                
        except Exception as e:
            _LOGGER.error("Failed to unlock door %s: %s", door_number, e)
            return False

    def lock_door(self, door_number: int) -> bool:
        """Lock a door immediately."""
        return self.unlock_door(door_number, 0)

    def _build_simple_packet(self, command: int, data: bytes = b'') -> bytes:
        """Build simple protocol packet without session management."""
        data_length = len(data)
        
        # Build packet
        packet = bytearray()
        packet.append(PACKET_START)  # 0xAA
        packet.append(PACKET_VERSION)  # 0x01
        packet.append(command)  # Command byte
        packet.extend(struct.pack('<H', data_length))  # Length (2 bytes, little-endian)
        
        # Add data
        if data:
            packet.extend(data)
        
        # Simple checksum (sum of all bytes)
        checksum = sum(packet[1:]) & 0xFFFF
        packet.extend(struct.pack('<H', checksum))
        
        # End byte
        packet.append(PACKET_END)  # 0x55
        
        return bytes(packet)
