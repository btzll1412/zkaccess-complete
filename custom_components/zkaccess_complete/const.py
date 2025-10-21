"""Constants for ZKAccess Complete Control System."""

# Domain
DOMAIN = "zkaccess_complete"

# Configuration
CONF_PANEL_NAME = "panel_name"
CONF_IP_ADDRESS = "ip_address"
CONF_PORT = "port"
CONF_PASSWORD = "password"
CONF_DOORS = "doors"

# Defaults
DEFAULT_PORT = 4370
DEFAULT_SCAN_INTERVAL = 5
DEFAULT_UNLOCK_DURATION = 5

# Event types from C3 board
EVENT_TYPE_NORMAL_OPEN = 0
EVENT_TYPE_NORMAL_CLOSE = 1
EVENT_TYPE_ALARM_OPEN = 2
EVENT_TYPE_ALARM_CLOSE = 3
EVENT_TYPE_DOOR_OPENED = 4
EVENT_TYPE_DOOR_CLOSED = 5
EVENT_TYPE_CARD_SWIPE = 200
EVENT_TYPE_PIN_ENTERED = 201
EVENT_TYPE_CARD_PIN = 202
EVENT_TYPE_ACCESS_DENIED = 205
EVENT_TYPE_DURESS = 206

EVENT_TYPES = {
    0: "Normal Open",
    1: "Normal Close",
    2: "Alarm Open",
    3: "Alarm Close",
    4: "Door Opened",
    5: "Door Closed",
    200: "Card Swipe",
    201: "PIN Entered",
    202: "Card + PIN",
    205: "Access Denied",
    206: "Duress Alarm",
}

# Verification modes
VERIFY_MODE_CARD = 0
VERIFY_MODE_PIN = 1
VERIFY_MODE_CARD_OR_PIN = 2
VERIFY_MODE_CARD_AND_PIN = 3

VERIFY_MODES = {
    0: "Card Only",
    1: "PIN Only",
    2: "Card or PIN",
    3: "Card and PIN",
}

# User status
USER_STATUS_ACTIVE = "active"
USER_STATUS_INACTIVE = "inactive"
USER_STATUS_EXPIRED = "expired"

# Services
SERVICE_ADD_USER = "add_user"
SERVICE_UPDATE_USER = "update_user"
SERVICE_DELETE_USER = "delete_user"
SERVICE_ADD_CARD = "add_card"
SERVICE_REMOVE_CARD = "remove_card"
SERVICE_SET_PIN = "set_pin"
SERVICE_GRANT_ACCESS = "grant_access"
SERVICE_REVOKE_ACCESS = "revoke_access"
SERVICE_CREATE_ACCESS_GROUP = "create_access_group"
SERVICE_DELETE_ACCESS_GROUP = "delete_access_group"
SERVICE_CREATE_TIME_ZONE = "create_time_zone"
SERVICE_DELETE_TIME_ZONE = "delete_time_zone"
SERVICE_LOCK_ALL_DOORS = "lock_all_doors"
SERVICE_UNLOCK_ALL_DOORS = "unlock_all_doors"
SERVICE_SYNC_TIME = "sync_time"
SERVICE_GET_EVENTS = "get_events"
SERVICE_CLEAR_EVENTS = "clear_events"

# Storage keys
STORAGE_VERSION = 1
STORAGE_KEY = f"{DOMAIN}_storage"
STORAGE_USERS = "users"
STORAGE_GROUPS = "access_groups"
STORAGE_TIMEZONES = "time_zones"
STORAGE_HOLIDAYS = "holidays"

# Attributes
ATTR_USER_ID = "user_id"
ATTR_USER_NAME = "user_name"
ATTR_CARD_NUMBER = "card_number"
ATTR_PIN_CODE = "pin_code"
ATTR_VERIFY_MODE = "verify_mode"
ATTR_START_DATE = "start_date"
ATTR_END_DATE = "end_date"
ATTR_GROUPS = "groups"
ATTR_DOORS = "doors"
ATTR_TIME_ZONES = "time_zones"
ATTR_EVENT_TYPE = "event_type"
ATTR_TIMESTAMP = "timestamp"
ATTR_DOOR_NUMBER = "door_number"
